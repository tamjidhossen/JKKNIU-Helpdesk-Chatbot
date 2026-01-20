#!/usr/bin/env python3
"""
Generate Markdown Report from Advanced RAG Evaluation Results
=============================================================

This script takes evaluation results JSON and generates formatted
markdown tables matching the user's specification.

Usage:
    python generate_report.py evaluation/adv_rag_results_dummy.json
    python generate_report.py evaluation/adv_rag_results.json --output custom_report.md
"""

import json
import argparse
from typing import List, Dict, Any


def calculate_category_stats(results: List[Dict[str, Any]], category: str) -> Dict[str, Any]:
    """Calculate statistics for a specific category."""
    cat_results = [r for r in results if r["category"] == category and not r.get("rate_limited", False)]
    
    if not cat_results:
        return None
    
    ratings = [r["rating"] for r in cat_results]
    avg_rating = sum(ratings) / len(ratings)
    
    return {
        "avg_rating": avg_rating,
        "count": len(cat_results),
    }


def calculate_overall_stats(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate overall statistics."""
    evaluated = [r for r in results if not r.get("rate_limited", False) and r.get("rating") is not None]
    total = len(results)
    
    if not evaluated:
        return None
    
    ratings = [r["rating"] for r in evaluated]
    avg_rating = sum(ratings) / len(ratings)
    five_star_count = len([r for r in evaluated if r["rating"] == 5])
    five_star_pct = (five_star_count / len(evaluated)) * 100
    failed_count = len([r for r in evaluated if r["rating"] <= 2])
    rate_limited = len([r for r in results if r.get("rate_limited", False)])
    
    return {
        "total_questions": total,
        "evaluated": len(evaluated),
        "rate_limited": rate_limited,
        "avg_rating": avg_rating,
        "failed_count": failed_count,
        "five_star_count": five_star_count,
        "five_star_pct": five_star_pct,
    }


def generate_report(results_file: str, output_file: str = None):
    """Generate markdown report from results JSON."""
    
    # Load results
    with open(results_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    results = data["results"]
    metadata = data.get("metadata", {})
    
    # Calculate statistics
    categories = ["factual", "aggregation", "reasoning", "vague", "comparison", "multihop", "procedural"]
    category_stats = {}
    
    for cat in categories:
        stats = calculate_category_stats(results, cat)
        if stats:
            category_stats[cat] = stats
    
    overall_stats = calculate_overall_stats(results)
    
    # Generate markdown
    if output_file is None:
        output_file = results_file.replace(".json", "_report.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Advanced RAG Evaluation Report\n\n")
        f.write(f"**Generated:** {metadata.get('timestamp', 'N/A')}\n\n")
        f.write(f"**Model:** {metadata.get('chatbot_model', 'N/A')}\n\n")
        f.write(f"**Evaluation Model:** {metadata.get('evaluation_model', 'N/A')}\n\n")
        f.write("---\n\n")
        
        # Table 1: Category-wise Performance
        f.write("## Category-wise Performance Breakdown\n\n")
        f.write("| Category | Average Rating | Sample Count |\n")
        f.write("|----------|----------------|---------------|\n")
        
        for cat in categories:
            if cat in category_stats:
                stats = category_stats[cat]
                # Format category name
                cat_display = cat.replace("multihop", "Multi-hop").replace("vague", "Vague/General").title()
                f.write(f"| {cat_display} | {stats['avg_rating']:.2f} | {stats['count']} |\n")
        
        f.write("\n---\n\n")
        
        # Table 2: Overall Performance
        f.write("## Overall Performance Summary\n\n")
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        
        if overall_stats:
            f.write(f"| Questions Evaluated | {overall_stats['evaluated']}/{overall_stats['total_questions']} |\n")
            f.write(f"| Average Rating (1-5) | {overall_stats['avg_rating']:.2f} |\n")
            f.write(f"| Failed Queries (Rating ≤ 2) | {overall_stats['failed_count']} |\n")
            f.write(f"| 5-Star Responses | {overall_stats['five_star_pct']:.1f}% |\n")
            f.write(f"| Rate Limited | {overall_stats['rate_limited']} |\n")
        
        f.write("\n")
        
        if overall_stats and overall_stats["rate_limited"] > 0:
            f.write(f"*\\*{overall_stats['rate_limited']} queries in the Advanced RAG hit rate limits and were excluded*\n\n")
        
        f.write("---\n\n")
        f.write("## Notes\n\n")
        f.write("- **Plain RAG**: Baseline configuration without enhancements\n")
        f.write("- **Enhanced RAG**: With HyDE, Multi-Query, Hybrid BM25+Semantic, Pre-computed Summaries\n")
        f.write("- **Advanced RAG**: Enhanced RAG with additional optimizations and comprehensive evaluation\n")
    
    print(f"✅ Generated report: {output_file}")
    
    # Print summary to console
    print(f"\n📊 Summary:")
    if overall_stats:
        print(f"   Questions Evaluated: {overall_stats['evaluated']}/{overall_stats['total_questions']}")
        print(f"   Average Rating: {overall_stats['avg_rating']:.2f}/5")
        print(f"   5-Star Responses: {overall_stats['five_star_pct']:.0f}%")
        print(f"   Failed Queries (≤2): {overall_stats['failed_count']}")
        print(f"   Rate Limited: {overall_stats['rate_limited']}")


def main():
    parser = argparse.ArgumentParser(description="Generate report from evaluation results")
    parser.add_argument("results_file", help="Path to results JSON file")
    parser.add_argument("--output", "-o", help="Output markdown file path")
    args = parser.parse_args()
    
    generate_report(args.results_file, args.output)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
