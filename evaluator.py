#!/usr/bin/env python3
"""
JKKNIU Helpdesk Chatbot Evaluator
=================================

Evaluates chatbot accuracy with test questions across categories:
- Factual: Direct information retrieval
- Aggregation: Multi-document reasoning (e.g., "teacher with most publications")
- Reasoning: Inference from indirect facts (e.g., "can humanities student join CSE?")
- Vague: Ambiguous or incomplete queries

Usage:
    python evaluator.py --output results              # Creates results.json and results.md
    python evaluator.py --output baseline --dry-run   # Show questions without calling API
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
from config import CHATBOT_TEMPLATE, GEMINI_MODEL
from api_keys import get_next_api_key, get_total_keys

# Rate limiting configuration (Gemini free tier)
RPM_LIMIT = 30  # Requests per minute
TPM_LIMIT = 15000  # Tokens per minute  
RPD_LIMIT = 14400  # Requests per day
REQUEST_DELAY = 120 / RPM_LIMIT  # ~4 seconds between requests

# Test questions organized by category
TEST_QUESTIONS = {
    "factual": [
        # Direct information retrieval
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
        # Multi-document reasoning
        "Which CSE teacher has published the most research papers?",
        "How many professors are there in the CSE department?",
        "List all the teachers in CSE department with their designations.",
        "How many teachers were prev students/alumni of JKKNIU?",
        "How many total publications does the CSE department have?",
        "Which teachers are graduates of Islamic University?",
    ],
    "reasoning": [
        # Inference from indirect facts
        "Can a humanities student from HSC get admission to CSE?",
        "If I have GPA below 2.0 after first year, what happens?",
        "Can I improve a course grade if I got B+?",
        "Is CSE suitable for someone interested in machine learning?",
        "What happens if my attendance is below 60%?",
        "Can I transfer credits from another university to your CSE?",
    ],
    "vague": [
        # Ambiguous or incomplete queries
        "Tell me about CSE",
        "How do I get in?",
        "Who should I contact?",
        "What courses are there?",
        "Help with admission",
    ],
    "comparison": [
        # Comparing entities or options
        "Compare admission requirements for CSE and English department",
        "What's the difference between CSE thesis and project?",
        "Which professor specializes in image processing or medical imaging?",
    ],
    "multi_hop": [
        # Requires connecting multiple pieces of information
        "What are the prerequisites for the Machine Learning course?",
        "Which professor teaches Neural Signal Processing and what's their research area?",
        "If I want to study robotics, what optional course can I take and what's the prerequisite?",
    ],
}


def count_tokens_approx(text: str) -> int:
    """Approximate token count (roughly 4 chars per token for English)."""
    return len(text) // 4


class Evaluator:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.prompt = ChatPromptTemplate.from_template(CHATBOT_TEMPLATE)
        self.results = []
        self.request_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
    
    def _get_model(self):
        """Get a new model with the next API key in rotation."""
        api_key = get_next_api_key()
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key)
        
    def ask_question(self, question: str, category: str) -> Dict[str, Any]:
        """Send a question to the chatbot and record the response."""
        result = {
            "question": question,
            "category": category,
            "timestamp": datetime.now().isoformat(),
            "response": None,
            "elapsed_time": None,
            "error": None,
            "input_tokens_approx": 0,
            "output_tokens_approx": 0,
        }
        
        if self.dry_run:
            result["response"] = "[DRY RUN - No API call made]"
            result["elapsed_time"] = 0
            return result
        
        try:
            start_time = time.time()
            
            # Retrieve context
            context = retriever.invoke(question)
            context_text = "\n".join([doc.page_content for doc in context])
            
            # Estimate input tokens
            input_text = f"{context_text}\n{question}"
            result["input_tokens_approx"] = count_tokens_approx(input_text)
            self.total_input_tokens += result["input_tokens_approx"]
            
            # Get response using rotating API key
            model = self._get_model()
            chain = self.prompt | model
            response = chain.invoke({"context": context, "question": question})
            result["response"] = response.content
            result["elapsed_time"] = time.time() - start_time
            
            # Estimate output tokens
            result["output_tokens_approx"] = count_tokens_approx(response.content)
            self.total_output_tokens += result["output_tokens_approx"]
            
            self.request_count += 1
            
        except Exception as e:
            result["error"] = str(e)
            
        return result
    
    def run_evaluation(self) -> List[Dict[str, Any]]:
        """Run all test questions with rate limiting."""
        total_questions = sum(len(qs) for qs in TEST_QUESTIONS.values())
        current = 0
        
        print(f"\n🧪 Starting evaluation with {total_questions} questions")
        print(f"   Using {get_total_keys()} API keys for rotation")
        print(f"   Rate limit: {RPM_LIMIT} RPM, delay: {REQUEST_DELAY:.1f}s between requests")
        if self.dry_run:
            print("   [DRY RUN MODE - No API calls will be made]\n")
        else:
            print(f"   Estimated time: {total_questions * REQUEST_DELAY / 60:.1f} minutes\n")
        
        for category, questions in TEST_QUESTIONS.items():
            print(f"📂 Category: {category.upper()}")
            
            for question in questions:
                current += 1
                print(f"   [{current}/{total_questions}] {question[:50]}...")
                
                result = self.ask_question(question, category)
                self.results.append(result)
                
                if result["error"]:
                    print(f"      ❌ Error: {result['error']}")
                elif not self.dry_run:
                    print(f"      ✓ {result['elapsed_time']:.2f}s, ~{result['output_tokens_approx']} tokens")
                
                # Rate limiting delay
                if not self.dry_run and current < total_questions:
                    time.sleep(REQUEST_DELAY)
        
        print(f"\n✅ Evaluation complete!")
        print(f"   Total requests: {self.request_count}")
        print(f"   Approx input tokens: {self.total_input_tokens}")
        print(f"   Approx output tokens: {self.total_output_tokens}")
        
        return self.results
    
    def save_results(self, output_base: str):
        """Save results to JSON and Markdown files."""
        # Save JSON
        json_path = f"{output_base}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_questions": len(self.results),
                    "dry_run": self.dry_run,
                    "model": GEMINI_MODEL,
                    "total_input_tokens_approx": self.total_input_tokens,
                    "total_output_tokens_approx": self.total_output_tokens,
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        print(f"📄 Saved JSON: {json_path}")
        
        # Save Markdown for human viewing
        md_path = f"{output_base}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# JKKNIU Chatbot Evaluation Results\n\n")
            f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
            f.write(f"**Model:** {GEMINI_MODEL}\n")
            f.write(f"**Questions:** {len(self.results)}\n")
            f.write(f"**Dry Run:** {self.dry_run}\n\n")
            f.write(f"---\n\n")
            
            # Group by category
            for category in TEST_QUESTIONS.keys():
                category_results = [r for r in self.results if r["category"] == category]
                if not category_results:
                    continue
                    
                f.write(f"## {category.upper()}\n\n")
                
                for i, result in enumerate(category_results, 1):
                    f.write(f"### Q{i}: {result['question']}\n\n")
                    
                    if result["error"]:
                        f.write(f"**Error:** {result['error']}\n\n")
                    else:
                        f.write(f"**Response:**\n\n{result['response']}\n\n")
                        if result["elapsed_time"]:
                            f.write(f"*Time: {result['elapsed_time']:.2f}s | ")
                            f.write(f"Tokens: ~{result['output_tokens_approx']}*\n\n")
                    
                    f.write(f"**Your Rating (1-5):** ___\n\n")
                    f.write(f"---\n\n")
            
            # Summary section
            f.write(f"## Summary\n\n")
            f.write(f"| Category | Questions | Avg Time | Avg Tokens |\n")
            f.write(f"|----------|-----------|----------|------------|\n")
            
            for category in TEST_QUESTIONS.keys():
                cat_results = [r for r in self.results if r["category"] == category and not r["error"]]
                if cat_results:
                    avg_time = sum(r["elapsed_time"] or 0 for r in cat_results) / len(cat_results)
                    avg_tokens = sum(r["output_tokens_approx"] for r in cat_results) / len(cat_results)
                    f.write(f"| {category} | {len(cat_results)} | {avg_time:.2f}s | {avg_tokens:.0f} |\n")
            
            f.write(f"\n**Total: {self.total_input_tokens + self.total_output_tokens} tokens (approx)**\n")
        
        print(f"📄 Saved Markdown: {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate JKKNIU Helpdesk Chatbot")
    parser.add_argument("--output", "-o", default="evaluation_results",
                        help="Output filename base (without extension)")
    parser.add_argument("--dry-run", action="store_true",
                        help="List questions without making API calls")
    args = parser.parse_args()
    
    evaluator = Evaluator(dry_run=args.dry_run)
    evaluator.run_evaluation()
    evaluator.save_results(args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
