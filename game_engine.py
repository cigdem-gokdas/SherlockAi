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
        self.time_limit = time_limit_minutes * 60
        self.start_time = None
        self.game_active = False
        self.discovered_evidence = []
        self.visited_locations = []
        self.interviewed_people = []
        self.current_location = "Crime Scene"
        self.case_title = "Unknown Case"
        self.victim_name = "Unknown Victim"
        
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
        """
        print("\n🔎 INITIALIZING NEW CASE...")
        
        if use_ai_generator and mystery_data:
            case = mystery_data['case']
            print(f"✅ Mystery initialized: '{case['title']}'")
            print(f"🎭 Victim: {case['victim']['name']} found dead in {case['victim']['killed_where']} at {case['victim']['killed_when']}")
            self.case_title = case['title']
            self.victim_name = case['victim']['name']
        else:
            db.reset_game()
            
            db.add_person("Hasan Efendi", "Victim", "Zengin tüccar")
            db.add_person("Ayşe Hanım", "Suspect", "Eşi, miras alacak")
            db.add_person("Mehmet Ağa", "Suspect", "Uşak, işten çıkarıldı")
            db.add_person("Fatma Hanım", "Suspect", "Hizmetçi")
            db.add_person("Ali Ağa", "Killer", "Bahçıvan")
            
            db.add_location_record("Ayşe Hanım", "Yatak Odası", "Saat 22:00")
            db.add_location_record("Mehmet Ağa", "Mutfak", "Saat 22:15")
            db.add_location_record("Ali Ağa", "Bahçe", "Saat 22:00")
            db.add_location_record("Hasan Efendi", "Bahçe", "Saat 22:00")
            
            db.add_relationship("Ayşe Hanım", "Hasan Efendi", "RESENTS", 
                              "Kocasına kızgın")
            db.add_relationship("Ali Ağa", "Ayşe Hanım", "LOVES", 
                              "Gizli aşk")
            
            db.add_clue("Kanlı Hançer", "Bahçe", "Mutfak hançeri, parmak izleriyle")
            db.add_clue("Aşk Mektubu", "Çalışma Odası", "İmzasız mektup")
            
            print("✅ Mystery initialized: 'Köşkte Gizem'")
            print(f"🎭 Victim: Hasan Efendi found dead in Bahçe at 22:00")
            self.case_title = "Köşkte Gizem"
            self.victim_name = "Hasan Efendi"
        
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
        """Search a location for clues using FalkorDB - PARAMETRELİ."""
        if not db.is_active:
            return []
        
        # Parametreli sorgu
        query = """
        MATCH (i:Item)-[:FOUND_IN]->(l:Location {name: $location_name})
        RETURN i.name AS item, i.description AS description
        """
        params = {'location_name': location_name}
        result = db.graph.query(query, params)
        
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
        """Find who was at a location at a specific time - PARAMETRELİ."""
        if not db.is_active:
            return []
        
        query = """
        MATCH (p:Person)-[r:SEEN_AT]->(l:Location {name: $location})
        WHERE r.time = $time
        RETURN p.name AS person, p.role AS role, r.time AS time
        """
        params = {'location': location, 'time': time}
        result = db.graph.query(query, params)
        
        witnesses = []
        for record in result.result_set:
            person_name = record[0]
            witnesses.append({
                "name": person_name,
                "role": record[1],
                "time": record[2]
            })
            
            if person_name not in self.interviewed_people:
                self.interviewed_people.append(person_name)
        
        return witnesses
    
    def mark_as_interviewed(self, person_name: str):
        """Mark a person as interviewed."""
        if person_name not in self.interviewed_people:
            self.interviewed_people.append(person_name)
    
    def get_relationships(self, person_name: str) -> List[Dict]:
        """Get all relationships for a person - PARAMETRELİ."""
        if not db.is_active:
            return []
        
        query = """
        MATCH (p1:Person {name: $person_name})-[r]->(p2:Person)
        RETURN type(r) AS relationship, p2.name AS target, r.detail AS detail
        """
        params = {'person_name': person_name}
        result = db.graph.query(query, params)
        
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
        
        return context[:500] + "..."
    
    def make_accusation(self, suspect_name: str) -> Dict:
        """Submit final accusation and check if correct."""
        if not db.is_active:
            return {"correct": False, "message": "Database not active"}
        
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