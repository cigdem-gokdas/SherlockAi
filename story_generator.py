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
        # Temperature düşürüldü, repeat_penalty eklendi (Daha tutarlı olması için)
        self.llm = Ollama(model=model_name, temperature=0.3, repeat_penalty=1.1)
        
        # RAG - Sherlock kitaplarından ilham al
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
        
        # TÜRKÇE karakter isimleri havuzu
        self.turkish_names = [
            "Mehmet Bey", "Ayşe Hanım", "Hasan Efendi", "Zeynep Hanım",
            "Ali Ağa", "Fatma Hanım", "Mustafa Efendi", "Emine Hanım",
            "İbrahim Bey", "Hatice Hanım", "Ahmet Ağa", "Şerife Hanım",
            "Sultan Hanım", "Cemal Bey", "Nermin Hanım", "Kazım Efendi",
            "Münevver Hanım", "Rıza Bey", "Perihan Hanım", "Salih Ağa"
        ]
        
        # TÜRKÇE lokasyon örnekleri
        self.turkish_locations = [
            "Kütüphane", "Bahçe", "Yemek Salonu", "Çalışma Odası",
            "Mutfak", "Yatak Odası", "Sera", "Kiler", "Salon", "Balkon",
            "Misafir Odası", "Avlu", "Teras", "Koridor"
        ]
        
    def get_inspiration_from_books(self, theme: str) -> str:
        """Sherlock kitaplarından tema ile ilgili pasajlar çek."""
        query = f"mystery investigation {theme} clues suspects"
        docs = self.vector_db.similarity_search(query, k=2)
        
        if docs:
            return docs[0].page_content[:500]
        return ""
    
    def generate_case_concept(self) -> Dict:
        """Ana hikaye konseptini üret - TAM TÜRKÇE."""
        
        # Genişletilmiş Türkçe Temalar
        themes = [
            "eski bir konakta cinayet", "akşam yemeğinde zehirlenme", "kilitli oda gizemi",
            "miras kavgası cinayeti", "şantaj mektupları ve ölüm", "intikam planı",
            "gece treninde cinayet", "tiyatro kulisinde ölüm", "aşk üçgeni cinayeti",
            "çalınan mücevher ve cinayet", "ıssız bir adada cinayet", "boğaz vapurunda şüpheli ölüm",
            "tarihi hamamda cinayet", "kapalıçarşı'da gizemli ölüm"
        ]
        
        theme = random.choice(themes)
        
        # DÜZELTME: Prompt içindeki özel isim örnekleri kaldırıldı (Soyutlaştırıldı)
        prompt = f"""SEN BİR TÜRK POLİSİYE ROMAN YAZARISIN.
GÖREVİN: Aşağıdaki temaya uygun, tutarlı bir cinayet kurgusu oluşturmak.

HİKAYE TEMASI: {theme}

KURALLAR:
1. İsimler 19. Yüzyıl Osmanlı/Türk isimleri olmalı (Şevket, Münir, Feride, Gülsüm vb.)
2. Mekanlar o döneme uygun olmalı (Konak, Hamam, Şerbetçi Dükkanı vb.)
3. Asla İngilizce kelime kullanma.
4. "Köşkte Gizem" veya "Ayşe" gibi klişeleri TEKRARLAMA. Her seferinde FARKLI isimler kullan.

ÇIKTI FORMATI (JSON):
{{
  "title": "Hikayenin Başlığı",
  "victim": {{
    "name": "Kurbanın İsmi",
    "background": "Mesleği ve durumu",
    "killed_when": "Ölüm saati",
    "killed_where": "Ölüm yeri"
  }},
  "suspects": [
    {{
      "name": "Şüpheli 1 İsmi",
      "role": "Kurbanla ilişkisi",
      "trait": "Karakter özelliği",
      "motive": "Cinayet nedeni",
      "is_killer": false
    }},
    {{
      "name": "Şüpheli 2 İsmi",
      "role": "İlişkisi",
      "trait": "Özelliği",
      "motive": "Nedeni",
      "is_killer": true
    }},
    {{
      "name": "Şüpheli 3 İsmi",
      "role": "İlişkisi",
      "trait": "Özelliği",
      "motive": "Nedeni",
      "is_killer": false
    }},
    {{
      "name": "Şüpheli 4 İsmi",
      "role": "İlişkisi",
      "trait": "Özelliği",
      "motive": "Nedeni",
      "is_killer": false
    }}
  ],
  "killer": {{
    "name": "KATİL OLAN ŞÜPHELİNİN İSMİ (Yukarıdakiyle AYNI olmalı)",
    "true_motive": "Gerçek sebebi"
  }},
  "locations": ["Mekan1", "Mekan2", "Mekan3", "Mekan4"],
  "crime_summary": "Kısa olay özeti"
}}

SADECE JSON DÖNDÜR.
JSON:"""
        
        response = self.llm.invoke(prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                case_data = json.loads(json_str)
                
                # 1. Türkçeleştirme
                case_data = self._turkishify_data(case_data)
                
                # 2. YENİ DÜZELTME: Mantık ve İsim Kontrolü
                case_data = self._sanitize_story_data(case_data)
                
                return case_data
            else:
                print("⚠️ JSON bulunamadı, varsayılan hikaye kullanılıyor")
                return self._get_fallback_case()
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse hatası: {e}")
            print("Response:", response[:200])
            return self._get_fallback_case()

    def _sanitize_story_data(self, case_data: Dict) -> Dict:
        """YENİ: AI hatalarını (çift isim, eksik katil) düzeltir."""
        
        # 1. İsim Çakışmalarını Önle
        seen_names = set()
        seen_names.add(case_data['victim']['name'])
        
        for i, suspect in enumerate(case_data['suspects']):
            name = suspect['name']
            
            # Eğer isim daha önce kullanıldıysa (çakışma varsa)
            if name in seen_names:
                # Havuzdan kullanılmamış bir isim bul
                new_name = next((n for n in self.turkish_names if n not in seen_names), f"Şüpheli {i+1}")
                print(f"⚠️ İsim çakışması düzeltildi: {name} -> {new_name}")
                case_data['suspects'][i]['name'] = new_name
                name = new_name
            
            seen_names.add(name)

        # 2. Katil Tutarlılığı
        killer_in_suspects = None
        for suspect in case_data['suspects']:
            if suspect.get('is_killer'):
                killer_in_suspects = suspect
                break
        
        # Eğer listede katil işaretlenmemişse, rastgele birini katil yap
        if not killer_in_suspects:
            target_index = random.randint(0, len(case_data['suspects'])-1)
            case_data['suspects'][target_index]['is_killer'] = True
            killer_in_suspects = case_data['suspects'][target_index]
            print(f"⚠️ Katil eksikti, atandı: {killer_in_suspects['name']}")

        # 'killer' objesindeki ismin, şüpheliler listesindeki katille aynı olduğundan emin ol
        case_data['killer']['name'] = killer_in_suspects['name']
        
        # 3. Mekan Sayısı Kontrolü
        while len(case_data['locations']) < 3:
             case_data['locations'].append(random.choice(self.turkish_locations))

        return case_data
    
    def _turkishify_data(self, case_data: Dict) -> Dict:
        """İngilizce kalan isimleri Türkçeleştir."""
        
        # Kurban ismini kontrol et
        victim_name = case_data['victim']['name']
        if not any(char in victim_name for char in 'ıİşŞğĞüÜöÖçÇ'):
            case_data['victim']['name'] = random.choice(self.turkish_names)
        
        # Şüphelileri kontrol et
        for i, suspect in enumerate(case_data['suspects']):
            if not any(char in suspect['name'] for char in 'ıİşŞğĞüÜöÖçÇ'):
                case_data['suspects'][i]['name'] = self.turkish_names[i % len(self.turkish_names)]
        
        # Katil ismini güncelle
        for suspect in case_data['suspects']:
            if suspect.get('is_killer'):
                case_data['killer']['name'] = suspect['name']
                break
        
        # Lokasyonları kontrol et
        for i, loc in enumerate(case_data['locations']):
            if not any(char in loc for char in 'ıİşŞğĞüÜöÖçÇ'):
                case_data['locations'][i] = self.turkish_locations[i % len(self.turkish_locations)]
        
        # Ölüm yerini kontrol et
        if not any(char in case_data['victim']['killed_where'] for char in 'ıİşŞğĞüÜöÖçÇ'):
            case_data['victim']['killed_where'] = case_data['locations'][0]
        
        return case_data
    
    def generate_clues(self, case_data: Dict) -> List[Dict]:
        """Kanıtları üret - TÜRKÇE."""
        victim = case_data['victim']['name']
        killer_name = case_data['killer']['name']
        locations = case_data['locations']
        
        prompt = f"""SEN BİR TÜRK POLİSİYE ROMAN YAZARISIN. SADECE TÜRKÇE YAZ!

BİR CİNAYET VAKASI İÇİN 5 ADET FİZİKSEL KANIT (İPUCU) ÜRET.

Kurban: {victim}
Katil: {killer_name}
Mekanlar: {', '.join(locations)}

KURALLAR:
1. Kanıtlar mantıklı ve bulunabilir olsun
2. EN AZ 2 KANIT, KATİLİ DOĞRUDAN İŞARET ETSİN
3. Diğer kanıtlar yanıltıcı olabilir
4. TÜM KANIT İSİMLERİ TÜRKÇE OLMALIDIR

ÇOK ÖNEMLİ: MUTLAKA TAM OLARAK ŞU FORMATTA JSON OLUŞTUR:
[
  {{
    "item_name": "Kanıt İsmi",
    "location": "Mekan İsmi",
    "description": "Detaylı açıklama",
    "points_to_killer": true
  }},
  {{
    "item_name": "Başka Bir Kanıt",
    "location": "Mekan İsmi",
    "description": "Detaylı açıklama",
    "points_to_killer": false
  }}
]

SADECE JSON ARRAY VER, BAŞKA HİÇBİR ŞEY YAZMA!
"""
        
        response = self.llm.invoke(prompt)
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                clues = json.loads(json_str)
                
                # Kanıt formatını normalize et
                normalized_clues = []
                for clue in clues:
                    normalized_clues.append({
                        'item_name': clue.get('item_name') or clue.get('name') or clue.get('item') or "Bilinmeyen Kanıt",
                        'location': clue.get('location') or clue.get('location_name') or locations[0],
                        'description': clue.get('description') or clue.get('desc') or "Detay yok",
                        'points_to_killer': clue.get('points_to_killer', False)
                    })
                
                return normalized_clues if normalized_clues else self._get_fallback_clues(locations)
            else:
                print("⚠️ JSON bulunamadı, varsayılan kanıtlar kullanılıyor")
                return self._get_fallback_clues(locations)
                
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse hatası: {e}")
            print(f"Response: {response[:200]}")
            return self._get_fallback_clues(locations)
    
    def generate_alibis(self, case_data: Dict) -> List[Dict]:
        """Şüphelilerin nerede olduklarını üret."""
        suspects = case_data['suspects']
        locations = case_data['locations']
        crime_time = case_data['victim']['killed_when']
        
        alibis = []
        
        for suspect in suspects:
            if suspect.get('is_killer'):
                alibis.append({
                    "person": suspect['name'],
                    "location": case_data['victim']['killed_where'],
                    "time": crime_time
                })
            else:
                other_locations = [loc for loc in locations 
                                 if loc != case_data['victim']['killed_where']]
                alibis.append({
                    "person": suspect['name'],
                    "location": random.choice(other_locations) if other_locations else locations[0],
                    "time": crime_time
                })
        
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
        
        for suspect in suspects:
            rel_type = random.choice(["HATES", "FEARS", "LOVES", "RESENTS", "DISTRUSTS"])
            relationships.append({
                "person1": suspect['name'],
                "person2": victim_name,
                "type": rel_type,
                "detail": suspect['motive']
            })
        
        for _ in range(min(3, len(suspects))):
            if len(suspects) >= 2:
                p1, p2 = random.sample(suspects, 2)
                rel_type = random.choice(["KNOWS", "ALLIES_WITH", "COMPETES_WITH"])
                relationships.append({
                    "person1": p1['name'],
                    "person2": p2['name'],
                    "type": rel_type,
                    "detail": f"Vaka ile bağlantılılar"
                })
        
        return relationships
    
    def create_full_mystery(self) -> Dict:
        """Tüm bileşenleri birleştirerek hikaye oluştur."""
        print("\n🎭 AI yeni bir cinayet hikayesi üretiyor...")
        
        # 1. Ana konsept
        case_data = self.generate_case_concept()
        print(f"✅ Hikaye: {case_data.get('title', 'İsimsiz Gizem')}")
        print(f"   Kurban: {case_data['victim']['name']}")
        print(f"   Şüpheli Sayısı: {len(case_data['suspects'])}")
        
        # 2. Kanıtlar
        clues = self.generate_clues(case_data)
        print(f"✅ {len(clues)} kanıt üretildi")
        
        # Debug: Kanıt formatını kontrol et
        if clues:
            first_clue = clues[0]
            print(f"   Örnek kanıt: {first_clue.get('item_name', 'KEY HATASI!')}")
        
        # 3. Alibiler
        alibis = self.generate_alibis(case_data)
        print(f"✅ {len(alibis)} alibi oluşturuldu")
        
        # 4. İlişkiler
        relationships = self.generate_relationships(case_data)
        print(f"✅ {len(relationships)} ilişki tanımlandı")
        
        mystery_data = {
            "case": case_data,
            "clues": clues,
            "alibis": alibis,
            "relationships": relationships
        }
        
        # DEBUG: Tüm veriyi JSON dosyasına kaydet
        try:
            with open("debug_mystery.json", "w", encoding="utf-8") as f:
                json.dump(mystery_data, f, ensure_ascii=False, indent=2)
            print("💾 Debug: Hikaye 'debug_mystery.json' dosyasına kaydedildi")
        except Exception as e:
            print(f"⚠️ Debug kayıt hatası: {e}")
        
        return mystery_data
    
    def load_mystery_to_database(self, mystery: Dict):
        """Üretilen hikayeyi FalkorDB'ye yükle."""
        if not db.is_active:
            print("❌ FalkorDB bağlantısı yok!")
            return
        
        print("\n💾 Hikaye FalkorDB'ye yükleniyor...")
        
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
        
        # 3. Kanıtları ekle (HATA GÜVENLİĞİ)
        for clue in mystery['clues']:
            try:
                # Farklı key isimlerini dene
                item_name = clue.get('item_name') or clue.get('name') or clue.get('item') or "Bilinmeyen Kanıt"
                location = clue.get('location') or clue.get('location_name') or "Bilinmeyen Yer"
                description = clue.get('description') or clue.get('desc') or "Detay yok"
                
                db.add_clue(item_name, location, description)
                print(f"  ✓ Kanıt eklendi: {item_name}")
            except Exception as e:
                print(f"  ⚠️ Kanıt eklenirken hata: {e}")
                print(f"     Clue data: {clue}")
                continue
        
        # 4. Alibileri ekle
        for alibi in mystery['alibis']:
            try:
                person = alibi.get('person') or alibi.get('name') or "Bilinmeyen"
                location = alibi.get('location') or "Bilinmeyen Yer"
                time = alibi.get('time') or "Bilinmeyen Saat"
                
                db.add_location_record(person, location, time)
            except Exception as e:
                print(f"  ⚠️ Alibi eklenirken hata: {e}")
                continue
        
        # 5. İlişkileri ekle
        for rel in mystery['relationships']:
            try:
                person1 = rel.get('person1') or rel.get('from') or "Bilinmeyen1"
                person2 = rel.get('person2') or rel.get('to') or "Bilinmeyen2"
                rel_type = rel.get('type') or "KNOWS"
                detail = rel.get('detail') or "İlişki detayı yok"
                
                db.add_relationship(person1, person2, rel_type, detail)
            except Exception as e:
                print(f"  ⚠️ İlişki eklenirken hata: {e}")
                continue
        
        print("✅ Hikaye veritabanına yüklendi!")
        
        return case
    
    def _get_fallback_case(self) -> Dict:
        """Hata durumunda varsayılan TÜRKÇE hikaye."""
        # DÜZELTME: Kullanıcıya yedek hikayenin devreye girdiği bildiriliyor
        print("\n⚠️ DİKKAT: AI bozuk veri ürettiği için 'YEDEK HİKAYE' (Köşk) devreye girdi!\n")
        return {
            "title": "Köşkte Gizem",
            "victim": {
                "name": "Hasan Efendi",
                "background": "Zengin tüccar",
                "killed_when": "Akşam Saat 22:00",
                "killed_where": "Bahçe"
            },
            "suspects": [
                {
                    "name": "Ayşe Hanım",
                    "role": "Eşi",
                    "trait": "Soğukkanlı",
                    "motive": "Miras",
                    "is_killer": False
                },
                {
                    "name": "Ali Ağa",
                    "role": "Bahçıvan",
                    "trait": "Kıskanç",
                    "motive": "Gizli aşk",
                    "is_killer": True
                },
                {
                    "name": "Mehmet Bey",
                    "role": "İş ortağı",
                    "trait": "Sinirli",
                    "motive": "Borç",
                    "is_killer": False
                },
                {
                    "name": "Fatma Hanım",
                    "role": "Hizmetçi",
                    "trait": "Sessiz",
                    "motive": "Maaş",
                    "is_killer": False
                }
            ],
            "killer": {
                "name": "Ali Ağa",
                "true_motive": "Aşk ve kıskançlık"
            },
            "locations": ["Bahçe", "Kütüphane", "Mutfak", "Yatak Odası"],
            "crime_summary": "Hasan Efendi bahçede ölü bulundu"
        }
    
    def _get_fallback_clues(self, locations: List[str]) -> List[Dict]:
        """Varsayılan kanıtlar - GÜVENLİ FORMAT."""
        loc1 = locations[0] if locations else "Bahçe"
        loc2 = locations[1] if len(locations) > 1 else "Kütüphane"
        loc3 = locations[2] if len(locations) > 2 else "Mutfak"
        
        return [
            {
                "item_name": "Kanlı Hançer",
                "location": loc1,
                "description": "Mutfak hançeri, üzerinde parmak izleri var",
                "points_to_killer": True
            },
            {
                "item_name": "Yırtık Kumaş",
                "location": loc1,
                "description": "Mavi kumaş parçası, bahçıvanın gömleğinden olabilir",
                "points_to_killer": True
            },
            {
                "item_name": "Aşk Mektubu",
                "location": loc2,
                "description": "İmzasız bir mektup, el yazısı tanıdık",
                "points_to_killer": False
            },
            {
                "item_name": "Çamurlu Çizmeler",
                "location": loc3,
                "description": "Bahçıvanın çizmeleri, taze toprak izi",
                "points_to_killer": True
            },
            {
                "item_name": "Zehir Şişesi",
                "location": loc2,
                "description": "Boş arsenik şişesi (yanıltıcı ipucu)",
                "points_to_killer": False
            }
        ]