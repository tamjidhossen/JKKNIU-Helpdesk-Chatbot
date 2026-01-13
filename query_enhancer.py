#!/usr/bin/env python3
"""
Query Enhancer for JKKNIU Helpdesk Chatbot
==========================================

Implements advanced query processing techniques:
1. Query Classification - Route to appropriate retrieval strategy
2. HyDE (Hypothetical Document Embeddings) - Generate JKKNIU-format hypothetical docs
3. Multi-Query Generation - Break complex queries into sub-queries

Usage:
    from query_enhancer import EnhancedRetriever
    retriever = EnhancedRetriever()
    results = retriever.retrieve("Which teacher has most publications?")
"""

import os
import re
from typing import List, Tuple, Optional
from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from config import (
    EMBEDDING_MODEL, VECTOR_DB_PATH, COLLECTION_NAME,
    GEMINI_MODEL, RETRIEVAL_K, UNIVERSITY_NAME
)
from api_keys import get_next_api_key


class QueryClassifier:
    """Classifies queries to determine the best retrieval strategy."""
    
    QUERY_PATTERNS = {
        "aggregation": [
            r"(most|highest|lowest|total|how many|count|list all)",
            r"(compare|versus|vs|difference between)",
            r"(rank|ranking|top \d+)",
        ],
        "factual": [
            r"(who is|what is|when|where|which)",
            r"(email|phone|contact|address)",
            r"(course code|CSE \d+|EEE \d+)",
        ],
        "reasoning": [
            r"(can i|can a|is it possible|eligible|allowed)",
            r"(what happens|if i|what if)",
            r"(recommend|should i|suitable for)",
        ],
        "vague": [
            r"^(tell me|help|info|about)$",
            r"^.{1,15}$",  # Very short queries
        ]
    }
    
    @classmethod
    def classify(cls, query: str) -> str:
        """Classify the query type."""
        query_lower = query.lower()
        
        for query_type, patterns in cls.QUERY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return query_type
        
        return "factual"  # Default
    
    @classmethod
    def get_retrieval_k(cls, query_type: str) -> int:
        """Get optimal k value based on query type."""
        k_values = {
            "aggregation": 30,  # Need more docs for aggregation
            "factual": 10,      # Fewer docs needed
            "reasoning": 15,    # Moderate amount
            "vague": 20,        # More for context
        }
        return k_values.get(query_type, RETRIEVAL_K)


class HyDEGenerator:
    """Generates hypothetical documents in JKKNIU data format."""
    
    HYDE_PROMPT = """You are generating a hypothetical document snippet that would answer the following question about JKKNIU university.

IMPORTANT: Format your response EXACTLY like JKKNIU data documents:
- For teacher queries: "Professor Dr. Name - Designation, Department of X, Jatiya Kabi Kazi Nazrul Islam University\\nPublications: ..."
- For admission queries: "Department Admission at JKKNIU 2025-2026\\nFor the 2025-2026 academic session..."
- For course queries: "CSE XXX Course Name (X.0 credits, Pre-requisite: ...)..."

Generate a realistic document snippet (2-3 sentences) that would contain the answer:

Question: {question}

Document snippet:"""

    def __init__(self):
        pass  # Model created per-call with rotating API key
    
    def _get_model(self):
        """Get model with next API key."""
        api_key = get_next_api_key()
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key)
    
    def generate(self, question: str) -> str:
        """Generate a hypothetical document for the question."""
        try:
            model = self._get_model()
            prompt = self.HYDE_PROMPT.format(question=question)
            response = model.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            print(f"HyDE generation failed: {e}")
            return question  # Fallback to original query


class MultiQueryGenerator:
    """Generates sub-queries for complex questions."""
    
    MULTI_QUERY_PROMPT = """Break down this complex question into 2-3 simpler sub-questions that together would help answer the original question.

Original question: {question}

Output only the sub-questions, one per line, without numbering or explanation:"""

    def __init__(self):
        pass  # Model created per-call with rotating API key
    
    def _get_model(self):
        """Get model with next API key."""
        api_key = get_next_api_key()
        return ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=api_key)
    
    def generate(self, question: str) -> List[str]:
        """Generate sub-queries for a complex question."""
        try:
            model = self._get_model()
            prompt = self.MULTI_QUERY_PROMPT.format(question=question)
            response = model.invoke(prompt)
            
            # Parse sub-queries
            sub_queries = [q.strip() for q in response.content.split("\n") if q.strip()]
            
            # Include original query
            return [question] + sub_queries[:2]  # Original + up to 2 sub-queries
        except Exception as e:
            print(f"Multi-query generation failed: {e}")
            return [question]


