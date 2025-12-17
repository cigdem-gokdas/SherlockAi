"""
Dinamik Hikaye Üreticisi
Ollama kullanarak her seferinde farklı cinayet senaryoları oluşturur
"""
import json
import random
from typing import Dict, List
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from falkor import db


class MysteryGenerator:
    """AI tabanlı dedektif hikayesi üreticisi."""
    
    def __init__(self, model_name: str = "llama3.2"):
        """Ollama modelini başlat."""
        self.llm = Ollama(model=model_name, temperature=0.9)  # Yaratıcılık için yüksek temp
        
        # RAG - Sherlock kitaplarından ilham al
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
        
        # Hikaye şablonları
        self.themes = [
            "manor murder", "poisoning at dinner", "locked room mystery",
            "inheritance dispute", "blackmail gone wrong", "revenge plot",
            "love triangle murder", "stolen jewels and murder"
        ]
        
        self.time_periods = [
            "Victorian era", "1920s glamour", "1950s noir", "modern day"
        ]
        
    def get_inspiration_from_books(self, theme: str) -> str:
        """Sherlock kitaplarından tema ile ilgili pasajlar çek."""
        query = f"mystery investigation {theme} clues suspects"
        docs = self.vector_db.similarity_search(query, k=2)
        
        if docs:
            return docs[0].page_content[:500]
        return ""
    
    def generate_case_concept(self) -> Dict:
        """Ana hikaye konseptini üret."""
        theme = random.choice(self.themes)
        era = random.choice(self.time_periods)
        
        inspiration = self.get_inspiration_from_books(theme)
        
        prompt = f"""You are a mystery writer creating a detective game case.

THEME: {theme}
ERA: {era}

INSPIRATION FROM CLASSIC DETECTIVE STORIES:
{inspiration}

Generate a murder mystery case with:
1. A victim (name, background, why killed)
2. 4-5 suspects (names, roles, motives)
3. The actual killer (and their secret motive)
4. 3-4 locations where events occurred
5. A brief crime description (when, where, how)

Return ONLY valid JSON in this exact format:
{{
  "title": "Case title",
  "victim": {{
    "name": "Name",
    "background": "Description",
    "killed_when": "Time",
    "killed_where": "Location"
  }},
  "suspects": [
    {{
      "name": "Name",
      "role": "Role",
      "trait": "Personality",
      "motive": "Why they might have done it",
      "is_killer": false
    }}
  ],
  "killer": {{
    "name": "Name (must match one suspect)",
    "true_motive": "The real hidden reason"
  }},
  "locations": ["Location1", "Location2", "Location3"],
  "crime_summary": "Brief description of what happened"
}}

IMPORTANT: 
- One suspect must have "is_killer": true
- Killer's name must exactly match one suspect's name
- Make it atmospheric and intriguing!
"""
        
        response = self.llm.invoke(prompt)
        
        # Temizle ve JSON parse et
        try:
            # JSON bloğunu bul
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                case_data = json.loads(json_str)
                return case_data
            else:
                print("⚠️ JSON bulunamadı, varsayılan hikaye kullanılıyor")
                return self._get_fallback_case()
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse hatası: {e}")
            print("Response:", response[:200])
            return self._get_fallback_case()
    
    def generate_clues(self, case_data: Dict) -> List[Dict]:
        """Kanıtları üret."""
        victim = case_data['victim']['name']
        killer_name = case_data['killer']['name']
        locations = case_data['locations']
        
        prompt = f"""Generate 5 physical clues/evidence for this murder case:

VICTIM: {victim}
KILLER: {killer_name}
LOCATIONS: {', '.join(locations)}

Create clues that:
- Some point to the real killer
- Some are red herrings pointing to innocent suspects
- Are found in different locations
- Include items like: weapons, letters, personal items, traces

Return ONLY a JSON array:
[
  {{
    "item_name": "Name of item",
    "location": "Where found (must be from locations list)",
    "description": "What it reveals",
    "points_to_killer": true/false
  }}
]
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                clues = json.loads(json_str)
                return clues
            else:
                return self._get_fallback_clues(locations)
                
        except json.JSONDecodeError:
            return self._get_fallback_clues(locations)
    
    def generate_alibis(self, case_data: Dict) -> List[Dict]:
        """Şüphelilerin nerede olduklarını üret."""
        suspects = case_data['suspects']
        locations = case_data['locations']
        crime_time = case_data['victim']['killed_when']
        
        alibis = []
        
        for suspect in suspects:
            # Katil suç mahallinde olmalı
            if suspect.get('is_killer'):
                alibis.append({
                    "person": suspect['name'],
                    "location": case_data['victim']['killed_where'],
                    "time": crime_time
                })
            else:
                # Masum kişiler farklı yerlerde
                other_locations = [loc for loc in locations 
                                 if loc != case_data['victim']['killed_where']]
                alibis.append({
                    "person": suspect['name'],
                    "location": random.choice(other_locations) if other_locations else locations[0],
                    "time": crime_time
                })
        
        # Kurban da ekle
        alibis.append({
            "person": case_data['victim']['name'],
            "location": case_data['victim']['killed_where'],
            "time": crime_time
        })
        
        return alibis
    
    def generate_relationships(self, case_data: Dict) -> List[Dict]:
        """İlişkileri üret."""
        suspects = case_data['suspects']
        victim_name = case_data['victim']['name']
        
        relationships = []
        
        # Her şüpheli ile kurban arasında ilişki
        for suspect in suspects:
            rel_type = random.choice(["HATES", "FEARS", "LOVES", "RESENTS", "DISTRUSTS"])
            relationships.append({
                "person1": suspect['name'],
                "person2": victim_name,
                "type": rel_type,
                "detail": suspect['motive']
            })
        
        # Şüpheliler arası ilişkiler (2-3 tane)
        for _ in range(min(3, len(suspects))):
            if len(suspects) >= 2:
                p1, p2 = random.sample(suspects, 2)
                rel_type = random.choice(["KNOWS", "ALLIES_WITH", "COMPETES_WITH"])
                relationships.append({
                    "person1": p1['name'],
                    "person2": p2['name'],
                    "type": rel_type,
                    "detail": f"Connected through the case"
                })
        
        return relationships
    
    def create_full_mystery(self) -> Dict:
        """Tüm bileşenleri birleştirerek hikaye oluştur."""
        print("\n🎭 AI yeni bir cinayet hikayesi üretiyor...")
        
        # 1. Ana konsept
        case_data = self.generate_case_concept()
        print(f"✅ Hikaye: {case_data.get('title', 'Untitled Mystery')}")
        
        # 2. Kanıtlar
        clues = self.generate_clues(case_data)
        print(f"✅ {len(clues)} kanıt üretildi")
        
        # 3. Alibiler
        alibis = self.generate_alibis(case_data)
        print(f"✅ {len(alibis)} alibi oluşturuldu")
        
        # 4. İlişkiler
        relationships = self.generate_relationships(case_data)
        print(f"✅ {len(relationships)} ilişki tanımlandı")
        
        return {
            "case": case_data,
            "clues": clues,
            "alibis": alibis,
            "relationships": relationships
        }
    
    def load_mystery_to_database(self, mystery: Dict):
        """Üretilen hikayeyi FalkorDB'ye yükle."""
        if not db.is_active:
            print("❌ FalkorDB bağlantısı yok!")
            return
        
        print("\n💾 Hikaye FalkorDB'ye yükleniyor...")
        
        # Reset database
        db.reset_game()
        
        case = mystery['case']
        
        # 1. Kurbanı ekle
        db.add_person(
            case['victim']['name'],
            'Victim',
            case['victim']['background']
        )
        
        # 2. Şüphelileri ekle
        for suspect in case['suspects']:
            role = 'Killer' if suspect.get('is_killer') else 'Suspect'
            db.add_person(suspect['name'], role, suspect['trait'])
        
        # 3. Kanıtları ekle
        for clue in mystery['clues']:
            db.add_clue(
                clue['item_name'],
                clue['location'],
                clue['description']
            )
        
        # 4. Alibileri ekle
        for alibi in mystery['alibis']:
            db.add_location_record(
                alibi['person'],
                alibi['location'],
                alibi['time']
            )
        
        # 5. İlişkileri ekle
        for rel in mystery['relationships']:
            db.add_relationship(
                rel['person1'],
                rel['person2'],
                rel['type'],
                rel['detail']
            )
        
        print("✅ Hikaye veritabanına yüklendi!")
        
        return case
    
    def _get_fallback_case(self) -> Dict:
        """Hata durumunda varsayılan hikaye."""
        return {
            "title": "The Manor Murder",
            "victim": {
                "name": "Lord Henry",
                "background": "Wealthy nobleman",
                "killed_when": "10:00 PM",
                "killed_where": "Garden"
            },
            "suspects": [
                {
                    "name": "Lady Margaret",
                    "role": "Wife",
                    "trait": "Calculating",
                    "motive": "Inheritance",
                    "is_killer": False
                },
                {
                    "name": "Thomas Gardener",
                    "role": "Gardener",
                    "trait": "Jealous",
                    "motive": "Secret affair",
                    "is_killer": True
                }
            ],
            "killer": {
                "name": "Thomas Gardener",
                "true_motive": "Love and jealousy"
            },
            "locations": ["Garden", "Library", "Kitchen", "Bedroom"],
            "crime_summary": "Lord Henry was found dead in the garden"
        }
    
    def _get_fallback_clues(self, locations: List[str]) -> List[Dict]:
        """Varsayılan kanıtlar."""
        return [
            {
                "item_name": "Bloody Knife",
                "location": locations[0] if locations else "Garden",
                "description": "Kitchen knife with fingerprints",
                "points_to_killer": True
            }
        ]


