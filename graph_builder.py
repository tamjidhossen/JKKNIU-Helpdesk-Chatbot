#!/usr/bin/env python3
"""
Knowledge Graph Builder for JKKNIU Helpdesk Chatbot
====================================================

Uses local Ollama LLM (gemma3:1b) to extract entities and relationships
from text documents, building a NetworkX graph for fast querying.

This replaces the hardcoded extraction in data_enricher.py with
dynamic LLM-based extraction.

Usage:
    from graph_builder import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder()
    builder.build_from_directory("Data/CSE_Teachers")
    builder.save("Data/knowledge_graph.gpickle")
"""

import os
import json
import glob
import pickle
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import networkx as nx
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

# Configuration
LOCAL_LLM_MODEL = "gemma3:1b"  # Lightweight, runs on CPU


@dataclass
class Entity:
    """Represents an extracted entity."""
    name: str
    entity_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    source_file: str = ""


@dataclass  
class Relationship:
    """Represents a relationship between entities."""
    source: str
    target: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)


class KnowledgeGraphBuilder:
    """Builds a knowledge graph from text documents using local LLM."""
    
    EXTRACTION_PROMPT = """Extract entities and relationships from this university faculty information.

Text:
{text}

Rules:
1. Entity types: Teacher, Department, University, Course, ResearchArea, Degree
2. Relationships: works_at, graduated_from, teaches, researches, authored, member_of
3. Publication counts: Only extract if specifically mentioned in the text.

Return ONLY valid JSON:
{{
  "entities": [
    {{"name": "...", "type": "Teacher", "properties": {{"designation": "...", "publications_count": 0}}}}
  ],
  "relationships": [
    {{"source": "...", "target": "...", "type": "graduated_from"}}
  ]
}}

Notice: Do not use the number 44 unless you actually find it in the text. If publications are listed but not counted, count them yourself and put the number in properties."""

    def __init__(self, model_name: str = LOCAL_LLM_MODEL, verbose: bool = False):
        """Initialize with local Ollama model."""
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.graph = nx.DiGraph()
        self.extraction_errors = []
        self.verbose = verbose
        
    def _extract_from_text(self, text: str, source_file: str = "") -> tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from text using local LLM."""
        entities = []
        relationships = []
        
        try:
            # Call local LLM
            response = self.llm.invoke(self.EXTRACTION_PROMPT.format(text=text))
            content = response.content.strip()
            
            if self.verbose:
                print(f"RAW LLM RESPONSE for {source_file}:\n{response.content}\n")
            
            # Parse JSON from response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            
            # Parse entities
            for e in data.get("entities", []):
                entities.append(Entity(
                    name=e.get("name", "").strip(),
                    entity_type=e.get("type", "Unknown"),
                    properties=e.get("properties", {}),
                    source_file=source_file
                ))
            
            # Parse relationships
            for r in data.get("relationships", []):
                relationships.append(Relationship(
                    source=r.get("source", "").strip(),
                    target=r.get("target", "").strip(),
                    relation_type=r.get("type", "related_to"),
                    properties=r.get("properties", {})
                ))
                
        except json.JSONDecodeError as e:
            self.extraction_errors.append(f"JSON parse error in {source_file}: {e}")
        except Exception as e:
            self.extraction_errors.append(f"Extraction error in {source_file}: {e}")
            
        return entities, relationships
    
    def _add_to_graph(self, entities: List[Entity], relationships: List[Relationship]):
        """Add extracted entities and relationships to the graph."""
        # Build name-to-node mapping from the ENTIRE graph plus current entities
        # This helps resolve relationships to entities in other files
        name_to_node = {data.get("name", "").lower(): node for node, data in self.graph.nodes(data=True)}
        
        # Add entities as nodes
        for entity in entities:
            if not entity.name:
                continue
            
            # Use normalized name as ID to avoid prefix/title duplicates
            node_id = self._normalize_name(entity.name)
            
            # If node exists, update its properties but keep existing ones
            if node_id in self.graph:
                # Update but don't overwrite source_file if it's from a primary file
                current_type = self.graph.nodes[node_id].get("entity_type")
                if current_type in ["Unknown", None] and entity.entity_type not in ["Unknown", None]:
                    self.graph.nodes[node_id]["entity_type"] = entity.entity_type
                
                # Merge properties
                for k, v in entity.properties.items():
                    if k not in ('name', 'entity_type', 'source_file', 'id'):
                        # Keep existing property if new value is 0 or None
                        if v or not self.graph.nodes[node_id].get(k):
                            self.graph.nodes[node_id][k] = v
            else:
                # Filter out reserved keys that would conflict with explicit arguments
                safe_properties = {k: v for k, v in entity.properties.items() 
                                 if k not in ('name', 'entity_type', 'source_file', 'id')}
                self.graph.add_node(
                    node_id,
                    name=entity.name, # Keep original name for display
                    entity_type=entity.entity_type,
                    source_file=entity.source_file,
                    **safe_properties
                )
            
            # Map name forms for fuzzy matching
            name_to_node[entity.name.lower()] = node_id
            name_to_node[node_id] = node_id # Normalized form maps to itself
        
        # Add relationships as edges with fuzzy matching
        for rel in relationships:
            if not rel.source or not rel.target:
                continue
            
            # Find source node (try exact, then fuzzy)
            source_node = self._find_node(rel.source, name_to_node)
            target_node = self._find_node(rel.target, name_to_node)
            
            if source_node and target_node:
                self.graph.add_edge(
                    source_node,
                    target_node,
                    relation_type=rel.relation_type,
                    **rel.properties
                )
    
    def _normalize_name(self, name: str) -> str:
        """Normalize a name by removing titles and extra spaces."""
        n = name.lower().strip()
        # Remove common titles and prefixes
        titles = ["prof. dr.", "professor dr.", "prof.", "dr.", "mr.", "mrs.", "ms.", "md.", 
                  "m. phil", "ph.d.", "phd", "assistant professor", "associate professor"]
        for title in titles:
            n = n.replace(title, "")
        
        # Remove dots and extra spaces
        n = n.replace(".", " ")
        n = " ".join(n.split())
        return n

    def _find_node(self, name: str, name_to_node: Dict[str, str]) -> Optional[str]:
        """Find a node by name with fuzzy matching."""
        name_lower = name.lower().strip()
        name_norm = self._normalize_name(name)
        
        # 1. Exact match on raw name
        if name_lower in name_to_node:
            return name_to_node[name_lower]
            
        # 2. Match on normalized name
        if name_norm in name_to_node:
            return name_to_node[name_norm]
        
        # 3. Partial match (name is substring of node name or vice versa)
        for node_name_key, node_id in name_to_node.items():
            # Check if the normalized input name is a substring of a normalized key in the map
            if name_norm and name_norm in node_name_key:
                return node_id
            # Check if a normalized key in the map is a substring of the normalized input name
            if node_name_key and node_name_key in name_norm:
                return node_id
        
        # 4. Check existing graph nodes directly by normalized name
        for node, data in self.graph.nodes(data=True):
            node_original_name = data.get("name", "")
            node_norm = self._normalize_name(node_original_name)
            if name_norm == node_norm or (name_norm and name_norm in node_norm) or (node_norm and node_norm in name_norm):
                return node
        
        return None
    
    def build_from_file(self, file_path: str) -> int:
        """Build graph from a single file. Returns number of entities extracted."""
        if not os.path.exists(file_path):
            return 0
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        filename = os.path.basename(file_path)
        entities, relationships = self._extract_from_text(content, filename)
        self._add_to_graph(entities, relationships)
        
        return len(entities)
    
    def build_from_directory(self, directory: str, pattern: str = "*.txt") -> Dict[str, int]:
        """Build graph from all matching files in directory."""
        results = {}
        files = sorted(glob.glob(os.path.join(directory, pattern)))
        
        print(f"📊 Processing {len(files)} files from {directory}...")
        
        for i, file_path in enumerate(files, 1):
            filename = os.path.basename(file_path)
            print(f"  [{i}/{len(files)}] Extracting from {filename}...", end=" ", flush=True)
            
            entity_count = self.build_from_file(file_path)
            results[filename] = entity_count
            print(f"✓ ({entity_count} entities)")
        
        return results
    
    def save(self, output_path: str):
        """Save the graph to a pickle file."""
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            pickle.dump(self.graph, f)
        print(f"💾 Graph saved to {output_path}")
        
    @classmethod
    def load(cls, graph_path: str) -> nx.DiGraph:
        """Load a previously saved graph."""
        with open(graph_path, "rb") as f:
            return pickle.load(f)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the current graph."""
        entity_types = {}
        for node, data in self.graph.nodes(data=True):
            t = data.get("entity_type", "Unknown")
            entity_types[t] = entity_types.get(t, 0) + 1
        
        relation_types = {}
        for _, _, data in self.graph.edges(data=True):
            t = data.get("relation_type", "unknown")
            relation_types[t] = relation_types.get(t, 0) + 1
            
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "entity_types": entity_types,
            "relation_types": relation_types,
            "extraction_errors": len(self.extraction_errors),
        }
    
    def query_by_type(self, entity_type: str) -> List[Dict]:
        """Query all entities of a specific type."""
        results = []
        for node, data in self.graph.nodes(data=True):
            if data.get("entity_type") == entity_type:
                results.append({"id": node, **data})
        return results
    
    def query_relationships(self, entity_name: str) -> List[Dict]:
        """Get all relationships for an entity."""
        results = []
        # Find matching nodes
        matching_nodes = [n for n in self.graph.nodes if entity_name.lower() in n.lower()]
        
        for node in matching_nodes:
            # Outgoing edges
            for _, target, data in self.graph.out_edges(node, data=True):
                results.append({
                    "source": node,
                    "target": target,
                    "relation": data.get("relation_type")
                })
            # Incoming edges
            for source, _, data in self.graph.in_edges(node, data=True):
                results.append({
                    "source": source,
                    "target": node,
                    "relation": data.get("relation_type")
                })
        return results
    
    def find_by_property(self, property_name: str, property_value: Any = None) -> List[Dict]:
        """Find entities with a specific property."""
        results = []
        for node, data in self.graph.nodes(data=True):
            if property_name in data:
                if property_value is None or data[property_name] == property_value:
                    results.append({"id": node, **data})
        return results


if __name__ == "__main__":
    # Quick test
    print("Testing KnowledgeGraphBuilder with gemma3:1b...")
    builder = KnowledgeGraphBuilder()
    
    # Test with a sample
    test_text = """
    Dr. A. H. M. Kamal - Professor, Department of Computer Science and Engineering, JKKNIU.
    Education: PhD from BUET, M.Sc from UPC Barcelona.
    Research: Medical Imaging, Information Security.
    Publications: 44 research papers.
    """
    
    entities, relationships = builder._extract_from_text(test_text, "test.txt")
    print(f"\nExtracted {len(entities)} entities and {len(relationships)} relationships")
    for e in entities:
        print(f"  - {e.entity_type}: {e.name}")