class HybridRetriever:
    """Combines semantic and keyword (BM25) search with RRF fusion."""
    
    def __init__(self, vector_store: Chroma, embeddings: OllamaEmbeddings):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.bm25 = None
        self.documents = None
        self._init_bm25()
    
    def _init_bm25(self):
        """Initialize BM25 index from vector store documents."""
        try:
            # Get all documents from the collection
            collection = self.vector_store._collection
            results = collection.get(include=["documents", "metadatas"])
            
            if results and results.get("documents"):
                self.documents = [
                    Document(page_content=doc, metadata=meta or {})
                    for doc, meta in zip(results["documents"], results.get("metadatas", [{}] * len(results["documents"])))
                ]
                
                # Tokenize for BM25
                tokenized_docs = [doc.page_content.lower().split() for doc in self.documents]
                self.bm25 = BM25Okapi(tokenized_docs)
                print(f"BM25 initialized with {len(self.documents)} documents")
            else:
                print("Warning: No documents found for BM25 initialization")
        except Exception as e:
            print(f"BM25 initialization failed: {e}")
    
    def semantic_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform semantic (embedding) search."""
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return results
    
    def keyword_search(self, query: str, k: int) -> List[Tuple[Document, float]]:
        """Perform BM25 keyword search."""
        if not self.bm25 or not self.documents:
            return []
        
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top k indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        return [(self.documents[i], scores[i]) for i in top_indices if scores[i] > 0]
    
    def reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[Document, float]],
        keyword_results: List[Tuple[Document, float]],
        k: int = 60
    ) -> List[Document]:
        """Fuse results using Reciprocal Rank Fusion (RRF)."""
        doc_scores = {}
        
        # RRF formula: score = sum(1 / (k + rank))
        for rank, (doc, _) in enumerate(semantic_results):
            doc_id = doc.page_content[:100]  # Use content prefix as ID
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0}
            doc_scores[doc_id]["score"] += 1 / (k + rank + 1)
        
        for rank, (doc, _) in enumerate(keyword_results):
            doc_id = doc.page_content[:100]
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {"doc": doc, "score": 0}
            doc_scores[doc_id]["score"] += 1 / (k + rank + 1)
        
        # Sort by fused score
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_docs]
    
    def retrieve(self, query: str, k: int) -> List[Document]:
        """Retrieve documents using hybrid search."""
        semantic_results = self.semantic_search(query, k=k)
        keyword_results = self.keyword_search(query, k=k)
        
        fused_results = self.reciprocal_rank_fusion(semantic_results, keyword_results)
        return fused_results[:k]


class EnhancedRetriever:
    """Main enhanced retriever combining all techniques."""
    
    def __init__(self, use_hyde: bool = True, use_multi_query: bool = True, use_hybrid: bool = True):
        self.embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        self.vector_store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=VECTOR_DB_PATH,
            embedding_function=self.embeddings
        )
        
        self.use_hyde = use_hyde
        self.use_multi_query = use_multi_query
        self.use_hybrid = use_hybrid
        
        self.hyde_generator = HyDEGenerator() if use_hyde else None
        self.multi_query_generator = MultiQueryGenerator() if use_multi_query else None
        self.hybrid_retriever = HybridRetriever(self.vector_store, self.embeddings) if use_hybrid else None
    
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        """Retrieve documents with enhanced techniques."""
        # Classify query
        query_type = QueryClassifier.classify(query)
        retrieval_k = k or QueryClassifier.get_retrieval_k(query_type)
        
        all_docs = []
        seen_content = set()
        
        # Determine which enhancement to use based on query type
        use_hyde_for_query = self.use_hyde and query_type in ["vague", "reasoning"]
        use_multi_query_for_query = self.use_multi_query and query_type == "aggregation"
        
        queries_to_run = [query]
        
        # Generate sub-queries for aggregation
        if use_multi_query_for_query and self.multi_query_generator:
            queries_to_run = self.multi_query_generator.generate(query)
        
        for q in queries_to_run:
            search_query = q
            
            # Apply HyDE for vague/reasoning queries
            if use_hyde_for_query and self.hyde_generator and q == query:
                search_query = self.hyde_generator.generate(q)
            
            # Retrieve with hybrid or plain semantic
            if self.use_hybrid and self.hybrid_retriever:
                docs = self.hybrid_retriever.retrieve(search_query, k=retrieval_k)
            else:
                docs = self.vector_store.similarity_search(search_query, k=retrieval_k)
            
            # Deduplicate
            for doc in docs:
                content_hash = hash(doc.page_content[:200])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    all_docs.append(doc)
        
        return all_docs[:retrieval_k]
    
    def invoke(self, query: str) -> List[Document]:
        """LangChain-compatible invoke method."""
        return self.retrieve(query)


# Create a default enhanced retriever for import
def get_enhanced_retriever(
    use_hyde: bool = True,
    use_multi_query: bool = True,
    use_hybrid: bool = True
) -> EnhancedRetriever:
    """Factory function to create an enhanced retriever."""
    return EnhancedRetriever(
        use_hyde=use_hyde,
        use_multi_query=use_multi_query,
        use_hybrid=use_hybrid
    )


if __name__ == "__main__":
    # Test the enhanced retriever
    print("Testing Enhanced Retriever...\n")
    
    retriever = EnhancedRetriever()
    
    test_queries = [
        ("Which CSE teacher has the most publications?", "aggregation"),
        ("Can a humanities student join CSE?", "reasoning"),
        ("What is CSE 425?", "factual"),
        ("Tell me about admission", "vague"),
    ]
    
    for query, expected_type in test_queries:
        print(f"Query: {query}")
        print(f"Expected type: {expected_type}")
        print(f"Classified as: {QueryClassifier.classify(query)}")
        
        docs = retriever.retrieve(query, k=3)
        print(f"Retrieved {len(docs)} docs:")
        for doc in docs[:2]:
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"  - {preview}...")
        print()
