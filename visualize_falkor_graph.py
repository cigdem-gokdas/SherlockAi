"""
Graph visualization script for FalkorDB movie relationships.

Connects to FalkorDB instance, queries graph structure,
builds a NetworkX graph, and saves visualization as PNG.
Adheres to Pylint standards.
"""

import redis
import networkx as nx
import matplotlib.pyplot as plt
from redis.commands.graph import Graph


# Configuration Constants
HOST = 'localhost'
PORT = 6379
GRAPH_KEY = 'IMDB_Graph'
OUTPUT_FILENAME = "project_graph_visualization.png"


def visualize_graph_data():
    """
    Connect to FalkorDB, fetch graph data, and visualize relationships.

    Queries all nodes and their relationships from FalkorDB,
    builds a NetworkX directed graph, and saves PNG visualization.
    """
    try:
        # 1. Database Connection
        redis_client = redis.Redis(host=HOST, port=PORT, decode_responses=True)
        graph_db = Graph(redis_client, GRAPH_KEY)

        # 2. Fetch Data from Graph
        print(
            f"Connecting to FalkorDB and fetching data from '{GRAPH_KEY}'...")

        # Cypher query: retrieve all nodes and their relationships
        query = "MATCH (s)-[r]->(d) RETURN s, r, d"

        # Execute query
        result = graph_db.query(query)

    except ConnectionError as conn_error:
        print(
            f"Connection error: Could not connect to FalkorDB at {HOST}:{PORT}")
        print(f"Details: {conn_error}")
        print("Ensure FalkorDB is running: docker run -p 6379:6379 falkordb/falkordb")
        return

    except Exception as error:  # pylint: disable=broad-exception-caught
        print(f"Error during database query: {error}")
        return

    # 3. Handle Empty Results
    if not result.result_set:
        print("⚠️  No relationships found in graph!")
        print(
            "Ensure falkor.py has successfully inserted Movie/Series data."
        )
        return

    print(f"✓ Successfully fetched {len(result.result_set)} relationships.")

    # 4. Build NetworkX Graph
    networkx_graph = nx.DiGraph()

    for record in result.result_set:
        source_node = record[0]
        relationship = record[1]
        dest_node = record[2]

        # Extract relationship type
        relationship_type = relationship.relation

        # Extract node properties
        src_props = source_node.properties
        dst_props = dest_node.properties

        # Use title/name as label, fallback to ID
        src_label = src_props.get(
            'title', src_props.get('name', f"Node_{source_node.id}")
        )
        dst_label = dst_props.get(
            'title', dst_props.get('name', f"Node_{dest_node.id}")
        )

        # Add edge with relationship type as label
        networkx_graph.add_edge(
            src_label, dst_label, label=relationship_type
        )

    # 5. Visualize and Save
    print("Generating graph visualization...")

    plt.figure(figsize=(14, 10))

    # Use spring layout for better visualization
    pos = nx.spring_layout(networkx_graph, k=2, iterations=50, seed=42)

    # Draw nodes
    nx.draw_networkx_nodes(
        networkx_graph, pos,
        node_color='lightblue',
        node_size=3000,
        alpha=0.9
    )

    # Draw edges
    nx.draw_networkx_edges(
        networkx_graph, pos,
        edge_color='gray',
        arrows=True,
        arrowsize=20,
        arrowstyle='->',
        width=2,
        alpha=0.6
    )

    # Draw labels
    nx.draw_networkx_labels(
        networkx_graph, pos,
        font_size=9,
        font_weight='bold'
    )

    # Draw edge labels (relationship types)
    edge_labels = nx.get_edge_attributes(networkx_graph, 'label')
    nx.draw_networkx_edge_labels(
        networkx_graph, pos,
        edge_labels,
        font_size=8
    )

    # Formatting
    plt.title(
        f"FalkorDB Movie Graph Visualization\n({len(networkx_graph.nodes())} "
        f"nodes, {len(networkx_graph.edges())} relationships)",
        fontsize=16,
        fontweight='bold'
    )
    plt.axis('off')
    plt.tight_layout()

    # Save to file
    try:
        plt.savefig(OUTPUT_FILENAME, dpi=300, bbox_inches='tight')
        print(f"✓ Graph visualization saved to '{OUTPUT_FILENAME}'")
    except IOError as io_error:
        print(f"Error saving file: {io_error}")
        return

    # Display graph info
    print("\n--- Graph Statistics ---")
    print(f"Total Nodes: {len(networkx_graph.nodes())}")
    print(f"Total Relationships: {len(networkx_graph.edges())}")
    print(f"Graph Density: {nx.density(networkx_graph):.4f}")

    if len(networkx_graph.nodes()) > 0:
        avg_degree = sum(dict(networkx_graph.degree()).values()
                         ) / len(networkx_graph.nodes())
        print(f"Average Degree: {avg_degree:.2f}")
    plt.show()


if __name__ == "__main__":
    visualize_graph_data()
