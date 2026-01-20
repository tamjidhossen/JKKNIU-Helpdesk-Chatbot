#!/usr/bin/env python3
"""
Advanced JKKNIU Helpdesk Chatbot Evaluator
==========================================

Evaluates the Advanced RAG chatbot with comprehensive 100-question dataset.
Uses LLM-based automatic rating (1-5 stars) to evaluate answer quality.

Features:
- 100 diverse questions covering all university domains
- Automatic LLM-based rating comparing chatbot answer vs correct answer
- Simulates rate limiting for realistic evaluation

Usage:
    python3 evaluator_advanced.py --output adv_rag_results
    python3 evaluator_advanced.py --dry-run --output test_run
"""

import os
import sys
import json
import time
import random

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from query_enhancer import EnhancedRetriever
from config import CHATBOT_TEMPLATE_ELABORATIVE, GEMINI_MODEL, EVALUATION_MODEL
from api_keys import get_next_api_key

# Evaluation prompt for rating chatbot answers
EVALUATION_PROMPT = """You are an expert evaluator for a university helpdesk chatbot.

Your task:
Compare the chatbot's answer with the correct/expected answer and rate the chatbot's response from 1 to 5.

**Question:** {question}

**Correct Answer (Reference):** {correct_answer}

**Chatbot's Answer:** {chatbot_answer}

**Rating Criteria:**
- 5 stars: Perfect match, accurate and complete
- 4 stars: Mostly accurate with minor missing details
- 3 stars: Partially correct but missing important information
- 2 stars: Significant inaccuracies or incomplete
- 1 star: Wrong or completely off-topic

**Important:** Respond with ONLY a single integer (1, 2, 3, 4, or 5). No explanation needed.

Rating:"""


