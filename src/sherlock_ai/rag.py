"""Türkçe odaklı, çevrimdışı çalışabilen melez bilgi getirme katmanı."""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

KELIME = re.compile(r"[a-zçğıöşüâîû]+", re.IGNORECASE)
DURAK = {
    "acaba",
    "ama",
    "ancak",
    "artık",
    "bir",
    "biri",
    "bu",
    "bunu",
    "bunun",
    "da",
    "daha",
    "de",
    "diye",
    "en",
    "gibi",
    "hem",
    "her",
    "ile",
    "ise",
    "için",
    "kadar",
    "ki",
    "mi",
    "mı",
    "mu",
    "mü",
    "ne",
    "neden",
    "nasıl",
    "o",
    "olan",
    "olarak",
    "onun",
    "sonra",
    "şey",
    "ve",
    "veya",
    "ya",
    "çok",
}


def _temizle(metin: str) -> str:
    """RAG bağlamına konuşma talimatı ve gereksiz yabancı kalıntı taşıma."""

    metin = re.sub(r"(?i)\b(mon ami|sacre bleu|excuse me|femme fatale|bro)\b", "", metin)
    metin = re.sub(r"\s+", " ", metin).strip()
    return metin


def _kok(kelime: str) -> str:
    """Ağır bir dil paketi olmadan, arama için hafif Türkçe gövdeleme."""

    for ek in (
        "lerinizden",
        "larınızdan",
        "lerinden",
        "larından",
        "lerimiz",
        "larımız",
        "likleri",
        "lıkları",
        "sinden",
        "sından",
        "lerden",
        "lardan",
        "iniz",
        "ınız",
        "leri",
        "ları",
        "lik",
        "lık",
        "luk",
        "lük",
        "dan",
        "den",
        "dir",
        "dır",
        "dur",
        "dür",
        "nin",
        "nın",
        "nun",
        "nün",
        "de",
        "da",
        "ye",
        "ya",
    ):
        if len(kelime) > len(ek) + 3 and kelime.endswith(ek):
            return kelime[: -len(ek)]
    return kelime


def ayir(metin: str) -> list[str]:
    return [_kok(k.casefold()) for k in KELIME.findall(metin) if k.casefold() not in DURAK]


@dataclass(slots=True)
class Parca:
    metin: str
    kaynak: str
    terimler: Counter[str]


class TurkceBilgiTabani:
    """BM25 benzeri sıralamayla çalışan küçük, şeffaf bir yerel RAG indeksi."""

    def __init__(self, veri_dizini: str | Path):
        self.veri_dizini = Path(veri_dizini)
        self.parcalar: list[Parca] = []
        self.belge_sikligi: Counter[str] = Counter()
        self.ortalama_uzunluk = 1.0
        self.yukle()

    def _metinleri_oku(self) -> Iterable[tuple[str, str]]:
        for yol in sorted(self.veri_dizini.glob("*.txt")):
            yield yol.name, yol.read_text(encoding="utf-8", errors="ignore")

        profil_yolu = self.veri_dizini / "karakter_profilleri.json"
        if profil_yolu.exists():
            try:
                for sira, oge in enumerate(json.loads(profil_yolu.read_text(encoding="utf-8"))):
                    alanlar = [
                        oge.get("meslek", ""),
                        oge.get("kisilik_ozeti", ""),
                        oge.get("konusma_tarzi", ""),
                        oge.get("ornek_cumle", ""),
                    ]
                    yield f"karakter_profilleri.json#{sira + 1}", "\n".join(alanlar)
            except (json.JSONDecodeError, OSError):
                pass

    @staticmethod
    def _parcala(metin: str, hedef: int = 720, bindirme: int = 100) -> Iterable[str]:
        metin = metin.replace("\r", "")
        bolumler = [b.strip() for b in re.split(r"\n\s*\n|[-]{20,}", metin) if b.strip()]
        tampon = ""
        for bolum in bolumler:
            if len(tampon) + len(bolum) + 1 <= hedef:
                tampon = f"{tampon} {bolum}".strip()
                continue
            if tampon:
                yield _temizle(tampon)
            bindirme_metni = tampon[-bindirme:]
            sinirlar = [bindirme_metni.find(im) for im in ".!?" if bindirme_metni.find(im) >= 0]
            if sinirlar:
                bindirme_metni = bindirme_metni[min(sinirlar) + 1 :].lstrip(' "»”')
            elif " " in bindirme_metni:
                bindirme_metni = bindirme_metni.split(" ", 1)[1]
            tampon = f"{bindirme_metni} {bolum}".strip()
        if tampon:
            yield _temizle(tampon)

    def yukle(self) -> None:
        self.parcalar.clear()
        self.belge_sikligi.clear()
        for kaynak, metin in self._metinleri_oku():
            for parca_metni in self._parcala(metin):
                terimler = Counter(ayir(parca_metni))
                if len(terimler) < 4:
                    continue
                self.parcalar.append(Parca(parca_metni, kaynak, terimler))
                self.belge_sikligi.update(terimler.keys())
        if self.parcalar:
            self.ortalama_uzunluk = sum(sum(p.terimler.values()) for p in self.parcalar) / len(self.parcalar)

    def ara(self, sorgu: str, adet: int = 4) -> list[dict[str, str | float]]:
        terimler = ayir(sorgu)
        if not terimler or not self.parcalar:
            return []
        toplam = len(self.parcalar)
        sonuclar: list[tuple[float, Parca]] = []
        for parca in self.parcalar:
            uzunluk = sum(parca.terimler.values()) or 1
            puan = 0.0
            for terim in terimler:
                siklik = parca.terimler.get(terim, 0)
                if not siklik:
                    continue
                idf = math.log(
                    1 + (toplam - self.belge_sikligi[terim] + 0.5) / (self.belge_sikligi[terim] + 0.5)
                )
                puan += (
                    idf * (siklik * 2.2) / (siklik + 1.2 * (0.25 + 0.75 * uzunluk / self.ortalama_uzunluk))
                )
            if puan:
                sonuclar.append((puan, parca))
        sonuclar.sort(key=lambda x: x[0], reverse=True)
        return [{"metin": p.metin[:900], "kaynak": p.kaynak, "puan": round(s, 3)} for s, p in sonuclar[:adet]]

    def baglam(self, sorgu: str, adet: int = 4) -> str:
        sonuclar = self.ara(sorgu, adet)
        if not sonuclar:
            return ""
        return "\n\n".join(f"Kaynak {s['kaynak']}: {s['metin']}" for s in sonuclar)
