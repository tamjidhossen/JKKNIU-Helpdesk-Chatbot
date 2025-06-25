#!/bin/bash
# Setup script for University Helpdesk Chatbot

echo "🎓 Setting up University Helpdesk Chatbot..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama from https://ollama.ai"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "⬇️ Installing Python packages..."
pip install -r requirements.txt

# Pull Ollama models
echo "🤖 Pulling Ollama models..."
ollama pull llama3.2
ollama pull nomic-embed-text

# Initialize vector database
echo "🔍 Initializing vector database..."
python vector.py

echo "✅ Setup complete!"
echo ""
echo "To run the chatbot:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run the chatbot: python main.py"
echo ""
echo "Type 'q' to quit the chatbot when running."