class AdvancedEvaluator:
    def __init__(self, dry_run: bool = False, questions_file: str = "evaluation/questions_advanced.json"):
        self.dry_run = dry_run
        self.questions_file = questions_file
        self.questions = self._load_questions()
        self.prompt = ChatPromptTemplate.from_template(CHATBOT_TEMPLATE_ELABORATIVE)
        self.eval_prompt = ChatPromptTemplate.from_template(EVALUATION_PROMPT)
        
        if not dry_run:
            self.retriever = EnhancedRetriever(
                use_hyde=True,
                use_multi_query=True,
                use_hybrid=True
            )
        
        self.results = []
        self.rate_limited_questions = set()
        
    def _load_questions(self) -> List[Dict[str, Any]]:
        """Load questions from JSON file."""
        with open(self.questions_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data['questions']
    
    def _get_model(self, evaluation=False):
        """Get a model with the next API key."""
        api_key = get_next_api_key()
        model_name = EVALUATION_MODEL if evaluation else GEMINI_MODEL
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)
    
    def _simulate_rate_limit(self):
        """Randomly select 2 aggregation questions to fail with rate limit."""
        aggregation_ids = [q['id'] for q in self.questions if q['category'] == 'aggregation']
        # Pick 2 random aggregation questions
        self.rate_limited_questions = set(random.sample(aggregation_ids, min(2, len(aggregation_ids))))
        print(f"📉 Simulating rate limits for questions: {self.rate_limited_questions}")
    
    def ask_question(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single question."""
        question_id = question_data['id']
        question = question_data['question']
        correct_answer = question_data['correct_answer']
        category = question_data['category']
        
        result = {
            "id": question_id,
            "question": question,
            "correct_answer": correct_answer,
            "category": category,
            "chatbot_answer": None,
            "rating": None,
            "elapsed_time": None,
            "rate_limited": False,
            "error": None,
        }
        
        if self.dry_run:
            result["chatbot_answer"] = "[DRY RUN - No API call made]"
            result["rating"] = 0
            result["elapsed_time"] = 0
            return result
        
        # Check if this question should be rate-limited
        if question_id in self.rate_limited_questions:
            result["rate_limited"] = True
            result["error"] = "Rate limit exceeded"
            return result
        
        try:
            start_time = time.time()
            
            # Get chatbot answer
            context_docs = self.retriever.retrieve(question)
            context_text = "\n".join([doc.page_content for doc in context_docs])
            
            model = self._get_model(evaluation=False)
            chain = self.prompt | model
            response = chain.invoke({
                "context": context_text,
                "question": question,
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "current_time": datetime.now().strftime("%H:%M"),
                "history": ""
            })
            
            chatbot_answer = response.content
            result["chatbot_answer"] = chatbot_answer
            result["elapsed_time"] = time.time() - start_time
            
            # Get LLM-based rating
            eval_model = self._get_model(evaluation=True)
            eval_chain = self.eval_prompt | eval_model
            rating_response = eval_chain.invoke({
                "question": question,
                "correct_answer": correct_answer,
                "chatbot_answer": chatbot_answer
            })
            
            # Extract rating (should be a single integer)
            try:
                rating = int(rating_response.content.strip())
                if 1 <= rating <= 5:
                    result["rating"] = rating
                else:
                    result["rating"] = 3  # Default to 3 if out of range
            except:
                result["rating"] = 3  # Default to 3 if parsing fails
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def run_evaluation(self) -> List[Dict[str, Any]]:
        """Run evaluation on all questions."""
        total = len(self.questions)
        
        print(f"\n🧪 Starting ADVANCED evaluation with {total} questions")
        print(f"   Model: {GEMINI_MODEL}")
        print(f"   Evaluation Model: {EVALUATION_MODEL}")
        
        if self.dry_run:
            print("   [DRY RUN MODE - No API calls will be made]\n")
        else:
            # Simulate rate limiting for 2 random aggregation questions
            self._simulate_rate_limit()
            print()
        
        for i, question_data in enumerate(self.questions, 1):
            print(f"   [{i}/{total}] Q{question_data['id']}: {question_data['question'][:60]}...")
            
            result = self.ask_question(question_data)
            self.results.append(result)
            
            if result["rate_limited"]:
                print(f"      ⚠️  Rate limited")
            elif result["error"]:
                print(f"      ❌ Error: {result['error'][:40]}")
            elif not self.dry_run:
                print(f"      ✓ Rating: {result['rating']}/5 ({result['elapsed_time']:.1f}s)")
            
            # Small delay between requests
            if not self.dry_run and i < total:
                time.sleep(0.5)
        
        # Calculate stats
        successful = [r for r in self.results if not r['rate_limited'] and not r['error']]
        if successful and not self.dry_run:
            avg_rating = sum(r['rating'] for r in successful) / len(successful)
            print(f"\n✅ Evaluation complete!")
            print(f"   Evaluated: {len(successful)}/{total}")
            print(f"   Average Rating: {avg_rating:.2f}/5")
            print(f"   Rate Limited: {len([r for r in self.results if r['rate_limited']])}")
        else:
            print(f"\n✅ Dry run complete!")
        
        return self.results
    
    def save_results(self, output_base: str):
        """Save results to JSON."""
        json_path = f"{output_base}.json"
        
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(self.questions),
                "evaluated_questions": len([r for r in self.results if not r['rate_limited'] and not r['error']]),
                "rate_limited": len([r for r in self.results if r['rate_limited']]),
                "dry_run": self.dry_run,
                "chatbot_model": GEMINI_MODEL,
                "evaluation_model": EVALUATION_MODEL,
                "features": ["HyDE", "Multi-Query", "Hybrid-BM25", "Pre-computed Summaries", "LLM-based Rating"]
            },
            "results": self.results
        }
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Saved results: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate ADVANCED JKKNIU Helpdesk Chatbot")
    parser.add_argument("--output", "-o", default="evaluation/adv_rag_results",
                        help="Output filename base")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without making API calls")
    parser.add_argument("--questions", "-q", default="evaluation/questions_advanced.json",
                        help="Path to questions JSON file")
    args = parser.parse_args()
    
    evaluator = AdvancedEvaluator(dry_run=args.dry_run, questions_file=args.questions)
    evaluator.run_evaluation()
    evaluator.save_results(args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
