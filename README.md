# JKKNIU Helpdesk Chatbot

An advanced RAG (Retrieval-Augmented Generation) chatbot for **Jatiya Kabi Kazi Nazrul Islam University** designed to provide accurate information about departments, faculty, admissions, and facilities. This system leverages local LLMs (via Ollama) and Google Gemini for robust, context-aware responses.

## 🚀 Advanced RAG Architecture

This chatbot employs a sophisticated RAG pipeline to ensure high relevance and accuracy:

1.  **Query Classification**: Input queries are classified into types (Factual, Aggregation, Reasoning, Vague) to determine the optimal retrieval strategy.
2.  **Query Expansion**:
    - **HyDE (Hypothetical Document Embeddings)**: Generates hypothetical university documents to improve semantic matching for vague queries.
    - **Multi-Query Generation**: Breaks complex questions into simpler sub-queries.
    - **Keyword Generation**:Extracts specific academic keywords to boost BM25 keyword search.
3.  **Hybrid Retrieval**:
    - **Semantic Search**: Uses `nomic-embed-text` embeddings with ChromaDB to find conceptually similar content.
    - **Keyword Search**: Uses BM25 to find exact matches for names and specific terms that embeddings might miss.
4.  **Reciprocal Rank Fusion (RRF)**: Merges results from semantic and keyword searches to rank the most relevant documents higher.
5.  **Chain-of-Thought Generation**: The LLM uses the retrieved context to reason through the answer.

## 🔄 Automatic Database Synchronization

The system features an intelligent **Auto-Ingestion** mechanism handled by `vector.py`.

- **Registry-Based Tracking**: Uses `Data/General/ingestion_registry.json` to track MD5 hashes of all processed files.
- **Smart Sync**: On startup (if configured) or when running `python vector.py`, it scans the `Data/` directory.
    - **New/Modified Files**: Automatically detected, chunked, embedded, and added to the vector store.
    - **Consistency**: If the vector database is deleted, the registry resets to ensure a full fresh ingestion.
- **No Manual Scripts**: You do not need to manually run an "add data" script. Just drop text files into `Data/` and run the chatbot.

## 🛠️ Setup

1.  **Clone & Install**:

    ```bash
    git clone <repository-url>
    cd JKKNIU-Helpdesk
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file from `.env.example`:

    ```bash
    cp .env.example .env
    # Edit .env and add your GOOGLE_API_KEYS (comma-separated for rotation)
    ```

3.  **Ollama Models**:
    Ensure you have [Ollama](https://ollama.ai) installed and pull the required models:

    ```bash
    ollama pull llama3.2          # For local inference (optional)
    ollama pull nomic-embed-text  # For embeddings
    ```

4.  **Initialize Data**:
    ```bash
    python vector.py
    ```

## 💻 Usage

### interactive Chat

Run the main chatbot interface:

```bash
python main.py
```

### Comparison Mode

Compare the "Original" (baseline RAG) vs. "Enhanced" (Advanced RAG) pipeline side-by-side:

```bash
python main.py --compare
```

## 📂 Project Structure

```
├── main.py                 # Entry point for the CLI Chatbot
├── server.py               # FastAPI Backend Server
├── query_enhancer.py       # Advanced RAG logic (Classification, HyDE, Hybrid Search)
├── vector.py               # Vector DB management & Auto-ingestion logic
├── config.py               # Configuration settings
├── Data/                   # Knowledge base (Text files & Structure JSON)
│   ├── General/            # Registry & General info
│   └── ...                 # Departmental & Faculty data
└── web-ui/                 # Frontend React Application
```

## ⚠️ Notes

- **API Keys**: The system supports multiple Google API keys in `.env` for rotation to handle rate limits.
- **Database**: The vector database is stored locally in `chroma_langchain_db/`. Deleting this folder will trigger a full rebuild on the next run.
