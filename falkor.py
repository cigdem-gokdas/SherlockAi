"""
DetectiveDatabase Module
Handles interactions with FalkorDB to store and retrieve game state data
(Suspects, Locations, Clues, and Relationships) for SherlockAI.
"""
import os
from dotenv import load_dotenv
from falkordb import FalkorDB

# Load environment variables
load_dotenv()


class DetectiveDatabase:
    """
    Manages the Knowledge Graph for the detective game.
    """

    def __init__(self):
        """Initialize connection to FalkorDB."""
        self.host = "localhost"
        self.port = 6379
        self.client = None
        self.graph = None
        self.is_active = False
        self._connect()

    def _connect(self):
        """Establish connection to the FalkorDB Docker container."""
        try:
            self.client = FalkorDB(host=self.host, port=self.port)
            # We create a specific graph named 'SherlockCase'
            self.graph = self.client.select_graph("SherlockCase")
            self.is_active = True
            print("✔ Connected to FalkorDB (Graph: SherlockCase)")
        except Exception as e:
            print(f"✘ FalkorDB Connection Failed: {e}")
            print(
                "  Make sure Docker is running: 'docker run -p 6379:6379 falkordb/falkordb'")
            self.is_active = False

    def reset_game(self):
        """
        Clears the entire graph to start a new game/scenario.
        """
        if not self.is_active:
            return

        try:
            # Cypher query to delete all nodes and relationships
            self.graph.query("MATCH (n) DETACH DELETE n")
            print("🧹 Game board cleared. Ready for a new mystery.")
        except Exception as e:
            print(f"Error resetting game: {e}")

    def add_person(self, name: str, role: str, trait: str):
        """
        Adds a person (Suspect, Victim, or Killer) to the graph.
        """
        if name:
            name = name.replace("'", "\\'")
        if trait:
            trait = trait.replace("'", "\\'")
        if not self.is_active:
            return

        query = f"""
        MERGE (p:Person {{name: '{name}'}})
        SET p.role = '{role}',
            p.trait = '{trait}'
        RETURN p
        """
        self.graph.query(query)
        print(f"👤 Added Person: {name} ({role})")

    def add_location_record(self, person_name: str, name: str, time: str):
        """
        Records a character's location at a specific time (Alibi).
        Creates: (Person)-[:SEEN_AT {time: '...'}]->(Location)
        """
        if name:
            name = name.replace("'", "\\'")
        if trait:
            trait = trait.replace("'", "\\'")
        if not self.is_active:
            return

        query = f"""
        MATCH (p:Person {{name: '{person_name}'}})
        MERGE (l:Location {{name: '{name}'}})
        MERGE (p)-[:SEEN_AT {{time: '{time}'}}]->(l)
        """
        self.graph.query(query)

    def add_relationship(self, person1: str, person2: str, relation_type: str, detail: str):
        """
        Adds a social relationship between two characters.
        """
        if name:
            name = name.replace("'", "\\'")
        if trait:
            trait = trait.replace("'", "\\'")
        if not self.is_active:
            return

        # relation_type should be uppercase, e.g., 'HATES', 'LOVES', 'KNOWS'
        rel_type = relation_type.upper().replace(" ", "_")

        query = f"""
        MATCH (p1:Person {{name: '{person1}'}})
        MATCH (p2:Person {{name: '{person2}'}})
        MERGE (p1)-[r:{rel_type} {{detail: '{detail}'}}]->(p2)
        """
        self.graph.query(query)

    def add_clue(self, item_name: str, location_name: str, description: str):
        """
        Places a physical clue in a location.
        Creates: (Item)-[:FOUND_IN]->(Location)
        """
        if description:
            description = description.replace("'", "\\'")
        if location_name:
            location_name = location_name.replace("'", "\\'")
        if item_name:
            item_name = item_name.replace("'", "\\'")
        if not self.is_active:
            return

        query = f"""
        MERGE (i:Item {{name: '{item_name}', description: '{description}'}})
        MERGE (l:Location {{name: '{location_name}'}})
        MERGE (i)-[:FOUND_IN]->(l)
        """
        self.graph.query(query)
        print(f"🔍 Clue hidden: {item_name} in {location_name}")


# Create a global instance
db = DetectiveDatabase()
