import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient

from sherlock_ai.ai import YapayZekaIstemcisi
from sherlock_ai.api import app
from sherlock_ai.fallback_case import yedek_vaka
from sherlock_ai.rag import TurkceBilgiTabani


class VakaTestleri(TestCase):
    def test_yedek_vaka_tutarli(self):
        vaka = yedek_vaka()
        self.assertEqual(len(vaka.supheliler), 4)
        self.assertEqual(len(vaka.mekanlar), 4)
        self.assertEqual(sum(s.katil for s in vaka.supheliler), 1)
        self.assertEqual(sum(s.cinsiyet == "kadın" for s in vaka.supheliler), 2)
        for supheli in vaka.supheliler:
            uygun = {"kadın": {0, 3}, "erkek": {1, 2}}[supheli.cinsiyet]
            self.assertIn(supheli.portre_konumu, uygun)
        self.assertGreaterEqual(len(vaka.kanitlar), 6)

    def test_rag_turkce_sorgu_getirir(self):
        kok = Path(__file__).resolve().parents[1]
        rag = TurkceBilgiTabani(kok / "data")
        sonuclar = rag.ara("kilitli oda kanıt ve zaman çizelgesi", 3)
        self.assertTrue(sonuclar)
        self.assertIn("metin", sonuclar[0])


class ApiTestleri(TestCase):
    def setUp(self):
        self.istemci = TestClient(app)

    @patch("sherlock_ai.api.yapay_zeka._sohbet", return_value=None)
    def test_cevrimdisi_tam_oyun_akisi(self, _):
        cevap = self.istemci.post(
            "/api/oyun", json={"tema": "Kilitli oda", "zorluk": "müfettiş", "sure_dakika": 35}
        )
        self.assertEqual(cevap.status_code, 200)
        oyun = cevap.json()
        self.assertFalse(oyun["ai_uretimi"])
        self.assertNotIn("cozum", oyun)
        self.assertNotIn("katil", oyun["supheliler"][0])

        oturum = oyun["oturum_id"]
        mekan = oyun["mekanlar"][0]["id"]
        arama = self.istemci.post(f"/api/oyun/{oturum}/ara/{mekan}")
        self.assertEqual(arama.status_code, 200)
        self.assertGreater(len(arama.json()["durum"]["kanitlar"]), 0)

        supheli = oyun["supheliler"][0]["id"]
        sorgu = self.istemci.post(
            f"/api/oyun/{oturum}/sorgula",
            json={"supheli_id": supheli, "soru": "O gece neredeydiniz?"},
        )
        self.assertEqual(sorgu.status_code, 200)
        self.assertTrue(sorgu.json()["cevap"])

        katil = next(s.id for s in yedek_vaka().supheliler if s.katil)
        sonuc = self.istemci.post(
            f"/api/oyun/{oturum}/sucla",
            json={"supheli_id": katil, "gerekce": "Kanıtlar aynı kaçış yolunu gösteriyor."},
        )
        self.assertEqual(sonuc.status_code, 200)
        self.assertTrue(sonuc.json()["dogru"])
        self.assertIn("Rauf Efendi", sonuc.json()["cozum"])


class SaglayiciTestleri(TestCase):
    def setUp(self):
        kok = Path(__file__).resolve().parents[1]
        self.rag = TurkceBilgiTabani(kok / "data")

    @patch("sherlock_ai.ai.httpx.post")
    @patch("sherlock_ai.ai.YapayZekaIstemcisi._etiketler", return_value=[])
    def test_ollama_yokken_geminiye_gecer(self, _, gonder):
        sahte = gonder.return_value
        sahte.raise_for_status.return_value = None
        sahte.json.return_value = {"candidates": [{"content": {"parts": [{"text": "Türkçe yanıt"}]}}]}
        with patch.dict(
            os.environ,
            {"AI_PROVIDER": "auto", "GEMINI_API_KEY": "test-anahtari"},
            clear=False,
        ):
            istemci = YapayZekaIstemcisi(self.rag)
            cevap = istemci._sohbet([{"role": "user", "content": "Bir ipucu ver."}])

        self.assertEqual(cevap, "Türkçe yanıt")
        self.assertEqual(gonder.call_args.kwargs["headers"]["x-goog-api-key"], "test-anahtari")
        self.assertNotIn("test-anahtari", str(gonder.call_args.kwargs["json"]))

    @patch("sherlock_ai.ai.YapayZekaIstemcisi._etiketler", return_value=["qwen3:1.7b"])
    def test_durumda_ollama_onceliklidir(self, _):
        with patch.dict(os.environ, {"AI_PROVIDER": "auto", "GEMINI_API_KEY": "test"}):
            durum = YapayZekaIstemcisi(self.rag).durum()

        self.assertEqual(durum["saglayici"], "ollama")
        self.assertEqual(durum["model"], "qwen3:1.7b")
