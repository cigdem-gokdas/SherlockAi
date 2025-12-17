"""
SherlockAI Game Engine
Manages game flow, timer, evidence collection, and win conditions.
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from falkor import db
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

class DetectiveGame:
    """Main game controller for the detective mystery."""
    
    def __init__(self, time_limit_minutes: int = 30):
        self.time_limit = time_limit_minutes * 60  # Convert to seconds
        self.start_time = None
        self.game_active = False
        self.discovered_evidence = []
        self.visited_locations = []
        self.interviewed_people = []
        self.current_location = "Crime Scene"
        self.case_title = "Unknown Case"
        self.victim_name = "Unknown Victim"
        
        # Load RAG system
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
        
    def initialize_mystery(self, use_ai_generator: bool = True, mystery_data: dict = None):
        """
        Set up a new mystery case.
        
        Args:
            use_ai_generator: If True, generate story with AI. If False, use provided mystery_data
            mystery_data: Pre-generated mystery dict (from MysteryGenerator)
        """
        print("\n🔍 INITIALIZING NEW CASE...")
        
        if use_ai_generator and mystery_data:
            # Use provided AI-generated mystery
            case = mystery_data['case']
            print(f"✅ Mystery initialized: '{case['title']}'")
            print(f"🎭 Victim: {case['victim']['name']} found dead in {case['victim']['killed_where']} at {case['victim']['killed_when']}")
            self.case_title = case['title']
            self.victim_name = case['victim']['name']
        else:
            # Fallback to manual case
            db.reset_game()
            
            # Example case: Manor Murder
            db.add_person("Lord Henry", "Victim", "Wealthy nobleman")
            db.add_person("Lady Margaret", "Suspect", "Wife, stands to inherit")
            db.add_person("James Butler", "Suspect", "Butler, recently fired")
            db.add_person("Dr. Watson", "Suspect", "Family physician")
            db.add_person("Alice Maid", "Suspect", "Maid, unpaid wages")
            db.add_person("Thomas Gardener", "Killer", "Gardener, secret affair")
            
            db.add_location_record("Lady Margaret", "Bedroom", "10:00 PM")
            db.add_location_record("James Butler", "Kitchen", "10:15 PM")
            db.add_location_record("Dr. Watson", "Study", "9:45 PM")
            db.add_location_record("Alice Maid", "Garden", "10:30 PM")
            db.add_location_record("Thomas Gardener", "Garden", "10:00 PM")
            db.add_location_record("Lord Henry", "Garden", "10:00 PM")
            
            db.add_relationship("Lady Margaret", "Lord Henry", "RESENTS", 
                              "Angry about affair with maid")
            db.add_relationship("James Butler", "Lord Henry", "HATES", 
                              "Fired without severance pay")
            db.add_relationship("Thomas Gardener", "Lady Margaret", "LOVES", 
                              "Secret romantic affair")
            db.add_relationship("Alice Maid", "Lord Henry", "FEARS", 
                              "Witnessed something suspicious")
            
            db.add_clue("Bloody Knife", "Garden", "Kitchen knife with fingerprints")
            db.add_clue("Love Letter", "Study", "Letter from Lady Margaret to unknown lover")
            db.add_clue("Muddy Boots", "Kitchen", "Gardener's boots with fresh soil")
            db.add_clue("Torn Fabric", "Garden", "Blue fabric matching gardener's shirt")
            db.add_clue("Poison Bottle", "Library", "Empty arsenic bottle (red herring)")
            
            print("✅ Mystery initialized: 'The Manor Murder'")
            print(f"🎭 Victim: Lord Henry found dead in the Garden at 10:00 PM")
            self.case_title = "The Manor Murder"
            self.victim_name = "Lord Henry"
        
    def start_game(self):
        """Begin the timed investigation."""
        self.start_time = time.time()
        self.game_active = True
        self.current_location = "Crime Scene"
        print(f"\n⏰ Timer started! You have {self.time_limit // 60} minutes.")
        print("🔎 Investigation begins...\n")
        
    def get_remaining_time(self) -> int:
        """Returns seconds remaining."""
        if not self.start_time:
            return self.time_limit
        elapsed = time.time() - self.start_time
        return max(0, int(self.time_limit - elapsed))
    
    def is_time_up(self) -> bool:
        """Check if time has expired."""
        return self.get_remaining_time() <= 0
    
    def search_location(self, location_name: str) -> List[Dict]:
        """Search a location for clues using FalkorDB."""
        if not db.is_active:
            return []
        
        query = f"""
        MATCH (i:Item)-[:FOUND_IN]->(l:Location {{name: '{location_name}'}})
        RETURN i.name AS item, i.description AS description
        """
        result = db.graph.query(query)
        
        found_items = []
        for record in result.result_set:
            item_data = {
                "name": record[0],
                "description": record[1],
                "location": location_name
            }
            found_items.append(item_data)
            
            if item_data not in self.discovered_evidence:
                self.discovered_evidence.append(item_data)
                print(f"🔍 NEW EVIDENCE: {item_data['name']}")
        
        if location_name not in self.visited_locations:
            self.visited_locations.append(location_name)
            
        return found_items
    
    def query_witnesses(self, location: str, time: str) -> List[Dict]:
        """Find who was at a location at a specific time."""
        if not db.is_active:
            return []
        
        query = f"""
        MATCH (p:Person)-[r:SEEN_AT]->(l:Location {{name: '{location}'}})
        WHERE r.time = '{time}'
        RETURN p.name AS person, p.role AS role, r.time AS time
        """
        result = db.graph.query(query)
        
        witnesses = []
        for record in result.result_set:
            person_name = record[0]
            witnesses.append({
                "name": person_name,
                "role": record[1],
                "time": record[2]
            })
            
            # Track interviewed people
            if person_name not in self.interviewed_people:
                self.interviewed_people.append(person_name)
        
        return witnesses
    
    def mark_as_interviewed(self, person_name: str):
        """Mark a person as interviewed."""
        if person_name not in self.interviewed_people:
            self.interviewed_people.append(person_name)
    
    def get_relationships(self, person_name: str) -> List[Dict]:
        """Get all relationships for a person."""
        if not db.is_active:
            return []
        
        query = f"""
        MATCH (p1:Person {{name: '{person_name}'}})-[r]->(p2:Person)
        RETURN type(r) AS relationship, p2.name AS target, r.detail AS detail
        """
        result = db.graph.query(query)
        
        relationships = []
        for record in result.result_set:
            relationships.append({
                "type": record[0],
                "target": record[1],
                "detail": record[2]
            })
        
        return relationships
    
    def consult_sherlock(self, question: str) -> str:
        """Use RAG to get detective advice from Sherlock Holmes books."""
        docs = self.vector_db.similarity_search(question, k=3)
        
        context = "\n\n".join([doc.page_content for doc in docs])
        
        prompt = f"""Based on these excerpts from detective stories:

