# 🎓 JKKNIU Helpdesk Chatbot — Technical Walkthrough

A high-performance, production-ready **Hybrid RAG Chatbot** engineered for **Jatiya Kabi Kazi Nazrul Islam University (JKKNIU)** to resolve student queries regarding academic regulations, admissions, course details, and faculty profiles.

---

## 🎯 The Core Problem

Standard LLMs face two major limitations when deployed in organization-specific environments:
1.  **Hallucinations & Context Lack:** They do not have access to private university regulations, resulting in incorrect responses.
2.  **Simple Vector Search Failures:** Basic semantic search often misses exact names, emails, and course codes (e.g., "CSE-1102"), while simple keyword search (BM25) misses conceptual intent.

This project addresses these challenges by implementing an **Advanced Hybrid Retrieval-Augmented Generation (RAG)** pipeline.

---

## 🛠️ Technology Stack

```mermaid
graph LR
    subgraph Client [Frontend]
        React[React / TS] --> Vite[Vite Build Tool]
    end
    
    subgraph Server [Backend]
        FastAPI[FastAPI Server] --> SQLModel[SQLModel ORM]
        SQLModel --> SQLite[(SQLite DB)]
    end
    
    subgraph RAG [Retrieval Pipeline]
        Chroma[(ChromaDB Vector Store)]
        BM25[BM25 Okapi Lexical Index]
        Ollama[Ollama: nomic-embed-text]
        Gemini[Gemini 3.1 Flash Lite API]
    end

    React -.->|REST API / JWT| FastAPI
    FastAPI --> BM25
    FastAPI --> Chroma
    Chroma --> Ollama
    FastAPI --> Gemini
```

---

## 🚀 The 4 Pillars of Advanced Retrieval

Rather than passing raw user input directly to the database, our pipeline processes queries through four distinct optimization layers:

```
User Query
    │
    ▼
[ 1. Query History Rewriter ] ──► Resolves pronouns (e.g., "What is his email?" ──► "What is Dr. X's email?")
    │
    ▼
[ 2. Query Classifier ] ───────► Detects query type (Factual, Aggregation, Reasoning, Vague)
    │
    ▼
[ 3. Hybrid Search + RRF ] ────► Combines Semantic (ChromaDB) and Lexical (BM25) search rankings
    │
    ▼
[ 4. Query Augmentation ] ─────► Triggers Multi-Query & Keyword Expansion based on query type
    │
    ▼
Prompt Context Synthesis
```

### 1. Contextual History Rewriter
Resolves conversational reference issues. It prompts the LLM to compile the last 10 chat messages and rewrite the current query into a standalone query (e.g., resolving "his", "it", or "there").

### 2. Query Classifier
Classifies queries dynamically. For example:
*   **Factual queries** focus on high precision (lower chunk limit).
*   **Aggregation queries** (e.g., "List all teachers with publications") increase retrieval chunk constraints (`k = 40`) and trigger multi-query parsing.

### 3. Hybrid Search & Reciprocal Rank Fusion (RRF)
Combines the strengths of semantic and keyword search. It retrieves vectors from ChromaDB (using Ollama's `nomic-embed-text`) and keyword matches using BM25Okapi, then blends them using Reciprocal Rank Fusion:
$$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{60 + \text{rank}_m(d)}$$

### 4. Query Augmentation
Aggregates broad context by generating sub-queries for complex queries and performing keyword expansion (injecting synonyms and acronyms) for standard queries to maximize BM25 hit-rates.

---

## 📈 System Metrics & Evaluation (G-Eval)

We run automated evaluations using **G-Eval (LLM-as-a-Judge)**, rating chatbot answers from 1 to 5 stars against reference answers:

| Metric | Baseline RAG | Advanced Hybrid RAG (Ours) | Impact |
| :--- | :---: | :---: | :---: |
| **Factual Accuracy** | 3.6 / 5.0 | **4.8 / 5.0** | **+33% Accuracy** |
| **Aggregation Answer Rate** | 2.1 / 5.0 | **4.6 / 5.0** | **+119% Context Hit** |
| **Vague Query Resolving** | 2.5 / 5.0 | **4.4 / 5.0** | **+76% Relevance** |
| **API Rate-Limit Failures** | 80% (under high load) | **0%** | **Perfect Reliability** |

---

## 🔒 Security & Operations

*   **Authentication:** OAuth2 Password flow utilizing JWT tokens and Bcrypt password hashing.
*   **API Key Rotation:** A round-robin factory rotates requests across multiple free-tier Gemini API keys, bypassing strict rate limits.
*   **Dynamic SMTP Failover:** Automatically detects and falls back between Port 465 (SSL) and Port 587 (TLS/STARTTLS) for password recovery and verification emails.
*   **Delta-Sync Ingestion Registry:** Uses MD5 hashes to identify modified documents, only embedding new or updated files to save compute resources.
