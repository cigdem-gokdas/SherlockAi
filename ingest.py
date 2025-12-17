import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Klasör yolları
DATA_PATH = "./data"
DB_PATH = "./chroma_db"

def create_vector_db():
    print("🕵️‍♂️ SherlockAi Veri Yükleyicisi Başlatılıyor...")
    if not os.path.exists(DATA_PATH):
        print(f"HATA: '{DATA_PATH}' klasörü bulunamadı!")
        return
    
    print("📚 Kitaplar okunuyor...")
    loader = DirectoryLoader(DATA_PATH, glob="./*.txt", loader_cls=TextLoader, loader_kwargs={'encoding': 'utf-8'})
    documents = loader.load()
    print(f"✅ Toplam {len(documents)} kitap/belge yüklendi.")

    print("✂️  Metinler parçalanıyor...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    print(f"🧩 {len(chunks)} veri parçacığı oluşturuldu.")

    print("🧠 Embedding modeli hazırlanıyor (Bu biraz sürebilir)...")
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("💾 Veritabanına kaydediliyor...")
    vector_db = Chroma.from_documents(documents=chunks, embedding=embedding_model, persist_directory=DB_PATH)
    print(f"🎉 İŞLEM BAŞARILI! Veritabanı oluşturuldu.")

if __name__ == "__main__":
    create_vector_db()