"""Türkçe RAG veri kümesini denetle ve örnek arama yap."""

from pathlib import Path

from sherlock_ai.rag import TurkceBilgiTabani


def main() -> None:
    kok = Path(__file__).resolve().parents[1]
    bilgi = TurkceBilgiTabani(kok / "data")
    print(f"Türkçe bilgi tabanı hazır: {len(bilgi.parcalar)} parça.")
    ornekler = bilgi.ara("kilitli oda zaman çizelgesi yanıltıcı kanıt", 3)
    for sira, sonuc in enumerate(ornekler, 1):
        print(f"\n{sira}. {sonuc['kaynak']} · puan {sonuc['puan']}")
        print(str(sonuc["metin"])[:240] + "…")


if __name__ == "__main__":
    main()