{context}

Question: {question}

Provide a brief, atmospheric response in the style of Sherlock Holmes."""
        
        # Return context for now - you'll integrate with Ollama next
        return context[:500] + "..."
    
    def make_accusation(self, suspect_name: str) -> Dict:
        """Submit final accusation and check if correct."""
        if not db.is_active:
            return {"correct": False, "message": "Database not active"}
        
        # Find the actual killer
        query = """
        MATCH (k:Person {role: 'Killer'})
        RETURN k.name AS killer
        """
        result = db.graph.query(query)
        
        if not result.result_set:
            return {"correct": False, "message": "No killer defined"}
        
        actual_killer = result.result_set[0][0]
        
        is_correct = (suspect_name.lower() == actual_killer.lower())
        
        return {
            "correct": is_correct,
            "accused": suspect_name,
            "actual_killer": actual_killer,
            "evidence_collected": len(self.discovered_evidence),
            "locations_visited": len(self.visited_locations),
            "time_remaining": self.get_remaining_time()
        }
    
    def get_game_summary(self) -> Dict:
        """Get current game state summary."""
        return {
            "time_remaining": self.get_remaining_time(),
            "current_location": self.current_location,
            "evidence_count": len(self.discovered_evidence),
            "visited_locations": self.visited_locations,
            "interviewed": self.interviewed_people
        }


# Example usage
if __name__ == "__main__":
    game = DetectiveGame(time_limit_minutes=30)
    game.initialize_mystery()
    game.start_game()
    
    # Simulate investigation
    print("\n--- Searching Garden ---")
    items = game.search_location("Garden")
    for item in items:
        print(f"  📦 {item['name']}: {item['description']}")
    
    print("\n--- Who was in the Garden at 10:00 PM? ---")
    witnesses = game.query_witnesses("Garden", "10:00 PM")
    for w in witnesses:
        print(f"  👤 {w['name']} ({w['role']})")
    
    print("\n--- What are Lady Margaret's relationships? ---")
    rels = game.get_relationships("Lady Margaret")
    for r in rels:
        print(f"  💔 {r['type']} → {r['target']}: {r['detail']}")
    
    print("\n--- Making accusation ---")
    result = game.make_accusation("Thomas Gardener")
    print(f"  {'✅ CORRECT!' if result['correct'] else '❌ WRONG!'}")
    print(f"  Actual killer: {result['actual_killer']}")