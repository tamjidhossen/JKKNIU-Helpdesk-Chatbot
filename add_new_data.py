#!/usr/bin/env python3
"""
Add New Data to ChromaDB
========================

This script adds new text files from the New_Data directory to the existing ChromaDB vector store.
It processes all .txt files in the Data/New_Data directory and adds them as chunked documents
to the vector database for retrieval by the helpdesk chatbot.

Usage:
    python add_new_data.py

Requirements:
    - Files should be placed in Data/New_Data/ directory
    - Files should have .txt extension
    - ChromaDB should already be initialized (run vector.py first if needed)
"""

import os
import glob
from pathlib import Path
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import (
    EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, DATA_DIR
)


class NewDataProcessor:
    """Handles adding new data files to the ChromaDB vector store."""
    
    def __init__(self):
        """Initialize the processor with embeddings and vector store."""
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )
        
        # Initialize vector store (should already exist)
        if not os.path.exists(VECTOR_DB_PATH):
            raise FileNotFoundError(
                f"Vector database not found at {VECTOR_DB_PATH}. "
                "Please run vector.py first to initialize the database."
            )
        
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        
        self.new_data_dir = os.path.join(DATA_DIR, "New_Data")
        
    def find_new_files(self):
        """Find all .txt files in the New_Data directory."""
        if not os.path.exists(self.new_data_dir):
            os.makedirs(self.new_data_dir, exist_ok=True)
            print(f"Created directory: {self.new_data_dir}")
            return []
        
        pattern = os.path.join(self.new_data_dir, "*.txt")
        files = glob.glob(pattern)
        return files
    
    def process_file(self, file_path):
        """Process a single file and return chunked documents."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                print(f"Warning: File {file_path} is empty, skipping.")
                return []
            
            # Split content into chunks
            chunks = self.text_splitter.split_text(content)
            documents = []
            
            filename = os.path.basename(file_path)
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    document = Document(
                        page_content=chunk.strip(),
                        metadata={
                            "source": filename,
                            "source_type": "new_data",
                            "chunk": i,
                            "file_path": file_path
                        }
                    )
                    documents.append(document)
            
            return documents
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            return []
    
    def add_files_to_vectorstore(self, files):
        """Add multiple files to the vector store."""
        if not files:
            print("No files to process.")
            return
        
        all_documents = []
        processed_files = []
        
        for file_path in files:
            print(f"Processing: {os.path.basename(file_path)}")
            documents = self.process_file(file_path)
            
            if documents:
                all_documents.extend(documents)
                processed_files.append(file_path)
                print(f"  → Created {len(documents)} chunks")
            else:
                print(f"  → No valid content found")
        
        if all_documents:
            print(f"\nAdding {len(all_documents)} chunks from {len(processed_files)} files to vector store...")
            
            # Add documents in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(all_documents), batch_size):
                batch = all_documents[i:i + batch_size]
                self.vector_store.add_documents(documents=batch)
                print(f"  → Added batch {i//batch_size + 1}/{(len(all_documents)-1)//batch_size + 1}")
            
            print(f"✅ Successfully added {len(all_documents)} chunks to the vector store")
            
            # Optionally move processed files to avoid reprocessing
            self.move_processed_files(processed_files)
        else:
            print("No valid documents to add.")
    
    def move_processed_files(self, processed_files):
        """Move processed files to a 'processed' subdirectory."""
        processed_dir = os.path.join(self.new_data_dir, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        
        for file_path in processed_files:
            filename = os.path.basename(file_path)
            destination = os.path.join(processed_dir, filename)
            
            try:
                os.rename(file_path, destination)
                print(f"Moved {filename} to processed/")
            except Exception as e:
                print(f"Warning: Could not move {filename}: {e}")
    
    def run(self):
        """Main execution method."""
        print("🔍 Scanning for new data files...")
        files = self.find_new_files()
        
        if not files:
            print(f"No .txt files found in {self.new_data_dir}")
            print(f"Place your text files in {self.new_data_dir} and run this script again.")
            return
        
        print(f"Found {len(files)} file(s) to process:")
        for file_path in files:
            print(f"  • {os.path.basename(file_path)}")
        
        print("\n" + "="*50)
        self.add_files_to_vectorstore(files)
        print("="*50)
        print("✅ Process completed!")


def main():
    """Main function to run the new data processor."""
    try:
        processor = NewDataProcessor()
        processor.run()
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
