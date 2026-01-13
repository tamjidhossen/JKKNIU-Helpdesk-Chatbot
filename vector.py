from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
import os
import glob
from config import (
    EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K,
    QA_FILE, USE_HYBRID_RETRIEVAL, USE_RERANKER
)

# Initialize embeddings
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

db_location = VECTOR_DB_PATH
add_documents = not os.path.exists(db_location)

# Create vector store
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=db_location,
    embedding_function=embeddings
)

def clean_text(text):
    """Normalize text content."""
    return text.replace('\r\n', '\n').strip()

def load_documents():
    """Load and chunk all text documents."""
    print("Loading documents from disk...")
    docs = []
    
    # Define directories to index
    source_patterns = [
        "Data/CSE_Teachers/*.txt",
        "Data/New_Data/processed/*.txt"
    ]
    
    # Collect all files
    all_files = []
    for pattern in source_patterns:
        found = glob.glob(pattern)
        all_files.extend(found)

    all_files = sorted(list(set(all_files)))
    print(f"Found {len(all_files)} files.")

    for file_path in all_files:
        try:
            filename = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = clean_text(f.read())
            
            if not content:
                continue

            chunks = text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    meta = {
                        "source": filename,
                        "source_path": file_path,
                        "source_dir": os.path.dirname(file_path),
                        "chunk_id": i,
                    }
                    docs.append(Document(page_content=chunk, metadata=meta))
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    print(f"Loaded {len(docs)} chunks.")
    return docs

all_docs = []
if add_documents or USE_HYBRID_RETRIEVAL:
    all_docs = load_documents()

if add_documents:
    if all_docs:
        print(f"Adding {len(all_docs)} chunks to vector store...")
        batch_size = 100
        for i in range(0, len(all_docs), batch_size):
            batch = all_docs[i:i+batch_size]
            vector_store.add_documents(documents=batch)
        print("Vector store populated.")
    else:
        print("No documents found to add.")
else:
    print(f"Using existing vector store at {db_location}")

# Determine retrieval parameters
initial_k = RETRIEVAL_K
if USE_RERANKER:
    initial_k = 50  # Fetch more candidates if reranking

print(f"Configuring Retriever (Hybrid={USE_HYBRID_RETRIEVAL}, Reranker={USE_RERANKER}, K={initial_k})")

# Base Vector Retriever
base_retriever = vector_store.as_retriever(search_kwargs={"k": initial_k})

# Hybrid Retrieval Setup
if USE_HYBRID_RETRIEVAL and all_docs:
    print("Initializing Hybrid Retriever (BM25 + Vector)...")
    bm25_retriever = BM25Retriever.from_documents(all_docs)
    bm25_retriever.k = initial_k
    
    retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, base_retriever],
        weights=[0.5, 0.5]
    )
else:
    retriever = base_retriever

# Reranking Setup
if USE_RERANKER:
    print("Initializing Cross-Encoder Reranker...")
    # Using a lightweight model for CPU efficiency
    model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    model = HuggingFaceCrossEncoder(model_name=model_name)
    compressor = CrossEncoderReranker(model=model, top_n=RETRIEVAL_K) # Rerank back to original K
    
    retriever = ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=retriever
    )

