import os
import json
import shutil
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Klasör yolları
DATA_PATH = "./data"
DB_PATH = "./chroma_db"

def load_json_files(directory):
    """JSON formatındaki diyalog dosyalarını okur."""
    documents = []
    if not os.path.exists(directory):
        return documents
        
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # JSON liste mi sözlük mü kontrol et
                    if isinstance(data, list):
                        items = data
                    else:
                        items = [data] # Tek objeyse listeye çevir

                    for item in items:
                        # İçerik oluştur
                        content = f"Rol: {item.get('rol', 'Bilinmiyor')}\n"
                        content += f"Karakteristik: {item.get('karakteristik', '')}\n"
                        content += "Örnek Konuşma Tarzı:\n"
                        if 'ornek_cumleler' in item:
                            for ornek in item['ornek_cumleler']:
                                content += f"- {ornek}\n"
                        
                        # Belgeye dönüştür
                        documents.append(Document(page_content=content, metadata={"source": filename, "type": "dialogue_style"}))
            except Exception as e:
                print(f"⚠️ {filename} okunurken hata: {e}")
    return documents

def create_vector_db():
    print("🕵️‍♂️ Veri Yükleyicisi Başlatılıyor...")
    
    # Klasör kontrolü
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
        print(f"⚠️ '{DATA_PATH}' klasörü oluşturuldu. Lütfen içine .txt kitapları ve .json dosyalarını atıp tekrar çalıştırın.")
        return

    # 1. Metin Dosyalarını Yükle (.txt)
    print("📚 Kitaplar (.txt) taranıyor...")
    txt_loader = DirectoryLoader(DATA_PATH, glob="./*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    book_docs = txt_loader.load()
    
    # 2. JSON Dosyalarını Yükle (.json)
    print("🎭 Karakter Diyalogları (.json) taranıyor...")
    json_docs = load_json_files(DATA_PATH)
    
    all_docs = book_docs + json_docs
    
    if not all_docs:
        print("❌ HATA: 'data' klasöründe hiç dosya bulunamadı!")
        return

    print(f"✅ Toplam {len(all_docs)} parça veri bulundu.")

    # 3. Parçalama
    print("✂️  Veriler işleniyor...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(all_docs)

    # 4. Embedding (TÜRKÇE İÇİN KRİTİK NOKTA)
    # ollama.py ile aynı model olmak ZORUNDA
    print("🧠 Yapay zeka modeli hazırlanıyor (paraphrase-multilingual-MiniLM-L12-v2)...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    # 5. Veritabanını Temizle ve Oluştur
    if os.path.exists(DB_PATH):
        print("🗑️  Eski veritabanı temizleniyor...")
        shutil.rmtree(DB_PATH)

    print("💾 Veritabanı kaydediliyor...")
    Chroma.from_documents(documents=chunks, embedding=embedding_model, persist_directory=DB_PATH)
    print("🎉 İŞLEM TAMAM! Veritabanı hazır.")

if __name__ == "__main__":
    create_vector_db()