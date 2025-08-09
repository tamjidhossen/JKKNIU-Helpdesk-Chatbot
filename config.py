"""Configuration settings for the University Helpdesk Chatbot"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Verify LangSmith configuration
if os.getenv("LANGSMITH_TRACING") == "true":
    print("LangSmith tracing enabled")
    print(f"Project: {os.getenv('LANGSMITH_PROJECT')}")
else:
    print("LangSmith tracing disabled")

# Model configurations
EMBEDDING_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma3"

# Vector store configuration
VECTOR_DB_PATH = "./chroma_langchain_db"
COLLECTION_NAME = "university_helpdesk"

# Text splitting configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Retrieval configuration
RETRIEVAL_K = 5

# Data paths
DATA_DIR = "Data"
QA_FILE = os.path.join(DATA_DIR, "Q&A.txt")
STRUCTURE_FILE = os.path.join(DATA_DIR, "structure_data.json")

# University information
UNIVERSITY_NAME = "Jatiya Kabi Kazi Nazrul Islam University"

# Chatbot prompt template
CHATBOT_TEMPLATE = """
You are a helpful university helpdesk chatbot for {university_name}.

Answer the question based only on the following context: {{context}}

Question: {{question}}

Instructions:
- Provide accurate and helpful information based on the context
- If the context doesn't contain enough information to answer the question, say "I don't have enough information to answer that question. Please contact the university directly."
- Be friendly and professional
- Include relevant contact information when appropriate
""".format(university_name=UNIVERSITY_NAME)
