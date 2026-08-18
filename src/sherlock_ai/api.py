"""SherlockAI HTTP API'si ve web arayüzü."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .ai import YapayZekaIstemcisi
from .game import OyunYoneticisi
from .rag import TurkceBilgiTabani
from .schemas import SorguIstegi, SoruIstegi, SuclamaIstegi, YeniOyunIstegi

PROJE_KOKU = Path(__file__).resolve().parents[2]
WEB = PROJE_KOKU / "web"
load_dotenv(PROJE_KOKU / ".env")

rag = TurkceBilgiTabani(PROJE_KOKU / "data")
yapay_zeka = YapayZekaIstemcisi(rag)
oyunlar = OyunYoneticisi(yapay_zeka)

app = FastAPI(
    title="SherlockAI",
    description="Türkçe yapay zekâ destekli sinematik detektiflik oyunu",
    version="2.1.0",
    docs_url="/gelistirici",
    redoc_url=None,
)
app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")


@app.get("/", include_in_schema=False)
def ana_sayfa() -> FileResponse:
    return FileResponse(WEB / "index.html")


@app.get("/api/durum")
def sistem_durumu() -> dict:
    return yapay_zeka.durum()


@app.post("/api/oyun")
def yeni_oyun(istek: YeniOyunIstegi) -> dict:
    oturum = oyunlar.yeni(istek.tema.strip(), istek.zorluk, istek.sure_dakika)
    return oturum.genel_veri()


@app.get("/api/oyun/{oturum_id}")
def oyun_durumu(oturum_id: str) -> dict:
    try:
        return oyunlar.getir(oturum_id).genel_veri()
    except KeyError as hata:
        raise HTTPException(404, str(hata)) from hata


@app.post("/api/oyun/{oturum_id}/ara/{mekan_id}")
def mekan_ara(oturum_id: str, mekan_id: str) -> dict:
    try:
        return oyunlar.mekan_ara(oturum_id, mekan_id)
    except KeyError as hata:
        raise HTTPException(404, str(hata)) from hata
    except ValueError as hata:
        raise HTTPException(400, str(hata)) from hata


@app.post("/api/oyun/{oturum_id}/sorgula")
def sorgula(oturum_id: str, istek: SorguIstegi) -> dict:
    try:
        return oyunlar.sorgula(oturum_id, istek.supheli_id, istek.soru.strip())
    except KeyError as hata:
        raise HTTPException(404, str(hata)) from hata
    except ValueError as hata:
        raise HTTPException(400, str(hata)) from hata


@app.post("/api/oyun/{oturum_id}/danis")
def danis(oturum_id: str, istek: SoruIstegi) -> dict:
    try:
        return oyunlar.yardim(oturum_id, istek.soru.strip())
    except KeyError as hata:
        raise HTTPException(404, str(hata)) from hata


@app.post("/api/oyun/{oturum_id}/sucla")
def sucla(oturum_id: str, istek: SuclamaIstegi) -> dict:
    try:
        return oyunlar.sucla(oturum_id, istek.supheli_id, istek.gerekce.strip())
    except KeyError as hata:
        raise HTTPException(404, str(hata)) from hata
    except ValueError as hata:
        raise HTTPException(400, str(hata)) from hata
