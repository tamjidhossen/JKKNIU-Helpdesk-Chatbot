from dotenv import load_dotenv
import os
import time
import threading
import markdown
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.spinner import Spinner
from rich.live import Live
from rich.prompt import Prompt
from rich.text import Text
from rich.rule import Rule

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
from config import CHATBOT_TEMPLATE, GEMINI_MODEL, LLM_MODEL, DEBUG_EVIDENCE, USE_QUERY_REWRITE

console = Console()
model = ChatGoogleGenerativeAI(model=GEMINI_MODEL)
# model = ChatOllama(model=LLM_MODEL)
template = CHATBOT_TEMPLATE
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# Query Reuse Chain
rewrite_template = """
You are a search query optimizer for a university helpdesk.
Original Query: {question}

Task: Generate an optimized search query for retrieval.
1. **CRITICAL**: Preserve all specific identifiers (e.g., "CSE-15", "4th year", "B.Sc.", "GST") EXACTLY as they appear.
2. Expand acronyms if needed
3. Add relevant synonyms or related terms (e.g., "papers" -> "publications", "teachers" -> "faculty").
4. Remove conversational filler phrases.

Output ONLY the optimized query text. Do not explain.
"""
rewrite_prompt = ChatPromptTemplate.from_template(rewrite_template)
rewrite_chain = rewrite_prompt | model

def display_header():
    console.print("[bold cyan]JKKNIU Helpdesk Chatbot[/bold cyan]")
    console.print()

def create_spinner_text(message):
    return Text.assemble(
        ("🤖 ", "cyan"),
        (message, "white"),
        ("...", "dim white")
    )

def get_user_input():
    return Prompt.ask("[green]Ask your question[/green] [dim](quit to exit)[/dim]")

def get_optimized_query(question):
    """Refine query for better retrieval."""
    if not USE_QUERY_REWRITE:
        return question
    
    try:
        if DEBUG_EVIDENCE:
            console.print("[dim]Optimizing query...[/dim]")
        
        response = rewrite_chain.invoke({"question": question})
        optimized = response.content.replace('"','').strip()
        
        if DEBUG_EVIDENCE:
            console.print(f"[dim]Rewritten: {optimized}[/dim]")
        
        # Hybrid Approach: Return combined identifier to maximize BM25 recall
        # We assume the LLM might still miss the exact token format needed for BM25
        # but adds valuable semantic expansion.
        combined_query = f"{question} {optimized}"
        
        if len(combined_query) > 1000: # Safety cap
            return optimized
            
        return combined_query
    except Exception as e:
        if DEBUG_EVIDENCE:
             console.print(f"[dim]Rewrite warning: {e}[/dim]")
        return question

def format_context(docs):
    """Convert retrieved documents into a clean string for the LLM."""
    formatted_chunks = []
    for i, doc in enumerate(docs):
        source = os.path.basename(doc.metadata.get("source", "unknown"))
        content = doc.page_content.strip()
        # Add metadata markers if available
        meta_str = ""
        if "page" in doc.metadata:
            meta_str = f" | Page: {doc.metadata['page']}"
            
        chunk_text = f"Source: {source}{meta_str}\nContent: {content}"
        formatted_chunks.append(chunk_text)
    return "\n\n---\n\n".join(formatted_chunks)

def process_question_with_spinner(question):
    response_data = {"result": None, "elapsed_time": None, "error": None}
    
    def get_response():
        try:
            start_time = time.time()
            
            # 0. Query Optimization (Milestone 5)
            search_query = get_optimized_query(question)

            # 1. Retrieve
            docs = retriever.invoke(search_query)
            
            # 2. Evidence Check (Milestone 1)
            if not docs:
                response_data["result"] = "I don't have enough information to answer that question based on the available university documents."
                response_data["elapsed_time"] = time.time() - start_time
                return

            # 3. Format Context
            context_text = format_context(docs)
            
            # Debug logging
            if DEBUG_EVIDENCE:
                console.print()
                console.print(f"[dim]Evidence: {len(docs)} chunks retrieved[/dim]")
                for i, doc in enumerate(docs):
                    source = os.path.basename(doc.metadata.get("source", "unknown"))
                    console.print(f"[dim] {i+1}. {source}[/dim]")

            # 4. Generate
            result = chain.invoke({"context": context_text, "question": question})
            response_data["result"] = result.content
            response_data["elapsed_time"] = time.time() - start_time
        except Exception as e:
            response_data["error"] = str(e)
            if DEBUG_EVIDENCE:
                console.print_exception()
    
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
    return response_data

def render_response(content, elapsed_time):
    console.print()
    
    try:
        md = Markdown(content)
        response_panel = Panel(
            md,
            title="[bold blue]Response[/bold blue]",
            border_style="green",
            padding=(1, 2)
        )
    except:
        response_panel = Panel(
            content,
            title="[bold blue]Response[/bold blue]",
            border_style="green",
            padding=(1, 2)
        )
    
    console.print(response_panel)
    
    console.print(f"[dim]{elapsed_time:.2f}s[/dim]")
    console.print()

def main():
    display_header()
    
    while True:
        question = get_user_input()
        
        if question.lower() in ['quit', 'exit', 'q']:
            console.print("[yellow]Goodbye! 👋[/yellow]")
            break
        
        if not question.strip():
            console.print("[red]Please enter a valid question.[/red]")
            continue
        
        response_data = process_question_with_spinner(question)
        
        if response_data["error"]:
            console.print(f"[red]Error: {response_data['error']}[/red]")
            continue
        
        render_response(response_data["result"], response_data["elapsed_time"])

if __name__ == "__main__":
    main()
