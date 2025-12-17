"""
Ollama-based AI Agent for SherlockAI
Karakterlere bürünerek rol yapan AI dedektif asistanı
"""
import json
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from falkor import db

class DetectiveAgent:
    """Karakterlere bürünen AI dedektif asistanı."""
    
    def __init__(self, model_name: str = "llama3.2"):
        """
        Ollama agent'ı başlat.
        
        Args:
            model_name: Ollama model adı (llama3.2, mistral, vb.)
        """
        self.llm = Ollama(model=model_name, temperature=0.8)
        
        # Vector DB yükle (Sherlock & Agatha Christie kitapları)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.vector_db = Chroma(
            persist_directory="./chroma_db",
            embedding_function=self.embeddings
        )
        
        # Dedektif asistanı persona
        self.assistant_persona = """Sen deneyimli bir dedektif asistanısın. 
Sherlock Holmes ve Hercule Poirot'nun metotlarını kullanıyorsun.
Konuşman kibar, biraz gizemli ve atmosferik olmalı.
Victorian dönemi İngiliz centilmenliği ile Agatha Christie'nin zarif üslubunu birleştir.

ÖNEMLİ KURALLAR:
- KATİLİ ASLA direkt söyleme, sadece yönlendir
- Mantıksal çıkarımlar öner
- Sorulara kısa (2-3 cümle) ve atmosferik cevaplar ver
- "Şunu unutmayın ki..." veya "Dikkat ederseniz..." gibi ifadeler kullan
- Her zaman "sayın dedektif" diye hitap et
"""
    
    def get_detective_context(self, query: str) -> str:
        """Sherlock/Agatha kitaplarından ilgili pasajları çek."""
        docs = self.vector_db.similarity_search(query, k=2)
        
        if not docs:
            return ""
        
        passages = []
        for doc in docs:
            content = doc.page_content[:400]
            passages.append(content)
        
        return "\n\n".join(passages)
    
    def character_introduction(self, name: str, trait: str, role: str, victim_name: str) -> str:
        """Karakterin kendini tanıtması."""
        
        # Karakterin psikolojisini anlamak için kitaplardan ilham al
        context = self.get_detective_context(f"suspect interrogation {trait} character")
        
        prompt = f"""Sen bir cinayet soruşturmasında şüphelisin. Karaktere bürün ve kendini tanıt.

KİŞİLİK BİLGİLERİN:
- İsmin: {name}
- Karakterin: {trait}
- Rolün: {role}
- Kurban: {victim_name}

KLASIK DEDEKTIF HİKAYELERİNDEN İLHAM:
{context}

Dedektif seni sorgulamaya geldi. İlk karşılaşmada kendini tanıt.

KURALLAR:
- Karakterine uygun konuş (örn: hizmetçiysen resmi, aristokrat isen kibirli)
- 2-3 cümle ile kendini tanıt
- Biraz gergin veya şüpheli görünebilirsin (çünkü şüphelisin)
- Kurbanla ilişkini kısaca belirt
- Victorian/1920s üslubunda konuş

Cevabın (sadece konuşma, başka açıklama yok):"""

        response = self.llm.invoke(prompt)
        return response.strip().strip('"')
    
    def character_response(self, character_name: str, character_trait: str, 
                          question: str, relationships: list, is_killer: bool = False) -> str:
        """Karakterin soruya cevabı."""
        
        # Karakterin ruh halini anlamak için kitaplardan öğren
        context = self.get_detective_context(f"interrogation question {question}")
        
        # İlişkileri formatlayalım
        rel_text = ""
        if relationships:
            rel_text = "İlişkilerin:\n"
            for rel in relationships[:3]:  # Max 3 tane göster
                rel_text += f"- {rel['target']}: {rel['detail']}\n"
        
        killer_instruction = ""
        if is_killer:
            killer_instruction = """
ÖNEMLİ: SEN KATİLSİN AMA BUNU ASLA İTİRAF ETME!
- Savunmacı ol ama şüphe uyandırma
- Yalan söylerken tutarlı ol
- Başkalarını suçlayabilirsin (kırmızı ringa balığı)
- Gerginsen bunu hafif belli et
"""
        else:
            killer_instruction = """
Sen MASUMSUN:
- Gerçekleri söyle ama tam bilgi vermeyebilirsin
- Kendi motifini savunabilirsin
- Başkalarından şüphelenebilirsin
"""
        
        prompt = f"""Sen {character_name} adlı karaktersin. Dedektif sana soru soruyor.

KİŞİLİĞİN: {character_trait}

{rel_text}

{killer_instruction}

DEDEKTIF HİKAYELERİNDEN ÖRNEK DIYALOGLAR:
{context}

DEDEKTİFİN SORUSU: "{question}"

KURALLAR:
- Karakterine sadık kal
- 2-3 cümle ile cevapla
- Victorian/1920s dönemi üslubunda konuş
- Eğer bilmiyorsan "bilmiyorum" diyebilirsin
- Duygularını göster (korku, öfke, üzüntü)

Cevabın (sadece konuşma):"""

        response = self.llm.invoke(prompt)
        return response.strip().strip('"')
    
    def answer_question(self, question: str, game_state: dict = None) -> str:
        """Dedektif asistanı olarak soruya cevap ver."""
        
        # Graph'tan ilgili bilgileri al
        graph_context = self._get_graph_context(question)
        
        # Kitaplardan metot öğren
        detective_methods = self.get_detective_context(question)
        
        game_info = ""
        if game_state:
            game_info = f"""
Soruşturma Durumu:
- Kanıt sayısı: {game_state.get('evidence_count', 0)}
- Ziyaret edilen yerler: {', '.join(game_state.get('visited_locations', [])) or 'Henüz yok'}
- Kalan süre: {game_state.get('time_remaining', 0)} saniye
"""
        
        prompt = f"""{self.assistant_persona}

VAKA VERİLERİ:
{graph_context}

SHERLOCK & AGATHA'DAN METOTLAR:
{detective_methods}

{game_info}

DEDEKTİFİN SORUSU: "{question}"

Kısa (2-3 cümle), atmosferik ve yol gösterici bir cevap ver.
Katili asla söyleme, sadece mantık yürütmeye yönlendir.

Cevabın:"""

        response = self.llm.invoke(prompt)
        return response.strip().strip('"')
    
    def suggest_next_action(self, game_state: dict) -> str:
        """Sonraki adım önerisi."""
        
        visited = game_state.get('visited_locations', [])
        evidence_count = game_state.get('evidence_count', 0)
        
        # Ziyaret edilmemiş yerler
        if db.is_active:
            query = "MATCH (l:Location) RETURN DISTINCT l.name"
            result = db.graph.query(query)
            all_locs = [r[0] for r in result.result_set]
            unvisited = [loc for loc in all_locs if loc not in visited]
        else:
            unvisited = []
        
        prompt = f"""{self.assistant_persona}

Dedektif şu durumda:
- {len(visited)} yer ziyaret edildi: {', '.join(visited) if visited else 'hiçbiri'}
- {evidence_count} kanıt toplandı
- Henüz gidilmemiş yerler: {', '.join(unvisited) if unvisited else 'tüm yerler gezildi'}

Sherlock Holmes tarzında, bir sonraki adım için kısa (2 cümle) öneri ver.

Önerin:"""

        response = self.llm.invoke(prompt)
        return response.strip().strip('"')
    
    def analyze_evidence(self, evidence_list: list) -> str:
        """Kanıtları analiz et."""
        
        if not evidence_list:
            return "Sayın dedektif, henüz analiz edecek kanıt bulunmuyor. Lokasyonları aramaya başlayın."
        
        evidence_text = "\n".join([
            f"- {e['name']} ({e['location']}): {e['description']}"
            for e in evidence_list
        ])
        
        prompt = f"""{self.assistant_persona}

Toplanan Kanıtlar:
{evidence_text}

Bu kanıtları Sherlock Holmes gibi analiz et:
- Hangi kanıtlar birbiriyle bağlantılı?
- Hangi şüpheliyi işaret ediyorlar?
- Çelişkiler var mı?

2-3 cümlelik zarif bir analiz yap. Katili söyleme!

Analizin:"""

        response = self.llm.invoke(prompt)
        return response.strip().strip('"')
    
    def comment_on_evidence(self, item_name: str, description: str) -> str:
        """Yeni bulunan kanıt hakkında yorum."""
        
        context = self.get_detective_context(f"evidence {item_name}")
        
        prompt = f"""{self.assistant_persona}

Dedektif yeni bir kanıt buldu:
Kanıt: {item_name}
Açıklama: {description}

Klasik dedektif hikayelerinden:
{context}

Bu kanıt hakkında kısa (1-2 cümle), atmosferik bir yorum yap.
"İlginç..." veya "Dikkat edin..." gibi başla.

Yorumun:"""

        response = self.llm.invoke(prompt)
        return response.strip().strip('"')
    
    def _get_graph_context(self, query: str) -> str:
        """Graph'tan ilgili bağlamı çek."""
        if not db.is_active:
            return "Veri yok"
        
        context = []
        
        # İnsanlar
        if any(w in query.lower() for w in ["kim", "kişi", "şüpheli", "who"]):
            q = "MATCH (p:Person) WHERE p.role <> 'Killer' RETURN p.name, p.role, p.trait LIMIT 5"
            result = db.graph.query(q)
            if result.result_set:
                context.append("Şüpheliler:")
                for r in result.result_set:
                    context.append(f"- {r[0]} ({r[1]}): {r[2]}")
        
        # Yerler
        if any(w in query.lower() for w in ["nerede", "yer", "where", "location"]):
            q = "MATCH (l:Location) RETURN DISTINCT l.name LIMIT 5"
            result = db.graph.query(q)
            if result.result_set:
                locs = [r[0] for r in result.result_set]
                context.append(f"Yerler: {', '.join(locs)}")
        
        return "\n".join(context) if context else "Henüz veri yok"


# Test
if __name__ == "__main__":
    agent = DetectiveAgent()
    
    # Test dedektif asistanı
    response = agent.answer_question("Nereden başlamalıyım?")
    print(f"Asistan: {response}")