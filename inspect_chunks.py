from vector import vector_store

# Get all documents from the vector store
all_docs = vector_store.get()

print(f"Total chunks in vector store: {len(all_docs['documents'])}")

for i, (doc_content, metadata) in enumerate(zip(all_docs['documents'], all_docs['metadatas'])):
    print(f"\nCHUNK {i+1}:")
    print(f"Metadata: {metadata}")
    print(f"Content: {doc_content}")
    print("-" * 60)