# Test fonksiyonu
def main():
    """Hikaye üreticiyi test et."""
    generator = MysteryGenerator(model_name="llama3.2")
    
    # Yeni hikaye üret
    mystery = generator.create_full_mystery()
    
    # Hikayeyi veritabanına yükle
    case = generator.load_mystery_to_database(mystery)
    
    # Özet göster
    print("\n" + "="*60)
    print(f"📖 {case['title']}")
    print("="*60)
    print(f"\n💀 KURBAN: {case['victim']['name']}")
    print(f"   {case['victim']['background']}")
    print(f"   Öldürüldü: {case['victim']['killed_when']} - {case['victim']['killed_where']}")
    
    print(f"\n🕵️ ŞÜPHELİLER:")
    for suspect in case['suspects']:
        marker = "🔴" if suspect.get('is_killer') else "🔵"
        print(f"   {marker} {suspect['name']} ({suspect['role']})")
        print(f"      Motif: {suspect['motive']}")
    
    print(f"\n🔍 KANIT SAYISI: {len(mystery['clues'])}")
    print(f"📍 LOKASYON SAYISI: {len(case['locations'])}")
    print("\n✅ Hikaye hazır! Şimdi main.py ile oynamaya başlayabilirsin.")


if __name__ == "__main__":
    main()