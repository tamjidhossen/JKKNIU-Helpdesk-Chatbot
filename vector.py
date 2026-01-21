#!/usr/bin/env python3
"""
Vector Database Management with Auto-Ingestion
==============================================

This script manages the ChromaDB vector store. It handles:
1. Recursive scanning of the Data/ directory.
2. Intelligent sync using file hashes to detect changes.
3. Automatic ingestion of new/modified files.
4. Robust error handling.

Usage:
    python vector.py        # Run a manual sync
    import vector; vector.sync_database() # Auto-sync from code
"""

import os
import glob
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Set

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR, RETRIEVAL_K
)

# Registry file to track processed files and their hashes
REGISTRY_FILE = os.path.join(DATA_DIR, "General", "ingestion_registry.json")

class DataIngestor:
    """Handles recursive file scanning and vector database synchronization."""

    def __init__(self):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        
        # Check if DB exists before Chroma potentially creates the folder
        db_exists = os.path.exists(VECTOR_DB_PATH) and os.path.isdir(VECTOR_DB_PATH) and os.listdir(VECTOR_DB_PATH)
        
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        
        if not db_exists:
            # If DB was deleted, we MUST ignore the registry and re-ingest everything
            self.registry = {}
        else:
            self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, str]:
        """Load the file registry from JSON."""
        if os.path.exists(REGISTRY_FILE):
            try:
                with open(REGISTRY_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_registry(self):
        """Save the current registry to JSON."""
        os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
        with open(REGISTRY_FILE, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _get_all_txt_files(self) -> List[str]:
        """Recursively find all .txt files in DATA_DIR."""
        files = []
        # Walk through directory
        for root, dirs, filenames in os.walk(DATA_DIR):
            # Skip hidden directories and the vector DB itself
            if ".git" in root or "chroma" in root or "__pycache__" in root:
                continue
            
            for filename in filenames:
                if filename.endswith(".txt"):
                    files.append(os.path.join(root, filename))
        return files

    def _process_file(self, file_path: str) -> List[Document]:
        """Read and chunk a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                return []

            filename = os.path.basename(file_path)
            # Use path relative to DATA_DIR as source ID if needed, or just filename
            rel_path = os.path.relpath(file_path, DATA_DIR)
            
            chunks = self.text_splitter.split_text(content)
            documents = []
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    doc = Document(
                        page_content=chunk.strip(),
                        metadata={
                            "source": filename,
                            "file_path": rel_path, # Store relative path for context
                            "chunk": i
                        }
                    )
                    documents.append(doc)
            return documents
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []

    def sync(self):
        """Synchronize the vector database with the file system."""
        print(f"🔍 Scanning {DATA_DIR} for changes...")
        
        all_files = self._get_all_txt_files()
        new_or_modified_files = []
        
        current_hashes = {}
        
        # Identify changed files
        for file_path in all_files:
            file_hash = self._calculate_file_hash(file_path)
            current_hashes[file_path] = file_hash
            
            # Check if new or modified
            if file_path not in self.registry or self.registry[file_path] != file_hash:
                new_or_modified_files.append(file_path)
        
        # Identify deleted files (in registry but not on disk)
        # Note: Chroma doesn't easily support deleting by source file without ID tracking.
        # For now, we just handle additions/updates. Deletions might require a full rebuild concept 
        # or managing IDs more strictly.
        
        if not new_or_modified_files:
            print("✅ Database is up to date.")
            return

        print(f"⚡ Found {len(new_or_modified_files)} new or modified files.")
        
        # Process files
        all_documents = []
        processed_count = 0
        
        for file_path in new_or_modified_files:
            print(f"  → Processing: {os.path.basename(file_path)}")
            docs = self._process_file(file_path)
            all_documents.extend(docs)
            processed_count += 1
            
            # Update registry *after* successful processing attempt
            self.registry[file_path] = current_hashes[file_path]

        if all_documents:
            print(f"📤 Adding {len(all_documents)} chunks to vector store...")
            batch_size = 50
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i + batch_size]
                self.vector_store.add_documents(batch)
                print(f"    Batch {i//batch_size + 1} done.")
            
            self._save_registry()
            print("✅ Sync completed successfully.")
        else:
            print("⚠️ No valid content found in new files.")

# Singleton instance for easy import
ingestor = DataIngestor()

# Expose retriever for other modules to use
retriever = ingestor.vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})

def sync_database():
    """Public wrapper for syncing."""
    try:
        ingestor.sync()
    except Exception as e:
        print(f"❌ Database sync failed: {e}")

if __name__ == "__main__":
    sync_database()