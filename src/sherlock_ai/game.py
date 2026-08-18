"""Sunucu tarafındaki oyun oturumları ve kurallar."""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from .ai import YapayZekaIstemcisi
from .schemas import Vaka


@dataclass
class OyunOturumu:
    kimlik: str
    vaka: Vaka
    sure_saniye: int
    ai_uretimi: bool
    baslangic: float = field(default_factory=time.time)
    bulunan_kanitlar: set[str] = field(default_factory=set)
    gezilen_mekanlar: set[str] = field(default_factory=set)
    sorgulananlar: set[str] = field(default_factory=set)
    sorgu_gecmisi: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    bitti: bool = False
    kazanildi: bool = False

    @property
    def kalan_sure(self) -> int:
        return max(0, self.sure_saniye - int(time.time() - self.baslangic))

    @property
    def puan(self) -> int:
        kanit_puani = len(self.bulunan_kanitlar) * 80
        sorgu_puani = len(self.sorgulananlar) * 45
        zaman_puani = self.kalan_sure // 6
        return kanit_puani + sorgu_puani + zaman_puani + (750 if self.kazanildi else 0)

    def genel_veri(self) -> dict[str, Any]:
        vaka = self.vaka
        bulunan = self.bulunan_kanitlar
        return {
            "oturum_id": self.kimlik,
            "baslik": vaka.baslik,
            "tarih": vaka.tarih,
            "yer": vaka.yer,
            "giris": vaka.giris,
            "kurban": vaka.kurban.model_dump(),
            "supheliler": [
                {
                    "id": s.id,
                    "ad": s.ad,
                    "rol": s.rol,
                    "kisilik": s.kisilik,
                    "gorunen_gudusu": s.gorunen_gudusu,
                    "portre": s.portre,
                    "portre_konumu": s.portre_konumu,
                    "sorgulandi": s.id in self.sorgulananlar,
                }
                for s in vaka.supheliler
            ],
            "mekanlar": [
                {
                    **m.model_dump(),
                    "arandi": m.id in self.gezilen_mekanlar,
                    "kanit_sayisi": sum(1 for k in vaka.kanitlar if k.mekan_id == m.id),
                }
                for m in vaka.mekanlar
            ],
            "kanitlar": [k.model_dump() for k in vaka.kanitlar if k.id in bulunan],
            "iliskiler": [i.model_dump() for i in vaka.iliskiler],
            "kalan_sure": self.kalan_sure,
            "sure_saniye": self.sure_saniye,
            "puan": self.puan,
            "bitti": self.bitti,
            "kazanildi": self.kazanildi,
            "ai_uretimi": self.ai_uretimi,
            "ilerleme": round(len(bulunan) / len(vaka.kanitlar) * 100),
        }


class OyunYoneticisi:
    def __init__(self, ai: YapayZekaIstemcisi):
        self.ai = ai
        self.oturumlar: dict[str, OyunOturumu] = {}
        self.kilit = RLock()

    def yeni(self, tema: str, zorluk: str, sure_dakika: int) -> OyunOturumu:
        vaka, ai_uretimi = self.ai.vaka_uret(tema, zorluk)
        kimlik = secrets.token_urlsafe(18)
        oturum = OyunOturumu(kimlik, vaka, sure_dakika * 60, ai_uretimi)
        with self.kilit:
            self.oturumlar[kimlik] = oturum
        return oturum

    def getir(self, kimlik: str) -> OyunOturumu:
        with self.kilit:
            if kimlik not in self.oturumlar:
                raise KeyError("Oyun oturumu bulunamadı")
            return self.oturumlar[kimlik]

    def mekan_ara(self, kimlik: str, mekan_id: str) -> dict[str, Any]:
        oturum = self.getir(kimlik)
        if oturum.bitti:
            raise ValueError("Bu vaka kapanmış")
        mekan = next((m for m in oturum.vaka.mekanlar if m.id == mekan_id), None)
        if not mekan:
            raise ValueError("Mekân bulunamadı")
        onceki = set(oturum.bulunan_kanitlar)
        oturum.gezilen_mekanlar.add(mekan_id)
        oturum.bulunan_kanitlar.update(k.id for k in oturum.vaka.kanitlar if k.mekan_id == mekan_id)
        yeniler = [k.model_dump() for k in oturum.vaka.kanitlar if k.id in oturum.bulunan_kanitlar - onceki]
        return {
            "mekan": mekan.model_dump(),
            "yeni_kanitlar": yeniler,
            "mesaj": f"{mekan.ad} dikkatle arandı. {len(yeniler)} yeni kanıt dosyaya eklendi."
            if yeniler
            else "Bu mekândaki kayda değer bütün izler daha önce toplandı.",
            "durum": oturum.genel_veri(),
        }

    def sorgula(self, kimlik: str, supheli_id: str, soru: str) -> dict[str, Any]:
        oturum = self.getir(kimlik)
        if oturum.bitti:
            raise ValueError("Bu vaka kapanmış")
        supheli = next((s for s in oturum.vaka.supheliler if s.id == supheli_id), None)
        if not supheli:
            raise ValueError("Şüpheli bulunamadı")
        oturum.sorgulananlar.add(supheli_id)
        cevap = self.ai.sorgula(oturum.vaka, supheli, soru, oturum.bulunan_kanitlar)
        gecmis = oturum.sorgu_gecmisi.setdefault(supheli_id, [])
        gecmis.extend([{"rol": "dedektif", "metin": soru}, {"rol": "şüpheli", "metin": cevap}])
        return {"cevap": cevap, "gecmis": gecmis[-12:], "durum": oturum.genel_veri()}

    def yardim(self, kimlik: str, soru: str) -> dict[str, Any]:
        oturum = self.getir(kimlik)
        cevap = self.ai.yardimciya_sor(
            oturum.vaka,
            soru,
            oturum.bulunan_kanitlar,
            oturum.gezilen_mekanlar,
        )
        return {"cevap": cevap, "durum": oturum.genel_veri()}

    def sucla(self, kimlik: str, supheli_id: str, gerekce: str) -> dict[str, Any]:
        oturum = self.getir(kimlik)
        if oturum.bitti:
            raise ValueError("Bu vaka zaten kapanmış")
        supheli = next((s for s in oturum.vaka.supheliler if s.id == supheli_id), None)
        if not supheli:
            raise ValueError("Şüpheli bulunamadı")
        oturum.bitti = True
        oturum.kazanildi = supheli.katil
        yeterli_kanit = len(oturum.bulunan_kanitlar) >= max(3, len(oturum.vaka.kanitlar) // 2)
        return {
            "dogru": supheli.katil,
            "yeterli_kanit": yeterli_kanit,
            "suclanan": supheli.ad,
            "gerekce": gerekce,
            "cozum": oturum.vaka.cozum,
            "puan": oturum.puan,
            "durum": oturum.genel_veri(),
        }
