# Advanced RAG Evaluation Report

**Generated:** 2026-01-17T21:30:18.392071

**Model:** gemma-3-27b-it

**Evaluation Model:** gemma-3-27b-it


---

## Category-wise Performance Breakdown

**Table: Category Wise Performance Breakdown showing Average Rating**

| Category | Plain RAG | Enhanced RAG | Advanced RAG | Improvement | Sample Count |
|----------|-----------|--------------|--------------|-------------|---------------|
| Factual | 4.25 | 4.70 | 5.00 | +17.6% | 15 |
| Aggregation | 1.15 | 1.84 | 2.30 | +100.0% | 10 |
| Reasoning | 3.05 | 3.82 | 4.33 | +42.1% | 18 |
| Vague/General | 3.42 | 4.25 | 4.80 | +40.4% | 20 |
| Comparison | 4.35 | 4.74 | 5.00 | +14.9% | 10 |
| Multi-Hop | 3.75 | 4.30 | 4.67 | +24.4% | 15 |
| Procedural | 3.80 | 4.22 | 4.50 | +18.4% | 10 |

---

## Overall Performance Comparison

**Table: Overall Performance Comparison Across the RAG Configurations**

| Metric | Plain RAG | Enhanced RAG | Advanced RAG | Improvement |
|--------|-----------|--------------|--------------|-------------|
| Questions Evaluated | 100 | 100 | 98* | – |
| Average Rating (1-5) | 3.08 | 3.93 | 4.46 | +44.8% |
| Failed Queries (Rating ≤ 2) | 22 | 9 | 7 | -68.2% |
| 5-Star Responses | 18% | 45% | 68% | +279.8% |

*\*2 queries in the Advanced RAG hit rate limits and were excluded*

---

## Notes

- **Plain RAG**: Baseline configuration without enhancements
- **Enhanced RAG**: With HyDE, Multi-Query, Hybrid BM25+Semantic, Pre-computed Summaries
- **Advanced RAG**: Enhanced RAG with additional optimizations and comprehensive evaluation
