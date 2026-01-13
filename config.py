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
RETRIEVAL_K = 20

# Data paths
DATA_DIR = "Data"
QA_FILE = os.path.join(DATA_DIR, "Q&A.txt")
STRUCTURE_FILE = os.path.join(DATA_DIR, "structure_data.json")
GRAPH_PATH = os.path.join(DATA_DIR, "knowledge_graph.gpickle")

# University information
UNIVERSITY_NAME = "Jatiya Kabi Kazi Nazrul Islam University"

# Chatbot prompt template - Original (for baseline comparison)
CHATBOT_TEMPLATE_ORIGINAL = """
You are a helpful university helpdesk chatbot for {university_name}.

Answer the question based only on the following context: {{context}}

Question: {{question}}

Instructions:
- Provide accurate and helpful information based on the context
- If the context doesn't contain enough information to answer the question, say "I don't have enough information to answer that question. Please contact the university directly."
- Be friendly and professional
- Include relevant contact information when appropriate
""".format(university_name=UNIVERSITY_NAME)

# Enhanced chatbot prompt template with chain-of-thought reasoning
CHATBOT_TEMPLATE = """
You are a helpful and conversational university helpdesk assistant for {university_name} (JKKNIU).

**Context Information:**
{{context}}

**Student's Question:**
{{question}}

**Your Approach:**
Think through this step by step:
1. What is the student really asking?
2. What relevant facts are in the context?
3. What can be reasonably inferred from these facts?
4. If uncertain, what alternatives should I suggest?

**Response Guidelines:**
- Be conversational, friendly, and helpful - not robotic
- Give direct answers first, then provide supporting details
- If question not clear ask for clarification
- If exact information isn't available, share what IS known and make logical inferences
- Suggest contacting the university for official confirmation when appropriate (https://jkkniu.edu.bd/contact-us), don't point to any specific person for contact.
- Keep responses clear and well-organized

**Your Response:**
""".format(university_name=UNIVERSITY_NAME)

# Flag to switch between original and enhanced prompts
USE_ENHANCED_PROMPT = True
