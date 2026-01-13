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
LLM_MODEL = "deepseek-r1:1.5b"
GEMINI_MODEL = "gemma-3-27b-it"
GOOGLE_EMBEDDING_MODEL = "models/gemini-embedding-001"

# Vector store configuration
VECTOR_DB_PATH = "./chroma_langchain_db"
COLLECTION_NAME = "university_helpdesk"

# Text splitting configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval configuration
RETRIEVAL_K = 15

# Feature Flags (Milestone 0)
USE_QUERY_REWRITE = True    # Use LLM to rewrite informal queries
USE_HYBRID_RETRIEVAL = True  # Use BM25 + Vector search
USE_RERANKER = True         # Use Cross-Encoder for reranking
USE_MMR = False              # Use Maximal Marginal Relevance
USE_SCORE_THRESHOLD = False  # Filter by similarity score
DEBUG_EVIDENCE = True        # Print used sources to console

# Data paths
DATA_DIR = "Data"
QA_FILE = os.path.join(DATA_DIR, "Q&A.txt")
STRUCTURE_FILE = os.path.join(DATA_DIR, "structure_data.json")

# University information
UNIVERSITY_NAME = "Jatiya Kabi Kazi Nazrul Islam University"

# Chatbot prompt template
CHATBOT_TEMPLATE = """
You are a helpful university helpdesk chatbot for {university_name}.

Context:
{{context}}

Question: {{question}}

Instructions:
1. Answer the question **ONLY** based on the provided context above. Do not use outside knowledge.
2. If the context does not contain the answer, say "I don't have enough information to answer that question based on the available documents." and ask a clarifying question if possible.
3. Be friendly, professional, and concise. Avoid long generic intros like "Hello! Here is the list...".
4. Do not mention "context" or "retrieved documents" in your answer to the user. Just answer the question directly.
""".format(university_name=UNIVERSITY_NAME)
