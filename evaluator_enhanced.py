#!/usr/bin/env python3
"""
Enhanced JKKNIU Helpdesk Chatbot Evaluator
==========================================

Evaluates the ENHANCED chatbot with all RAG improvements:
- HyDE (Hypothetical Document Embeddings)
- Multi-query generation for aggregation
- Hybrid BM25 + semantic search with RRF
- Pre-computed summaries

Supports PARALLEL execution using multiple API keys.

Usage:
    python evaluator_enhanced.py --output enhanced_results
    python evaluator_enhanced.py --output enhanced_results --parallel 4
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from query_enhancer import EnhancedRetriever, QueryClassifier
from config import CHATBOT_TEMPLATE, GEMINI_MODEL
from api_keys import get_next_api_key, get_total_keys

# Rate limiting - with 8 keys, can be more aggressive
RPM_LIMIT = 30
REQUEST_DELAY = 2.0  # Reduced delay with multiple keys

# Test questions (same as baseline)
TEST_QUESTIONS = {
    "factual": [
        "Who is the head of the CSE department?",
        "Give me the mail of Dr. A. H. M. Kamal?",
        "How many credits are required for CSE B.Sc. degree?",
        "What is CSE 425 course about?",
        "How many seats are available in CSE for 25-26 admission?",
        "What is the minimum GPA required to pass CSE at JKKNIU?",
        "What residential halls are available at JKKNIU?",
        "Who is the current and prev vc?",
    ],
    "aggregation": [
        "Which CSE teacher has published the most research papers?",
        "How many professors are there in the CSE department?",
        "List all the teachers in CSE department with their designations.",
        "How many teachers were prev students/alumni of JKKNIU?",
        "How many total publications does the CSE department have?",
        "Which teachers are graduates of Islamic University?",
    ],
    "reasoning": [
        "Can a humanities student from HSC get admission to CSE?",
        "If I have GPA below 2.0 after first year, what happens?",
        "Can I improve a course grade if I got B+?",
        "Is CSE suitable for someone interested in machine learning?",
        "What happens if my attendance is below 60%?",
        "Can I transfer credits from another university to your CSE?",
    ],
    "vague": [
        "Tell me about CSE",
        "How do I get in?",
        "Who should I contact?",
        "What courses are there?",
        "Help with admission",
    ],
    "comparison": [
        "Compare admission requirements for CSE and English department",
        "What's the difference between CSE thesis and project?",
        "Which professor specializes in image processing or medical imaging?",
    ],
    "multi_hop": [
        "What are the prerequisites for the Machine Learning course?",
        "Which professor teaches Neural Signal Processing and what's their research area?",
        "If I want to study robotics, what optional course can I take and what's the prerequisite?",
    ],
}


def count_tokens_approx(text: str) -> int:
    """Approximate token count."""
    return len(text) // 4


class EnhancedEvaluator:
    def __init__(self, dry_run: bool = False, parallel: int = 1):
        self.dry_run = dry_run
        self.parallel = min(parallel, get_total_keys())  # Cap at number of API keys
        self.prompt = ChatPromptTemplate.from_template(CHATBOT_TEMPLATE)
        self.retriever = EnhancedRetriever(
            use_hyde=True,
            use_multi_query=True,
            use_hybrid=True
        )
        self.results = []
        self.request_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def _get_model(self):
        """Get a model with the next API key."""
        api_key = get_next_api_key()
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key)
    
    def ask_question(self, question: str, category: str, index: int) -> Dict[str, Any]:
        """Process a single question."""
        result = {
            "question": question,
            "category": category,
            "index": index,
            "timestamp": datetime.now().isoformat(),
            "response": None,
            "elapsed_time": None,
            "error": None,
            "input_tokens_approx": 0,
            "output_tokens_approx": 0,
            "query_type": QueryClassifier.classify(question),
        }
        
        if self.dry_run:
            result["response"] = "[DRY RUN - No API call made]"
            result["elapsed_time"] = 0
            return result
        
        try:
            start_time = time.time()
            
            # Use enhanced retriever
            context_docs = self.retriever.retrieve(question)
            context_text = "\n".join([doc.page_content for doc in context_docs])
            
            # Estimate input tokens
            result["input_tokens_approx"] = count_tokens_approx(context_text + question)
            
            # Get response with rotating API key
            model = self._get_model()
            chain = self.prompt | model
            response = chain.invoke({"context": context_text, "question": question})
            
            result["response"] = response.content
            result["elapsed_time"] = time.time() - start_time
            result["output_tokens_approx"] = count_tokens_approx(response.content)
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_evaluation_parallel(self) -> List[Dict[str, Any]]:
        """Run evaluation with parallel execution."""
        all_questions = []
        for category, questions in TEST_QUESTIONS.items():
            for q in questions:
                all_questions.append((q, category))
        
        total = len(all_questions)
        print(f"\n🧪 Starting ENHANCED evaluation with {total} questions")
        print(f"   Using {get_total_keys()} API keys, {self.parallel} parallel workers")
        
        if self.dry_run:
            print("   [DRY RUN MODE]\n")
        
        results = [None] * total
        
        with ThreadPoolExecutor(max_workers=self.parallel) as executor:
            futures = {}
            for i, (question, category) in enumerate(all_questions):
                future = executor.submit(self.ask_question, question, category, i)
                futures[future] = i
            
            completed = 0
            for future in as_completed(futures):
                idx = futures[future]
                result = future.result()
                results[idx] = result
                completed += 1
                
                if result["error"]:
                    print(f"   [{completed}/{total}] ❌ {result['question'][:40]}... - {result['error'][:30]}")
                else:
                    print(f"   [{completed}/{total}] ✓ {result['question'][:40]}... ({result['elapsed_time']:.1f}s)")
        
        # Calculate totals
        for r in results:
            if r and not r["error"]:
                self.request_count += 1
                self.total_input_tokens += r["input_tokens_approx"]
                self.total_output_tokens += r["output_tokens_approx"]
        
        self.results = results
        
        print(f"\n✅ Evaluation complete!")
        print(f"   Total requests: {self.request_count}")
        print(f"   Approx tokens: {self.total_input_tokens + self.total_output_tokens}")
        
        return results
    
    def run_evaluation_sequential(self) -> List[Dict[str, Any]]:
        """Run evaluation sequentially (for comparison)."""
        total_questions = sum(len(qs) for qs in TEST_QUESTIONS.values())
        current = 0
        
        print(f"\n🧪 Starting ENHANCED evaluation with {total_questions} questions")
        print(f"   Using {get_total_keys()} API keys (sequential mode)")
        print(f"   Delay: {REQUEST_DELAY}s between requests")
        
        if self.dry_run:
            print("   [DRY RUN MODE]\n")
        
        for category, questions in TEST_QUESTIONS.items():
            print(f"📂 Category: {category.upper()}")
            
            for question in questions:
                current += 1
                print(f"   [{current}/{total_questions}] {question[:50]}...")
                
                result = self.ask_question(question, category, current - 1)
                self.results.append(result)
                
                if result["error"]:
                    print(f"      ❌ Error: {result['error'][:50]}")
                elif not self.dry_run:
                    self.request_count += 1
                    self.total_input_tokens += result["input_tokens_approx"]
                    self.total_output_tokens += result["output_tokens_approx"]
                    print(f"      ✓ {result['elapsed_time']:.2f}s, ~{result['output_tokens_approx']} tokens")
                
                if not self.dry_run and current < total_questions:
                    time.sleep(REQUEST_DELAY)
        
        print(f"\n✅ Evaluation complete!")
        print(f"   Total requests: {self.request_count}")
        print(f"   Approx tokens: {self.total_input_tokens + self.total_output_tokens}")
        
        return self.results
    
    def save_results(self, output_base: str):
        """Save results to JSON and Markdown."""
        # Sort results by index for consistent ordering
        sorted_results = sorted(self.results, key=lambda x: x["index"])
        
        # Save JSON
        json_path = f"{output_base}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "enhanced": True,
                    "total_questions": len(sorted_results),
                    "dry_run": self.dry_run,
                    "model": GEMINI_MODEL,
                    "parallel_workers": self.parallel,
                    "features": ["HyDE", "Multi-Query", "Hybrid-BM25", "Pre-computed Summaries"],
                },
                "results": sorted_results
            }, f, indent=2, ensure_ascii=False)
        print(f"📄 Saved JSON: {json_path}")
        
        # Save Markdown
        md_path = f"{output_base}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# JKKNIU ENHANCED Chatbot Evaluation Results\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Model:** {GEMINI_MODEL}\n")
            f.write(f"**Enhanced Features:** HyDE, Multi-Query, Hybrid-BM25, Pre-computed Summaries\n")
            f.write(f"**Questions:** {len(sorted_results)}\n\n")
            f.write(f"---\n\n")
            
            for category in TEST_QUESTIONS.keys():
                category_results = [r for r in sorted_results if r["category"] == category]
                if not category_results:
                    continue
                
                f.write(f"## {category.upper()}\n\n")
                
                for i, result in enumerate(category_results, 1):
                    f.write(f"### Q{i}: {result['question']}\n\n")
                    f.write(f"**Query Type:** {result.get('query_type', 'unknown')}\n\n")
                    
                    if result["error"]:
                        f.write(f"**Error:** {result['error']}\n\n")
                    else:
                        f.write(f"**Response:**\n\n{result['response']}\n\n")
                        if result["elapsed_time"]:
                            f.write(f"*Time: {result['elapsed_time']:.2f}s | Tokens: ~{result['output_tokens_approx']}*\n\n")
                    
                    f.write(f"**Your Rating (1-5):** ___\n\n")
                    f.write(f"---\n\n")
            
            # Summary
            f.write(f"## Summary\n\n")
            f.write(f"| Category | Questions | Avg Time | Avg Tokens |\n")
            f.write(f"|----------|-----------|----------|------------|\n")
            
            for category in TEST_QUESTIONS.keys():
                cat_results = [r for r in sorted_results if r["category"] == category and not r["error"]]
                if cat_results:
                    avg_time = sum(r["elapsed_time"] or 0 for r in cat_results) / len(cat_results)
                    avg_tokens = sum(r["output_tokens_approx"] for r in cat_results) / len(cat_results)
                    f.write(f"| {category} | {len(cat_results)} | {avg_time:.2f}s | {avg_tokens:.0f} |\n")
        
        print(f"📄 Saved Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate ENHANCED JKKNIU Helpdesk Chatbot")
    parser.add_argument("--output", "-o", default="enhanced_results",
                        help="Output filename base")
    parser.add_argument("--dry-run", action="store_true",
                        help="List questions without making API calls")
    parser.add_argument("--parallel", "-p", type=int, default=4,
                        help="Number of parallel workers (default: 4)")
    parser.add_argument("--sequential", action="store_true",
                        help="Run sequentially instead of parallel")
    args = parser.parse_args()
    
    evaluator = EnhancedEvaluator(dry_run=args.dry_run, parallel=args.parallel)
    
    if args.sequential:
        evaluator.run_evaluation_sequential()
    else:
        evaluator.run_evaluation_parallel()
    
    evaluator.save_results(args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
