import json
import time
import os
import sys
from datetime import datetime
from rich.console import Console
from rich.progress import track

# Add parent directory to path to import main and config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import chain, retriever, format_context, get_optimized_query

console = Console()

QUESTIONS_FILE = "eval/questions.json"
RESULTS_DIR = "eval/results"
RATE_LIMIT_DELAY = 10  # Seconds between requests (to check 15k TPM / 30 RPM)

def load_questions():
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)

def run_evaluation():
    questions = load_questions()
    results = []
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{RESULTS_DIR}/results_{timestamp}.json"
    output_md_filename = f"{RESULTS_DIR}/results_{timestamp}.md"

    console.print(f"[bold green]Starting evaluation with {len(questions)} questions...[/bold green]")
    console.print(f"Rate limit delay: {RATE_LIMIT_DELAY}s")
    
    try:
        for i, q_item in enumerate(questions):
            q_id = q_item["id"]
            question_text = q_item["question"]
            console.print(f"[{i+1}/{len(questions)}] Processing: {question_text}")
            
            start_time = time.time()
            try:
                # 1. Optimize Query
                search_query = get_optimized_query(question_text)
                
                # 2. Retrieve
                context_docs = retriever.invoke(search_query)
                
                # 3. Format
                context_str = format_context(context_docs)
                
                # 4. Generate
                if not context_docs:
                     model_output = "I don't have enough information to answer that question based on the available university documents."
                else: 
                     result = chain.invoke({"context": context_str, "question": question_text})
                     model_output = result.content
                
                elapsed = time.time() - start_time
                
                # Retrieve individual document contents for logging
                retrieved_docs_log = [{"content": doc.page_content, "metadata": doc.metadata} for doc in context_docs]

                results.append({
                    "id": q_id,
                    "category": q_item["category"],
                    "question": question_text,
                    "model_answer": model_output,
                    "retrieved_context": retrieved_docs_log,
                    "elapsed_time": elapsed,
                    "error": None
                })
                
            except Exception as e:
                console.print(f"[bold red]Error on Q{q_id}: {str(e)}[/bold red]")
                results.append({
                    "id": q_id,
                    "category": q_item["category"],
                    "question": question_text,
                    "model_answer": None,
                    "retrieved_context": [],
                    "elapsed_time": 0,
                    "error": str(e)
                })

            # Save partial results
            with open(output_filename, "w") as f:
                json.dump(results, f, indent=2)

            # Wait to respect rate limits
            if i < len(questions) - 1:
                time.sleep(RATE_LIMIT_DELAY)

    except KeyboardInterrupt:
        console.print("[bold yellow]Evaluation interrupted![/bold yellow]")
    
    # Generate Markdown Summary
    with open(output_md_filename, "w") as f:
        f.write(f"# Evaluation Results - {timestamp}\n\n")
        f.write(f"Total Questions: {len(questions)}\n\n")
        
        for res in results:
            f.write(f"## Q{res['id']}: {res['question']}\n\n")
            f.write(f"**Category:** {res['category']}\n\n")
            if res['error']:
                f.write(f"**Error:** {res['error']}\n\n")
            else:
                f.write(f"**Answer:**\n{res['model_answer']}\n\n")
                f.write(f"**Time:** {res['elapsed_time']:.2f}s\n\n")
                f.write("<details>\n<summary>Retrieved Context</summary>\n\n")
                for i, doc in enumerate(res['retrieved_context']):
                    f.write(f"**Chunk {i+1}** (Source: {doc['metadata'].get('source', 'unknown')}):\n")
                    f.write(f"> {doc['content'][:200]}...\n\n")
                f.write("</details>\n\n")
            f.write("---\n")
    
    console.print(f"[bold green]Evaluation complete! Results saved to {output_md_filename}[/bold green]")

if __name__ == "__main__":
    run_evaluation()
