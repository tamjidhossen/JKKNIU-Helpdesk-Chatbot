# JKKNIU Chatbot RAG Evaluation Comparison

**Date:** 2026-01-13
**Metrics:** User Ratings (1-5 scale)

## 📊 Executive Summary

The enhanced chatbot shows a **10.5% overall improvement** in response quality compared to the baseline, with the most significant gains in **Aggregation (+62%)** and **Vague/General (+18.7%)** queries.

| Metric | Baseline | Enhanced | Improvement |
| :--- | :---: | :---: | :---: |
| **Questions Evaluated** | 31 | 29* | - |
| **Overall Average Rating** | **3.80** | **4.20** | **+10.5%** |

*\*2 questions in Enhanced run hit rate limits and were excluded from calculation.*

---

## 📈 Category-wise Performance

| Category | Baseline Avg | Enhanced Avg | Change | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **FACTUAL** | 4.88 | **5.00** | +2.5% | Consistent high accuracy. |
| **AGGREGATION** | 1.33 | **2.16** | **+62.4%** | Significant boost from pre-computed summaries, though some data gaps remain. |
| **REASONING** | 3.66 | **4.20** | +14.7% | Improved handling of admission/logic queries. |
| **VAGUE** | 4.00 | **4.75** | +18.7% | HyDE effectively resolved ambiguous "Tell me about..." queries. |
| **COMPARISON** | 5.00 | 5.00 | 0.0% | Maintained perfect score. |
| **MULTI-HOP** | 4.66 | 4.66 | 0.0% | Maintained high performance. |

---

## 📝 Detailed Analysis

### 1. AGGREGATION (Biggest Winner 🏆)
*   **Before:** The chatbot struggled to count or check multiple files (e.g., "Which teacher has most papers?"). Ratings were mostly 1s and 2s.
*   **After:** Pre-computed summaries allow it to answer questions like "How many professors?" and "Who has most publications?" much better.
*   **Recommendation:** To reach a 5/5, we need to ensure the raw data contains *explicit* headers for "Designation" and "Alumni Status" for every single teacher so the `data_enricher.py` can capture them perfectly.

### 2. REASONING & VAGUE
*   **Reasoning:** Improved from 3.66 to 4.20. The enhanced prompts helped with logic like "Can a humanities student get into CSE?".
*   **Vague:** HyDE generated good context for "Tell me about CSE", raising the average from 4.0 to 4.75.

### 3. Rate Limits
*   The enhanced parallel execution is faster but hit the free tier rate limit on 2 questions.
*   **Fix:** The API Key rotation is working, but with `parallel=4`, we might be hitting *per minute* token limits too fast. Reducing parallel workers to `2` or `3` would be safer for the free tier.

---

## 🔍 Data Gaps Identified (Opportunities for Improvement)
The following questions still received low ratings (<3) in the enhanced version, indicating missing data in the source text files:
*   *"How many teachers were prev students/alumni of JKKNIU?"* (Rated 1) - Source text lacks alma mater info for most teachers.
*   *"Which teachers are graduates of Islamic University?"* (Rated 2) - Partial info found, but likely incomplete.
