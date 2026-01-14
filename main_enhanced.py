#!/usr/bin/env python3
"""
Enhanced JKKNIU Helpdesk Chatbot
================================

This is the improved version of the chatbot with:
- Enhanced query processing (HyDE, multi-query, hybrid search)
- Chain-of-thought prompting
- Better handling of aggregation and reasoning queries

Usage:
    python main_enhanced.py              # Run enhanced chatbot
    python main_enhanced.py --compare    # Run both original and enhanced for comparison
"""

from dotenv import load_dotenv
import os
import sys
import time
import argparse
import threading
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.prompt import Prompt
from rich.text import Text
from rich.table import Table

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from query_enhancer import EnhancedRetriever, QueryClassifier
from vector import retriever as basic_retriever
from config import CHATBOT_TEMPLATE, CHATBOT_TEMPLATE_ORIGINAL, GEMINI_MODEL
from api_keys import get_next_api_key

console = Console()


class EnhancedChatbot:
    """Enhanced chatbot with advanced RAG techniques."""
    
    def __init__(self, use_enhanced: bool = True):
        self.use_enhanced = use_enhanced
        
        if use_enhanced:
            self.retriever = EnhancedRetriever(
                use_hyde=True,
                use_multi_query=True,
                use_hybrid=True,
                use_keyword_expansion=True
            )
            self.prompt = ChatPromptTemplate.from_template(CHATBOT_TEMPLATE)
        else:
            self.retriever = basic_retriever
            self.prompt = ChatPromptTemplate.from_template(CHATBOT_TEMPLATE_ORIGINAL)
        
        self.conversation_history = []
    
    def _get_model(self):
        """Get a new model with the next API key in rotation."""
        api_key = get_next_api_key()
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key)
    
    def ask(self, question: str, history: str = "") -> dict:
        """Process a question and return the response with metadata."""
        result = {
            "question": question,
            "response": None,
            "elapsed_time": None,
            "query_type": None,
            "docs_retrieved": 0,
            "error": None,
        }
        
        try:
            start_time = time.time()
            
            # Classify query for display
            result["query_type"] = QueryClassifier.classify(question)
            
            # Retrieve context
            if self.use_enhanced:
                context_docs = self.retriever.retrieve(question)
            else:
                context_docs = self.retriever.invoke(question)
            
            result["docs_retrieved"] = len(context_docs)
            
            # Format context
            context = "\n\n".join([doc.page_content for doc in context_docs])
            
            # Get response with rotating API key
            model = self._get_model()
            chain = self.prompt | model
            response = chain.invoke({
                "context": context, 
                "question": question,
                "history": history
            })
            result["response"] = response.content
            result["elapsed_time"] = time.time() - start_time
            
            # Update conversation history
            self.conversation_history.append({
                "question": question,
                "response": response.content[:200] + "..." if len(response.content) > 200 else response.content
            })
            
        except Exception as e:
            error_str = str(e)
            if "exhausted" in error_str.lower() or "429" in error_str:
                result["response"] = "I'm receiving too many requests at the moment. Please wait a minute and try again."
                result["query_type"] = "Error"
            elif "blocked" in error_str.lower():
                result["response"] = "I'm sorry, I cannot answer that question as it might violate my safety guidelines."
                result["query_type"] = "Restricted"
            else:
                result["error"] = error_str
                result["response"] = "I encountered an error processing your request. Please try again later."
        
        return result


def display_header(enhanced: bool = True):
    """Display the chatbot header."""
    mode = "[bold green]ENHANCED[/bold green]" if enhanced else "[bold yellow]ORIGINAL[/bold yellow]"
    console.print(f"[bold cyan]JKKNIU Helpdesk Chatbot[/bold cyan] ({mode})")
    if enhanced:
        console.print("[dim]Using: HyDE + Multi-Query + Hybrid Search + Keyword Expansion + Chain-of-Thought[/dim]")
    console.print()


def create_spinner_text(message: str) -> Text:
    """Create spinner text for processing indicator."""
    return Text.assemble(
        ("🤖 ", "cyan"),
        (message, "white"),
        ("...", "dim white")
    )


