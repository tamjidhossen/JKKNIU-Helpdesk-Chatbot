# University Helpdesk Chatbot

A RAG-based (Retrieval-Augmented Generation) chatbot for **Jatiya Kabi Kazi Nazrul Islam University** using LangChain and Ollama. This chatbot provides accurate information about university departments, faculty, admission procedures, and campus facilities.

## Features

- 🎓 University information and structure
- 👥 Faculty and department details
- 📚 Admission procedures and requirements
- 🏢 Campus facilities and services
- ⚡ Fast response times with local LLM
- 🔍 Context-aware answers using vector search
- 📊 Optional LangSmith integration for monitoring and debugging

## Setup

1. **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd helpdesk-chatbot
    ```

2. **Create and activate virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Install and setup Ollama models:**

    ```bash
    # Install Ollama from https://ollama.ai
    ollama pull llama3.2          # Main language model
    ollama pull nomic-embed-text  # Embedding model
    ```

5. **Configure LangSmith (Optional):**

    LangSmith is a platform for monitoring, debugging, and improving LLM applications. You can either enable it for enhanced observability or disable it completely.

    **Option A: Enable LangSmith**

    Create a `.env` file in the project root:

    ```bash
    LANGSMITH_TRACING=true
    LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
    LANGSMITH_API_KEY="your_api_key_here"
    LANGSMITH_PROJECT="your_project_name"
    ```

    To get your API key:
    1. Sign up at [LangSmith](https://smith.langchain.com/)
    2. Create a new project
    3. Copy your API key from the settings
    4. Replace `your_api_key_here` and `your_project_name` in the `.env` file

    **Option B: Disable LangSmith**

    Create a `.env` file with tracing disabled:

    ```bash
    LANGSMITH_TRACING=false
    ```

    Or simply don't create a `.env` file - the application will work without LangSmith.

6. **Initialize the vector database:**

    ```bash
    python vector.py
    ```

    This will process the data files and create the local vector database.

7. **Run the chatbot:**
    ```bash
    python main_enhanced.py
    ```

## Project Structure

```
├── main_enhanced.py        # Main chatbot interface
├── vector.py              # Vector database setup and retrieval
├── evaluation/            # Evaluation scripts and results
│   ├── evaluator.py       # Baseline evaluation script
│   ├── evaluator_enhanced.py # Enhanced evaluation script
│   └── *.md, *.json       # Evaluation results
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (LangSmith config)
├── Data/
│   ├── Q&A.txt           # FAQ data
│   └── structure_data.json # University structure data
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Usage

1. Start the chatbot with `python main_enhanced.py`
2. Ask questions about:
    - University departments and faculty
    - Admission procedures
    - Campus facilities
    - Academic programs
    - Contact information

3. Type `q` to quit the application

### Example Questions

- "What departments are available in the university?"
- "Who is the head of Computer Science department?"
- "What are the admission requirements?"
- "Tell me about the residential halls"
- "How can I contact the registrar office?"

## Configuration

The chatbot uses the following default configurations:

- **LLM Model:** llama3.2
- **Embedding Model:** nomic-embed-text
- **Chunk Size:** 500 characters
- **Chunk Overlap:** 50 characters
- **Retrieval Results:** Top 5 similar chunks
- **LangSmith:** Optional (configured via .env file)

## Data Sources

The chatbot uses two main data sources:

1. **Q&A.txt:** Frequently asked questions and answers
2. **structure_data.json:** Structured university data including:
    - University information
    - Department details
    - Faculty information
    - Authority contacts

## Development

### Adding New Data

1. Update `Data/` text files with new information
2. The system automatically syncs new data on startup if `AUTO_UPDATE_VECTOR_DB` is True in `config.py`
3. Alternatively, run `python vector.py` to manually rebuild the vector database

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
