"""Model çevrimdışıyken de oynanabilen, elde doğrulanmış Türkçe vaka."""

from __future__ import annotations

from copy import deepcopy

from .schemas import Vaka

VAKA = {
    "baslik": "Yıldız Korusu'nda Son Perde",
    "tarih": "17 Teşrinievvel 1911, gece yarısı",
    "yer": "Kandilli, İstanbul",
    "giris": (
        "Boğaz'ı örten sis, Yıldız Korusu Köşkü'nün pencerelerine dayanırken "
        "ev sahibi Nüzhet Paşa kilitli çalışma odasında ölü bulundu. Kapının "
        "anahtarı içerideydi; masadaki saat 23.17'de durmuş, gramofon ise aynı "
        "plağın son ölçüsünü durmadan çalıyordu. Köşkte bulunan dört kişinin de "
        "Paşa'dan sakladığı bir şey var."
    ),
    "kurban": {
        "ad": "Nüzhet Paşa",
        "kimlik": "Eski saray tercümanı, nadir evrak koleksiyoncusu ve köşkün sahibi",
        "olum_zamani": "22.55 ile 23.15 arası",
        "olum_yeri": "Kilitli Çalışma Odası",
    },
    "supheliler": [
        {
            "id": "leyla",
            "ad": "Leyla Hanım",
            "rol": "Paşa'nın yeğeni ve tek mirasçısı",
            "kisilik": "Ölçülü, mağrur; sözlerini titizlikle seçiyor.",
            "gorunen_gudusu": "Vasiyetname değiştirilirse mirasını yitirecekti.",
            "gizli_bilgi": "O gece kasadan annesine ait mektupları almak için çalışma odasına girdi.",
            "katil": False,
            "cinsiyet": "kadın",
            "portre": "portreler.jpg",
            "portre_konumu": 0,
        },
        {
            "id": "cemil",
            "ad": "Cemil Bey",
            "rol": "Aile hekimi",
            "kisilik": "Soğukkanlı, kesin konuşan ve kolay öfkelenmeyen biri.",
            "gorunen_gudusu": "Paşa, sahte reçete defterini polise vermekle tehdit etmişti.",
            "gizli_bilgi": "Paşa'nın kahvesine uyku ilacı kattı; öldürmek değil konuşmasını geciktirmek istedi.",
            "katil": False,
            "cinsiyet": "erkek",
            "portre": "portreler.jpg",
            "portre_konumu": 1,
        },
        {
            "id": "rauf",
            "ad": "Rauf Efendi",
            "rol": "Köşkün kâtibi",
            "kisilik": "Titiz, içine kapanık; mürekkep lekeli parmaklarını saklıyor.",
            "gorunen_gudusu": "Hesap defterlerindeki açığı Paşa fark etmişti.",
            "gizli_bilgi": "Gramofon düzeneğini kurdu, saati durdurdu ve balkon geçidini kullandı.",
            "katil": True,
            "cinsiyet": "erkek",
            "portre": "portreler.jpg",
            "portre_konumu": 2,
        },
        {
            "id": "sabiha",
            "ad": "Sabiha Hanım",
            "rol": "Ünlü tiyatro sanatçısı ve eski aile dostu",
            "kisilik": "Duygulu, göz alıcı; gerçeği bir sahne metni gibi anlatıyor.",
            "gorunen_gudusu": "Paşa, geçmişlerine dair mektupları yayımlayacaktı.",
            "gizli_bilgi": "23.10'da kış bahçesinde Rauf'u ıslak bir dosya taşırken gördü.",
            "katil": False,
            "cinsiyet": "kadın",
            "portre": "portreler.jpg",
            "portre_konumu": 3,
        },
    ],
    "mekanlar": [
        {
            "id": "calisma",
            "ad": "Kilitli Çalışma Odası",
            "betimleme": "Ceviz kitaplıklar, sönmüş şömine ve hâlâ dönen bir gramofon. Balkon kapısının pirinç sürgüsünde ince bir çizik var.",
            "gorsel": "mekanlar.jpg",
            "gorsel_konumu": 0,
        },
        {
            "id": "kis_bahcesi",
            "ad": "Kış Bahçesi",
            "betimleme": "Buğulu camların ardında Boğaz ışıkları. Islak taşlarda çalışma odasına uzanan tek sıra ayak izi seçiliyor.",
            "gorsel": "mekanlar.jpg",
            "gorsel_konumu": 1,
        },
        {
            "id": "arsiv",
            "ad": "Bodrum Arşivi",
            "betimleme": "Rutubetli raflar ve mühürlü hesap defterleri. Duvarın gerisinde eski servis geçidinin kapısı gizlenmiş.",
            "gorsel": "mekanlar.jpg",
            "gorsel_konumu": 2,
        },
        {
            "id": "sahne",
            "ad": "Musiki Salonu",
            "betimleme": "Kadife perdeli küçük bir sahne, nota sehpaları ve Paşa'nın davetliler için hazırlattığı gramofon plakları.",
            "gorsel": "mekanlar.jpg",
            "gorsel_konumu": 3,
        },
    ],
    "kanitlar": [
        {
            "id": "saat",
            "ad": "Durdurulmuş Cep Saati",
            "mekan_id": "calisma",
            "aciklama": "Akrep ile yelkovan 23.17'yi gösteriyor; fakat kurma yayı sağlam ve camında darbe yok.",
            "cikarim": "Saat kazayla değil, ölüm zamanını saptırmak için elle durdurulmuş.",
            "onem": "yüksek",
        },
        {
            "id": "igne",
            "ad": "Çelik Gramofon İğnesi",
            "mekan_id": "sahne",
            "aciklama": "Kutudaki iğnelerden biri eğilmiş; çalışma odasındaki düzeneğin yayına tam uyuyor.",
            "cikarim": "Duyulan ses canlı bir tartışma değil, önceden hazırlanmış bir kayıttı.",
            "onem": "yüksek",
        },
        {
            "id": "murekkep",
            "ad": "Mor Mürekkep Lekesi",
            "mekan_id": "kis_bahcesi",
            "aciklama": "Servis kapısının kolunda yalnızca kâtip odasında kullanılan mor mürekkep var.",
            "cikarim": "Geçidi kullanan kişi kısa süre önce kâtip masasındaki mürekkebe dokunmuş.",
            "onem": "yüksek",
        },
        {
            "id": "recete",
            "ad": "Yırtık Reçete",
            "mekan_id": "calisma",
            "aciklama": "Şömine dibindeki parçada uyku ilacı ölçüsü ve Cemil Bey'in parafı görülüyor.",
            "cikarim": "Doktor bir şey saklıyor; ancak doz tek başına öldürücü değil.",
            "onem": "orta",
        },
        {
            "id": "ayak_izi",
            "ad": "Dar Topuk İzi",
            "mekan_id": "kis_bahcesi",
            "aciklama": "Yağmur suyu içindeki izler arşiv merdiveninden balkona gidiyor; dönüş izi bulunmuyor.",
            "cikarim": "Katil kapı yerine servis geçidini kullanmış olabilir.",
            "onem": "yüksek",
        },
        {
            "id": "defter",
            "ad": "Çifte Kayıtlı Hesap Defteri",
            "mekan_id": "arsiv",
            "aciklama": "Aynı ödeme iki ayrı tarihte gösterilmiş; düzeltmeler Rauf Efendi'nin el yazısıyla yapılmış.",
            "cikarim": "Kâtibin zimmet açığı ve güçlü bir susturma nedeni var.",
            "onem": "yüksek",
        },
        {
            "id": "mektup",
            "ad": "Mühürlü Aile Mektupları",
            "mekan_id": "arsiv",
            "aciklama": "Leyla Hanım'ın annesine ait mektupların kurdelesi o gece yeniden bağlanmış.",
            "cikarim": "Leyla'nın yalanı cinayeti değil, aile sırrını saklıyor.",
            "onem": "düşük",
        },
        {
            "id": "dugme",
            "ad": "Sedef Düğme",
            "mekan_id": "calisma",
            "aciklama": "Balkon perdesine takılmış düğme, kâtibin yeleğindeki eksik parçayla aynı oyma desenini taşıyor.",
            "cikarim": "Rauf Efendi çalışma odasından balkon yoluyla ayrılmış.",
            "onem": "yüksek",
        },
    ],
    "iliskiler": [
        {
            "kaynak_id": "leyla",
            "hedef_id": "cemil",
            "tur": "güveniyor",
            "ayrinti": "Aile hekimine çocukluğundan beri güveniyor.",
        },
        {
            "kaynak_id": "cemil",
            "hedef_id": "rauf",
            "tur": "kuşkulanıyor",
            "ayrinti": "Hesap defterlerindeki silintileri fark etti.",
        },
        {
            "kaynak_id": "rauf",
            "hedef_id": "sabiha",
            "tur": "korkuyor",
            "ayrinti": "Kış bahçesinde görüldüğünü biliyor.",
        },
        {
            "kaynak_id": "sabiha",
            "hedef_id": "leyla",
            "tur": "koruyor",
            "ayrinti": "Aile mektuplarının açığa çıkmasını istemiyor.",
        },
        {
            "kaynak_id": "leyla",
            "hedef_id": "rauf",
            "tur": "güvenmiyor",
            "ayrinti": "Kâtibin hesapları sakladığını sezdi.",
        },
    ],
    "cozum": (
        "Rauf Efendi, zimmet açığını ortaya çıkaran Nüzhet Paşa'yı susturdu. "
        "Musiki salonundaki plaktan kestiği tartışma kaydını gramofonda çaldırarak "
        "ölüm saatini ileri gösterdi; cep saatini 23.17'de durdurdu. Bodrumdaki "
        "servis geçidinden balkona çıktı. Mor mürekkep, tek yönlü ayak izleri ve "
        "perdede kalan sedef düğme aynı kaçış yolunu doğruluyor."
    ),
    "rag_notu": "Vaka; sahte zaman çizelgesi, masum yalan ile ölümcül yalanı ayırma ve fiziksel izleri birlikte okuma ilkelerinden kuruldu.",
}


def yedek_vaka() -> Vaka:
    """Her oyun için bağımsız bir nesne döndür."""

    return Vaka.model_validate(deepcopy(VAKA))