def process_with_spinner(chatbot: EnhancedChatbot, question: str) -> dict:
    """Process question with a spinner animation."""
    response_data = {"result": None}
    
    def get_response():
        response_data["result"] = chatbot.ask(question)
    
    response_thread = threading.Thread(target=get_response)
    response_thread.daemon = True
    response_thread.start()
    
    with Live(
        create_spinner_text("Processing your question"),
        refresh_per_second=10,
        transient=True
    ) as live:
        spinner = Spinner("dots", text="Thinking...")
        while response_thread.is_alive():
            live.update(spinner)
            time.sleep(0.1)
    
    response_thread.join()
    return response_data["result"]


def render_response(result: dict, show_metadata: bool = True):
    """Render the chatbot response."""
    console.print()
    
    if result["error"]:
        console.print(f"[red]Error: {result['error']}[/red]")
        return
    
    try:
        md = Markdown(result["response"])
        response_panel = Panel(
            md,
            title="[bold blue]Response[/bold blue]",
            border_style="green",
            padding=(1, 2)
        )
    except:
        response_panel = Panel(
            result["response"],
            title="[bold blue]Response[/bold blue]",
            border_style="green",
            padding=(1, 2)
        )
    
    console.print(response_panel)
    
    if show_metadata:
        metadata = f"[dim]{result['elapsed_time']:.2f}s | "
        metadata += f"Query: {result['query_type']} | "
        metadata += f"Docs: {result['docs_retrieved']}[/dim]"
        console.print(metadata)
    
    console.print()


def run_comparison_mode(question: str):
    """Run both original and enhanced chatbots for comparison."""
    console.print("[bold]Running comparison mode...[/bold]\n")
    
    # Original
    console.print("[yellow]⏳ Original chatbot...[/yellow]")
    original_bot = EnhancedChatbot(use_enhanced=False)
    original_result = process_with_spinner(original_bot, question)
    
    # Enhanced
    console.print("[green]⏳ Enhanced chatbot...[/green]")
    enhanced_bot = EnhancedChatbot(use_enhanced=True)
    enhanced_result = process_with_spinner(enhanced_bot, question)
    
    # Display comparison
    table = Table(title="Comparison")
    table.add_column("Metric", style="cyan")
    table.add_column("Original", style="yellow")
    table.add_column("Enhanced", style="green")
    
    table.add_row("Time", f"{original_result['elapsed_time']:.2f}s", f"{enhanced_result['elapsed_time']:.2f}s")
    table.add_row("Query Type", original_result['query_type'], enhanced_result['query_type'])
    table.add_row("Docs Retrieved", str(original_result['docs_retrieved']), str(enhanced_result['docs_retrieved']))
    
    console.print(table)
    console.print()
    
    # Show responses
    console.print("[yellow bold]Original Response:[/yellow bold]")
    console.print(Panel(original_result["response"][:500] + "..." if len(original_result["response"]) > 500 else original_result["response"]))
    
    console.print("[green bold]Enhanced Response:[/green bold]")
    console.print(Panel(enhanced_result["response"][:500] + "..." if len(enhanced_result["response"]) > 500 else enhanced_result["response"]))


def main():
    parser = argparse.ArgumentParser(description="JKKNIU Enhanced Helpdesk Chatbot")
    parser.add_argument("--compare", action="store_true", help="Compare original vs enhanced for each query")
    parser.add_argument("--original", action="store_true", help="Use original (non-enhanced) mode")
    args = parser.parse_args()
    
    use_enhanced = not args.original
    
    display_header(enhanced=use_enhanced)
    
    chatbot = EnhancedChatbot(use_enhanced=use_enhanced)
    
    while True:
        question = Prompt.ask("[green]Ask your question[/green] [dim](quit to exit, /compare for comparison)[/dim]")
        
        if question.lower() in ['quit', 'exit', 'q']:
            console.print("[yellow]Goodbye! 👋[/yellow]")
            break
        
        if not question.strip():
            console.print("[red]Please enter a valid question.[/red]")
            continue
        
        if question.lower() == '/compare':
            console.print("[dim]Entering comparison mode. Type a question to compare both versions.[/dim]")
            compare_q = Prompt.ask("[green]Question for comparison[/green]")
            if compare_q.strip():
                run_comparison_mode(compare_q)
            continue
        
        if args.compare:
            run_comparison_mode(question)
        else:
            result = process_with_spinner(chatbot, question)
            render_response(result)


if __name__ == "__main__":
    main()
