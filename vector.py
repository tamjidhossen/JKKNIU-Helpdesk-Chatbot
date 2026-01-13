from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
import time
from config import (
    EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K,
    QA_FILE, STRUCTURE_FILE, GOOGLE_EMBEDDING_MODEL
)

# Initialize embeddings and text splitter
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
# embeddings = GoogleGenerativeAIEmbeddings(model=GOOGLE_EMBEDDING_MODEL)
# vector = embeddings.embed_query("Hello world")
# print(vector[:5])

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

if add_documents:
    documents = []
    
    total_chunks = 0
    
    # Dynamically find all teacher files
    import glob
    teacher_files = sorted(glob.glob("Data/CSE_Teachers/t*.txt"))
    
    for file_path in teacher_files:
        filename = os.path.basename(file_path)
        # Load and chunk Teachers data
        with open(file_path, "r", encoding="utf-8") as f:
            teacher_content = f.read()
        
        # Split Teachers content into chunks
        teacher_chunks = text_splitter.split_text(teacher_content)
        
        for i, chunk in enumerate(teacher_chunks):
            if chunk.strip():
                document = Document(
                    page_content=chunk.strip(),
                    metadata={"source": filename, "chunk": i}
                )
                documents.append(document)
        
        doc_len = len(documents)
        if doc_len >= 50: 
            total_chunks += doc_len
            print(f"Adding {doc_len} chunks to vectore store")
            vector_store.add_documents(documents=documents)
            documents = []
            # time.sleep(60) # gemini embedding has 30,000 TPM

    if documents:
        vector_store.add_documents(documents=documents)

    print(f"Total chunks added: {total_chunks}")
    
retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})