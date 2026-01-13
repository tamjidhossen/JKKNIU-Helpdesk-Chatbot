#!/usr/bin/env python3
"""
Build Knowledge Graph CLI
=========================

One-time script to build the knowledge graph from text data files.
Uses local Ollama LLM (gemma3:1b) for entity extraction.

Usage:
    python build_graph.py                    # Build from all data
    python build_graph.py --teachers-only    # Build from teacher data only
    python build_graph.py --test             # Quick test with one file

Output:
    - Data/knowledge_graph.gpickle   (serialized NetworkX graph)
    - Data/graph_stats.json          (statistics for debugging)
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from graph_builder import KnowledgeGraphBuilder
from config import DATA_DIR


def main():
    parser = argparse.ArgumentParser(description="Build knowledge graph from JKKNIU data")
    parser.add_argument("--teachers-only", action="store_true", help="Only process teacher files")
    parser.add_argument("--test", action="store_true", help="Run a quick test with one file")
    parser.add_argument("--incremental", action="store_true", help="Load existing graph and add to it")
    parser.add_argument("--output", default="Data/knowledge_graph.gpickle", help="Output path")
    args = parser.parse_args()
    
    print("🚀 JKKNIU Knowledge Graph Builder")
    print("=" * 50)
    print(f"Using local LLM: gemma3:1b (via Ollama)")
    print()
    
    builder = KnowledgeGraphBuilder()
    
    if args.test:
        # Quick test with single file
        print("🧪 Running quick test with single file...")
        test_file = os.path.join(DATA_DIR, "CSE_Teachers", "t1.txt")
        if os.path.exists(test_file):
            count = builder.build_from_file(test_file)
            print(f"✓ Extracted {count} entities from t1.txt")
            stats = builder.get_stats()
            print(f"\nGraph stats: {json.dumps(stats, indent=2)}")
        else:
            print(f"❌ Test file not found: {test_file}")
            return 1
    else:
        # Build from directories
        directories = []
        
        if args.teachers_only:
            directories = [os.path.join(DATA_DIR, "CSE_Teachers")]
        else:
            # All data directories
            directories = [
                os.path.join(DATA_DIR, "CSE_Teachers"),
                os.path.join(DATA_DIR, "New_Data", "processed"),
            ]
        
        total_entities = 0
        for directory in directories:
            if os.path.exists(directory):
                print(f"\n📁 Processing: {directory}")
                results = builder.build_from_directory(directory)
                total_entities += sum(results.values())
            else:
                print(f"⚠️  Directory not found: {directory}")
        
        print(f"\n{'=' * 50}")
        print(f"✅ Total entities extracted: {total_entities}")
        
        # Show stats
        stats = builder.get_stats()
        print(f"\n📊 Graph Statistics:")
        print(f"   Nodes: {stats['total_nodes']}")
        print(f"   Edges: {stats['total_edges']}")
        print(f"   Entity types: {stats['entity_types']}")
        print(f"   Relation types: {stats['relation_types']}")
        
        if stats['extraction_errors'] > 0:
            print(f"\n⚠️  Extraction errors: {stats['extraction_errors']}")
            for error in builder.extraction_errors[:5]:
                print(f"     - {error}")
        
        # Save graph
        builder.save(args.output)
        
        # Save stats for debugging
        stats_path = args.output.replace(".gpickle", "_stats.json")
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"📄 Stats saved to {stats_path}")
    
    print("\n🎉 Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
