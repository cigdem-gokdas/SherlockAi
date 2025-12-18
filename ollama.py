import json
import logging
from langchain_community.llms import Ollama
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from falkor import db

logging.basicConfig(level=logging.INFO)

class DetectiveAgent:
    """
    Tamamen Türkçe konuşan, RAG tabanlı ve karakterlere bürünen dedektif asistanı.
    """
    
    def __init__(self, model_name: str = "gemma2"):
        print(f"🤖 AI Ajanı Başlatılıyor (Model: {model_name})...")
        
        self.llm = Ollama(
            model=model_name, 
            temperature=0.1,    # Gemma2 çok yaratıcıdır, 0.1 gayet iyi.
            repeat_penalty=1.2  # Tekrarı önleyen kritik ayar
        )
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        try:
            self.vector_db = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings
            )
            print("✅ Vektör Veritabanı (RAG) Bağlandı.")
        except Exception as e:
            print(f"❌ Vektör Veritabanı Hatası: {e}")
            self.vector_db = None
        
        self.system_prompt = """SENİN GÖREVİN: Sherlock Holmes evreninde geçen bir cinayet oyununda, oyuncuya yardımcı olan yapay zekasın.

ÇOK ÖNEMLİ KURALLAR (BU KURALLARA UYMAZSAN SİSTEM ÇÖKER):
1. DİL: SADECE SAF VE DURU İSTANBUL TÜRKÇESİ KULLAN.
2. YASAKLAR: Asla İngilizce kelime kullanma (Örn: "invitation", "thing", "suspicion" YASAK). Cümle aralarına İngilizce sıkıştırma.
3. GRAMER: Kelimelere uydurma ekler getirme ("thingi", "suspasiyon" gibi kelimeler uydurma).
4. ÜSLUP: Edebi, 19. yüzyıl beyefendisi/hanımefendisi gibi konuş.
5. GİZLİLİK: Katilin ismini asla direkt söyleme.
"""
    
    def get_rag_context(self, query: str, k: int = 3) -> str:
        if not self.vector_db:
            return ""
        try:
            docs = self.vector_db.similarity_search(query, k=k)
            if not docs:
                return ""
            context_parts = []
            for doc in docs:
                content = doc.page_content.replace("\n", " ").strip()
                context_parts.append(f"- {content}")
            return "\n".join(context_parts)
        except Exception:
            return ""

    def character_introduction(self, name: str, trait: str, role: str, victim_name: str) -> str:
        # Karakter konuşmalarında RAG bazen kafasını karıştırabilir, bu yüzden prompt'u basitleştirdik.
        prompt = f"""{self.system_prompt}

ŞU AN BU KARAKTERİ CANLANDIRIYORSUN:
İsim: {name}
Rol: {role}
Özellik: {trait}
Kurbanla İlişki: {victim_name} tanıyordun.

GÖREV: Dedektife kendini tanıt.
SADECE TÜRKÇE KONUŞ. "Thing", "Invitation" gibi kelimeler kullanma.
Kısa ve öz konuş.

Cevap:"""
        return self._invoke_llm(prompt)
    
    def character_response(self, character_name: str, character_trait: str, 
                          question: str, relationships: list, is_killer: bool = False) -> str:
        
        rel_text = "İlişkilerim:"
        if relationships:
            for r in relationships[:3]:
                rel_text += f"\n- {r['target']} kişisine: {r['detail']}"
        
        secret = "SEN KATİLSİN! Yakalanmamak için mantıklı yalanlar söyle." if is_killer else "SEN MASUMSUN. Bildiklerini anlat."
        
        prompt = f"""{self.system_prompt}

KARAKTERİN: {character_name} ({character_trait})
DURUMUN: {secret}
{rel_text}

SORU: "{question}"

GÖREV:
Bu soruya karakterine uygun cevap ver.
ASLA İNGİLİZCE KELİME KULLANMA.
Saçma kelimeler türetme. Düzgün Türkçe cümle kur.

Cevap:"""
        return self._invoke_llm(prompt)
    
    def answer_question(self, question: str, game_state: dict = None) -> str:
        graph_context = self._get_graph_context(question)
        
        prompt = f"""{self.system_prompt}

BİLGİLER:
{graph_context}

SORU: "{question}"

GÖREV: Dedektif asistanı olarak Türkçe cevap ver. İngilizce terim kullanma.

Cevap:"""
        return self._invoke_llm(prompt)
    
    def suggest_next_action(self, game_state: dict) -> str:
        prompt = f"""{self.system_prompt}
Oyuncu şimdi ne yapmalı? Ona Sherlock tarzı kısa bir tavsiye ver.
Cevap:"""
        return self._invoke_llm(prompt)

    def analyze_evidence(self, evidence_list: list) -> str:
        if not evidence_list: return "Henüz kanıt yok."
        evidence_text = "\n".join([f"- {e['name']}: {e['description']}" for e in evidence_list])
        
        prompt = f"""{self.system_prompt}
KANITLAR:
{evidence_text}

Bu kanıtları yorumla. Türkçe konuş.
Analiz:"""
        return self._invoke_llm(prompt)
    
    def comment_on_evidence(self, item_name: str, description: str) -> str:
        prompt = f"""{self.system_prompt}
Yeni Kanıt: {item_name} ({description})
Buna kısa, gizemli bir tepki ver.
Cevap:"""
        return self._invoke_llm(prompt)
    
    def _get_graph_context(self, query: str) -> str:
        if not db or not db.is_active: return ""
        context = []
        try:
            query_lower = query.lower()
            if any(x in query_lower for x in ['kim', 'kişi', 'şüpheli']):
                q = "MATCH (p:Person) RETURN p.name, p.role, p.trait LIMIT 5"
                res = db.graph.query(q)
                if res.result_set:
                    for r in res.result_set: context.append(f"{r[0]} ({r[1]}) - {r[2]}")
            
            if any(x in query_lower for x in ['nerede', 'mekan', 'yer']):
                q = "MATCH (l:Location) RETURN l.name LIMIT 5"
                res = db.graph.query(q)
                if res.result_set:
                    context.append("Mekanlar: " + ", ".join([r[0] for r in res.result_set]))
        except: pass
        return "\n".join(context)

    def _invoke_llm(self, prompt: str) -> str:
        try:
            response = self.llm.invoke(prompt)
            # İngilizce kaçamakları temizlemeye çalış
            clean = response.strip().strip('"').strip("'")
            if "Here is" in clean or "Sure" in clean: # LLM İngilizce cevap vermeye kalkarsa
                 return "Kafam biraz karıştı dedektif, lütfen sorunuzu Türkçe tekrarlayın."
            return clean
        except Exception as e:
            return "Şu an düşüncelerimi toparlayamıyorum."