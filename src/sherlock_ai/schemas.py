"""SherlockAI veri sözleşmeleri.

Model çıktısı bu şemalardan geçmeden oyuna alınmaz. Böylece yerel model
yarım veya tutarsız bir cevap verse bile oyun durumu bozulmaz.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class Kurban(BaseModel):
    ad: str = Field(min_length=3, max_length=70)
    kimlik: str = Field(min_length=8, max_length=240)
    olum_zamani: str = Field(min_length=3, max_length=80)
    olum_yeri: str = Field(min_length=3, max_length=80)


class Supheli(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    ad: str = Field(min_length=3, max_length=70)
    rol: str = Field(min_length=3, max_length=100)
    kisilik: str = Field(min_length=3, max_length=180)
    gorunen_gudusu: str = Field(min_length=3, max_length=220)
    gizli_bilgi: str = Field(min_length=3, max_length=300)
    katil: bool = False
    portre: str = "portreler.jpg"
    portre_konumu: int = Field(default=0, ge=0, le=3)


class Mekan(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    ad: str = Field(min_length=3, max_length=80)
    betimleme: str = Field(min_length=8, max_length=260)
    gorsel: str = "mekanlar.jpg"
    gorsel_konumu: int = Field(default=0, ge=0, le=3)


class Kanit(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_-]+$")
    ad: str = Field(min_length=2, max_length=90)
    mekan_id: str
    aciklama: str = Field(min_length=8, max_length=300)
    cikarim: str = Field(min_length=8, max_length=260)
    onem: Literal["düşük", "orta", "yüksek"] = "orta"


class Iliski(BaseModel):
    kaynak_id: str
    hedef_id: str
    tur: str = Field(min_length=2, max_length=80)
    ayrinti: str = Field(min_length=3, max_length=200)


class Vaka(BaseModel):
    baslik: str = Field(min_length=4, max_length=100)
    tarih: str = Field(min_length=3, max_length=70)
    yer: str = Field(min_length=3, max_length=100)
    giris: str = Field(min_length=30, max_length=700)
    kurban: Kurban
    supheliler: list[Supheli] = Field(min_length=4, max_length=4)
    mekanlar: list[Mekan] = Field(min_length=4, max_length=4)
    kanitlar: list[Kanit] = Field(min_length=6, max_length=10)
    iliskiler: list[Iliski] = Field(min_length=4, max_length=12)
    cozum: str = Field(min_length=30, max_length=700)
    rag_notu: str = ""

    @field_validator("supheliler")
    @classmethod
    def tekil_supheli_adlari(cls, value: list[Supheli]) -> list[Supheli]:
        adlar = [k.ad.casefold() for k in value]
        if len(set(adlar)) != len(adlar):
            raise ValueError("Şüpheli adları benzersiz olmalı")
        return value

    @model_validator(mode="after")
    def tutarliligi_denetle(self) -> Vaka:
        if sum(k.katil for k in self.supheliler) != 1:
            raise ValueError("Tam olarak bir katil bulunmalı")
        mekanlar = {m.id for m in self.mekanlar}
        supheliler = {s.id for s in self.supheliler}
        if any(k.mekan_id not in mekanlar for k in self.kanitlar):
            raise ValueError("Her kanıt geçerli bir mekâna bağlı olmalı")
        if any(i.kaynak_id not in supheliler or i.hedef_id not in supheliler for i in self.iliskiler):
            raise ValueError("Her ilişki geçerli şüphelilere bağlı olmalı")
        return self


class YeniOyunIstegi(BaseModel):
    tema: str = Field(default="Boğaz kıyısında kilitli oda", min_length=3, max_length=120)
    zorluk: Literal["çırak", "müfettiş", "üstat"] = "müfettiş"
    sure_dakika: int = Field(default=35, ge=10, le=90)


class SorguIstegi(BaseModel):
    supheli_id: str
    soru: str = Field(min_length=2, max_length=500)


class SoruIstegi(BaseModel):
    soru: str = Field(min_length=2, max_length=500)


class SuclamaIstegi(BaseModel):
    supheli_id: str
    gerekce: str = Field(default="", max_length=800)
