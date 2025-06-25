from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
from config import (
    EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME,
    CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_K,
    QA_FILE, STRUCTURE_FILE
)

# Initialize embeddings and text splitter
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
)

db_location = VECTOR_DB_PATH
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []
    
    # Load and chunk Q&A data
    with open(QA_FILE, "r", encoding="utf-8") as f:
        qa_content = f.read()
    
    # Split Q&A content into chunks
    qa_chunks = text_splitter.split_text(qa_content)
    
    for i, chunk in enumerate(qa_chunks):
        if chunk.strip():
            document = Document(
                page_content=chunk.strip(),
                metadata={"source": "Q&A", "chunk": i}
            )
            documents.append(document)
    
    # Load and process structured data
    with open(STRUCTURE_FILE, "r", encoding="utf-8") as f:
        structured_data = json.load(f)
    
    # Process university info
    uni_info = structured_data["university"]
    uni_text = f"University: {uni_info['name']}\nLocation: {uni_info['location']}\nFaculties: {uni_info['faculties']}\nDepartments: {uni_info['departments']}\nStudents: {uni_info['students']}"
    
    # Add residential halls info
    halls = uni_info["residential_halls"]
    halls_text = "Residential Halls:\n" + "\n".join([f"- {hall['name']} ({hall['gender']})" for hall in halls])
    uni_text += f"\n{halls_text}"
    
    # Chunk university info if it's long
    uni_chunks = text_splitter.split_text(uni_text)
    for i, chunk in enumerate(uni_chunks):
        document = Document(
            page_content=chunk,
            metadata={"source": "structured_data", "type": "university_info", "chunk": i}
        )
        documents.append(document)
    
    # Process faculty info (chunk each faculty member's info)
    cse_dept = structured_data["departments"][0]
    for j, teacher in enumerate(cse_dept["teachers"]):
        # Handle phone field properly (could be string, list, or None)
        phone = teacher.get('phone', 'N/A')
        if isinstance(phone, list):
            phone = ', '.join(phone)
        elif phone is None:
            phone = 'N/A'
    
    teacher_text = f"Name: {teacher['name']}\nDesignation: {teacher['designation']}\nDepartment: Computer Science and Engineering\nEmail: {teacher['email']}\nPhone: {phone}\nResearch Areas: {', '.join(teacher.get('research_areas', []))}\nCourses: {', '.join(teacher.get('courses_taught', []))}"
    
    # Usually faculty info is short, but chunk if needed
    teacher_chunks = text_splitter.split_text(teacher_text)
    for i, chunk in enumerate(teacher_chunks):
        document = Document(
            page_content=chunk,
            metadata={"source": "structured_data", "type": "faculty", "faculty_id": j, "chunk": i}
        )
        documents.append(document)

    # Process authority info (chunk each authority member's info)
    for j, authority in enumerate(structured_data["authority"]):
        auth_text = f"Name: {authority['name']}\nDesignation: {authority['designation']}\nEmail: {authority['email']}\nOffice: {authority.get('office', 'N/A')}"
        
        # Chunk authority info if needed
        auth_chunks = text_splitter.split_text(auth_text)
        for i, chunk in enumerate(auth_chunks):
            document = Document(
                page_content=chunk,
                metadata={"source": "structured_data", "type": "authority", "authority_id": j, "chunk": i}
            )
            documents.append(document)

# Create vector store
vector_store = Chroma(
    collection_name=COLLECTION_NAME,
    persist_directory=db_location,
    embedding_function=embeddings
)

if add_documents:
    vector_store.add_documents(documents=documents)
    print(f"Added {len(documents)} chunks to the vector store")

retriever = vector_store.as_retriever(search_kwargs={"k": RETRIEVAL_K})