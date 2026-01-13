import pickle
import networkx as nx

with open("Data/knowledge_graph.gpickle", "rb") as f:
    graph = pickle.load(f)

for name in ["A. H. M. Kamal", "Md. Mijanur Rahman"]:
    print(f"\n--- {name} ---")
    # Fuzzy find node
    node_id = None
    for n, d in graph.nodes(data=True):
        if name.lower() in d.get("name", "").lower():
            node_id = n
            print(f"Node: {n}")
            print(f"Data: {d}")
            
            # Count relations
            out_edges = graph.out_edges(n, data=True)
            pub_rels = [e for e in out_edges if "pub" in e[2].get("relation_type", "").lower()]
            print(f"Publication relations: {len(pub_rels)}")
            for e in pub_rels[:3]:
                print(f"  -> {e[1]}")
            if len(pub_rels) > 3:
                print("  ...")
