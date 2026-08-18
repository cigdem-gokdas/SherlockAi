"""
Graph visualization script for SherlockAI (Updated for FalkorDB Client).
Connects to FalkorDB, queries the game graph, and saves a PNG image.
"""
import networkx as nx
import matplotlib.pyplot as plt
from falkordb import FalkorDB

# Configuration
HOST = 'localhost'
PORT = 6379
GRAPH_KEY = 'SherlockCase'  # Updated graph name
OUTPUT_FILENAME = "project_graph_visualization.png"


def visualize_graph_data():
    """
    Fetches nodes/edges using FalkorDB client and plots them.
    """
    try:
        # 1. Connect using the modern FalkorDB client
        client = FalkorDB(host=HOST, port=PORT)
        graph_db = client.select_graph(GRAPH_KEY)

        print(f"Fetching data from graph: '{GRAPH_KEY}'...")

        # 2. Execute Query
        query = "MATCH (s)-[r]->(d) RETURN s, r, d"
        result = graph_db.query(query)

    except Exception as e:
        print(f"Error connecting or querying: {e}")
        return

    # 3. Build NetworkX Graph
    G = nx.DiGraph()

    # Check if result has data
    if not result.result_set:
        print("  Graph is empty! Run the game setup first.")
        return

    for record in result.result_set:
        source = record[0]
        relation = record[1]
        target = record[2]

        # Get properties safely
        # Person nodes usually have 'name', others might vary
        src_label = source.properties.get('name', str(source.id))
        dst_label = target.properties.get('name', str(target.id))
        rel_label = relation.relation  # Relationship type (e.g., HATES)

        G.add_edge(src_label, dst_label, label=rel_label)

    # 4. Draw Graph
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5, seed=42)

    # Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_size=2000,
                           node_color='lightblue', alpha=0.9)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

    # Draw Edges
    nx.draw_networkx_edges(G, pos, arrowstyle='->',
                           arrowsize=20, edge_color='gray')

    # Draw Edge Labels (Relationships)
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    plt.title("SherlockAI Knowledge Graph")
    plt.axis('off')

    try:
        plt.savefig(OUTPUT_FILENAME)
        print(f" Visualization saved to {OUTPUT_FILENAME}")
    except Exception as e:
        print(f"Could not save image: {e}")

    # Show on screen (optional, might require GUI backend)
    # plt.show()


if __name__ == "__main__":
    visualize_graph_data()
