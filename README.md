# University Helpdesk Chatbot

A RAG-based (Retrieval-Augmented Generation) chatbot for **Jatiya Kabi Kazi Nazrul Islam University** using LangChain and Ollama. This chatbot provides accurate information about university departments, faculty, admission procedures, and campus facilities.

## Features

- 🎓 University information and structure
- 👥 Faculty and department details
- 📚 Admission procedures and requirements
- 🏢 Campus facilities and services
- ⚡ Fast response times with local LLM
- 🔍 Context-aware answers using vector search

## Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- At least 4GB RAM (for running local models)

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

5. **Initialize the vector database:**
   ```bash
   python vector.py
   ```
   This will process the data files and create the local vector database.

6. **Run the chatbot:**
   ```bash
   python main.py
   ```

## Project Structure

```
├── main.py                 # Main chatbot interface
├── vector.py              # Vector database setup and retrieval
├── inspect_chunks.py      # Utility for inspecting stored chunks
├── requirements.txt       # Python dependencies
├── Data/
│   ├── Q&A.txt           # FAQ data
│   └── structure_data.json # University structure data
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Usage

1. Start the chatbot with `python main.py`
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

1. Update `Data/Q&A.txt` with new FAQ entries
2. Modify `Data/structure_data.json` for structured data
3. Delete the `chroma_langchain_db/` folder
4. Run `python vector.py` to rebuild the vector database

### Inspecting Vector Store

Use the inspection utility to see what's stored:
```bash
python inspect_chunks.py
```

### Customizing the Model

Edit `main.py` to change:
- The LLM model (line 6)
- The prompt template (lines 8-20)
- Response formatting

## Troubleshooting

**Common Issues:**

1. **"Model not found" error:**
   - Ensure Ollama is running: `ollama serve`
   - Pull required models: `ollama pull llama3.2`

2. **Empty responses:**
   - Check if vector database exists: run `python vector.py`
   - Verify data files are in the `Data/` folder

3. **Slow responses:**
   - Consider using a smaller model
   - Adjust chunk size and retrieval parameters

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Contact

For questions or support, please contact the development team or create an issue on GitHub.

---

*Built with ❤️ for Jatiya Kabi Kazi Nazrul Islam University*
