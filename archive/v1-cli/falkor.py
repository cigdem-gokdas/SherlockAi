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
            self.graph = self.client.select_graph("SherlockCase")
            self.is_active = True
            print("Connected to FalkorDB (Graph: SherlockCase)")
        except Exception as e:
            print(f"FalkorDB Connection Failed: {e}")
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
            self.graph.query("MATCH (n) DETACH DELETE n")
            print(" Game board cleared. Ready for a new mystery.")
        except Exception as e:
            print(f"Error resetting game: {e}")

    def add_person(self, name: str, role: str, trait: str):
        """
        Adds a person (Suspect, Victim, or Killer) to the graph.
        """
        if not self.is_active:
            return

        # Parametreli sorgu kullan
        query = """
        MERGE (p:Person {name: $name})
        SET p.role = $role,
            p.trait = $trait
        RETURN p
        """
        params = {'name': name, 'role': role, 'trait': trait}
        self.graph.query(query, params)

    def add_location_record(self, person_name: str, name: str, time: str):
        """
        Records a character's location at a specific time (Alibi).
        Creates: (Person)-[:SEEN_AT {time: '...'}]->(Location)
        """
        if not self.is_active:
            return

        query = """
        MATCH (p:Person {name: $person_name})
        MERGE (l:Location {name: $location_name})
        MERGE (p)-[:SEEN_AT {time: $time}]->(l)
        """
        params = {'person_name': person_name, 'location_name': name, 'time': time}
        self.graph.query(query, params)

    def add_relationship(self, person1: str, person2: str, relation_type: str, detail: str):
        """
        Adds a social relationship between two characters.
        """
        if not self.is_active:
            return

        rel_type = relation_type.upper().replace(" ", "_")

        query = f"""
        MATCH (p1:Person {{name: $person1}})
        MATCH (p2:Person {{name: $person2}})
        MERGE (p1)-[r:{rel_type} {{detail: $detail}}]->(p2)
        """
        params = {'person1': person1, 'person2': person2, 'detail': detail}
        self.graph.query(query, params)

    def add_clue(self, item_name: str, location_name: str, description: str):
        """
        Places a physical clue in a location.
        Creates: (Item)-[:FOUND_IN]->(Location)
        """
        if not self.is_active:
            return

        query = """
        MERGE (i:Item {name: $item_name, description: $description})
        MERGE (l:Location {name: $location_name})
        MERGE (i)-[:FOUND_IN]->(l)
        """
        params = {'item_name': item_name, 'location_name': location_name, 'description': description}
        self.graph.query(query, params)


# Create a global instance
db = DetectiveDatabase()