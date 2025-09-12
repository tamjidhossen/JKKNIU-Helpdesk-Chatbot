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
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
from config import CHATBOT_TEMPLATE, GEMINI_MODEL

console = Console()
model = ChatGoogleGenerativeAI(model=GEMINI_MODEL)
template = CHATBOT_TEMPLATE
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

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

def process_question_with_spinner(question):
    response_data = {"result": None, "elapsed_time": None, "error": None}
    
    def get_response():
        try:
            start_time = time.time()
            context = retriever.invoke(question)
            result = chain.invoke({"context": context, "question": question})
            response_data["result"] = result.content
            response_data["elapsed_time"] = time.time() - start_time
        except Exception as e:
            response_data["error"] = str(e)
    
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
