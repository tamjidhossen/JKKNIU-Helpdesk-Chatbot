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

## 🛠️ Current Technical Stack (Enhanced)

The "Enhanced" chatbot achieves these results using a multi-stage RAG pipeline:

### 1. Hybrid Retrieval (BM25 + Semantic)
*   **Problem Solved:** Semantic search misses exact keywords (e.g., "CSE 425"), while keyword search misses context.
*   **Method:** We run both searches and combine results using **Reciprocal Rank Fusion (RRF)**.

### 2. Hypothethical Document Embeddings (HyDE)
*   **Problem Solved:** Queries like "Tell me about CSE" are too short to match detailed documents.
*   **Method:** The LLM hallucinates a "fake" ideal document (e.g., "The CSE Dept at JKKNIU was established in...") and uses *that* for retrieval, significantly boosting relevance for vague queries.

### 3. Multi-Query Expansion
*   **Problem Solved:** Complex questions often need data from multiple sources.
*   **Method:** The system breaks down one question into 3 distinct sub-queries to cast a wider net.

### 4. Pre-computed Summaries
*   **Problem Solved:** "Counting" or "Aggregating" across 20+ files is impossible for standard RAG.
*   **Method:** We pre-generate summary docs (Publication Stats, Faculty Overview) so the bot can just "read" the answer directly.

### 5. Intelligent Keyword Expansion
*   **Problem Solved:** Users use abbreviations like "IU" or "JnU" that aren't in the text.
*   **Method:** An LLM generates precise search keywords (e.g., "IU" → "Islamic University", "Kushtia") which are fed into the BM25 retriever to catch relevant documents that semantic search might miss.

---

## 🔍 Data Gaps Identified (Opportunities for Improvement)
The following questions still received low ratings (<3) in the enhanced version, indicating missing data in the source text files:
*   *"How many teachers were prev students/alumni of JKKNIU?"* (Rated 1) - **FIXED:** Added alumni extraction logic.
*   *"Which teachers are graduates of Islamic University?"* (Rated 2) - **FIXED:** Added university extraction logic.
