const $ = (secici, kok = document) => kok.querySelector(secici);
const $$ = (secici, kok = document) => [...kok.querySelectorAll(secici)];

const durum = {
  oyun: null,
  aktifSupheli: null,
  sayac: null,
  sorguGecmisi: {},
};

const portreKonumu = (sira) => ["0%", "33.333%", "66.666%", "100%"][sira] || "0%";
const mekanKonumu = (sira) => ["0% 0%", "100% 0%", "0% 100%", "100% 100%"][sira] || "0% 0%";
const guvenli = (metin = "") => String(metin).replace(/[&<>'"]/g, harf => ({"&":"&amp;", "<":"&lt;", ">":"&gt;", "'":"&#39;", '"':"&quot;"}[harf]));

async function api(yol, secenek = {}) {
  const yanit = await fetch(yol, {
    headers: {"Content-Type": "application/json", ...(secenek.headers || {})},
    ...secenek,
  });
  const veri = await yanit.json().catch(() => ({}));
  if (!yanit.ok) throw new Error(veri.detail || "İşlem tamamlanamadı.");
  return veri;
}

function yukle(goster, metin = "Vaka dosyası hazırlanıyor…") {
  $("#yukleniyor-metin").textContent = metin;
  $("#yukleniyor").classList.toggle("is-hidden", !goster);
}

function bildir(metin) {
  const kutu = document.createElement("div");
  kutu.className = "toast";
  kutu.textContent = metin;
  $("#bildirimler").append(kutu);
  setTimeout(() => kutu.remove(), 4200);
}

async function sistemDurumu() {
  try {
    const veri = await api("/api/durum");
    const rozet = $("#model-durumu");
    rozet.classList.toggle("is-live", veri.bagli);
    $("span", rozet).textContent = veri.bagli
      ? `${veri.model} · ${veri.kip || "hazır"}`
      : `${veri.kip || "çevrimdışı güvenli kip"} hazır`;
  } catch {
    $("#model-durumu span").textContent = "Sunucu bekleniyor";
  }
}

function panelAc(ad) {
  $$(".case-nav button").forEach(dugme => dugme.classList.toggle("is-active", dugme.dataset.panel === ad));
  $$(".panel").forEach(panel => panel.classList.toggle("is-active", panel.id === `panel-${ad}`));
}

function sayacBaslat() {
  clearInterval(durum.sayac);
  durum.sayac = setInterval(() => {
    if (!durum.oyun || durum.oyun.bitti) return;
    durum.oyun.kalan_sure = Math.max(0, durum.oyun.kalan_sure - 1);
    sureYaz(durum.oyun.kalan_sure);
    if (durum.oyun.kalan_sure === 0) {
      clearInterval(durum.sayac);
      bildir("Süreniz doldu. Son hükmünüzü vermelisiniz.");
      $("#suclama").showModal();
    }
  }, 1000);
}

function sureYaz(saniye) {
  const dakika = Math.floor(saniye / 60).toString().padStart(2, "0");
  const kalan = (saniye % 60).toString().padStart(2, "0");
  $("#ust-sure").textContent = `${dakika}:${kalan}`;
}

function oyunGoster(veri) {
  durum.oyun = veri;
  $("#acilis").classList.add("is-hidden");
  $("#oyun").classList.remove("is-hidden");
  $("#ust-baslik").textContent = veri.baslik;
  $("#vaka-baslik").textContent = veri.baslik;
  $("#vaka-yer-tarih").textContent = `${veri.yer} · ${veri.tarih}`;
  $("#vaka-giris").textContent = veri.giris;
  $("#kurban-ad").textContent = veri.kurban.ad;
  $("#kurban-kimlik").textContent = veri.kurban.kimlik;
  $("#kurban-zaman").textContent = veri.kurban.olum_zamani;
  $("#kurban-mekan").textContent = veri.kurban.olum_yeri;
  $("#ust-kanit").textContent = veri.kanitlar.length;
  $("#ust-puan").textContent = veri.puan;
  $("#mekan-sayac").textContent = `${veri.mekanlar.filter(m => m.arandi).length}/4`;
  $("#supheli-sayac").textContent = `${veri.supheliler.filter(s => s.sorgulandi).length}/4`;
  $("#kanit-sayac").textContent = veri.kanitlar.length;
  $("#ilerleme-yuzde").textContent = `${veri.ilerleme}%`;
  $("#ilerleme-cizgi").style.width = `${veri.ilerleme}%`;
  sureYaz(veri.kalan_sure);
  renderHizli();
  renderMekanlar();
  renderSupheliler();
  renderKanitlar();
  renderIliskiler();
  renderSuclama();
  sayacBaslat();
}

function renderHizli() {
  const ilkMekan = durum.oyun.mekanlar.find(m => !m.arandi) || durum.oyun.mekanlar[0];
  const ilkSupheli = durum.oyun.supheliler.find(s => !s.sorgulandi) || durum.oyun.supheliler[0];
  $("#hizli-kartlar").innerHTML = `
    <article class="quick-card" data-hizli="mekan" data-id="${guvenli(ilkMekan.id)}"><small>01 · OLAY YERİ</small><h3>${guvenli(ilkMekan.ad)}</h3><p>İlk fiziksel izleri güvenceye al.</p><b>⌖</b></article>
    <article class="quick-card" data-hizli="supheli" data-id="${guvenli(ilkSupheli.id)}"><small>02 · SORGU</small><h3>${guvenli(ilkSupheli.ad)}</h3><p>Zaman çizelgesini kendi ağzından dinle.</p><b>♙</b></article>
    <article class="quick-card" data-hizli="zihin"><small>03 · ÇIKARIM</small><h3>Zihin Odası</h3><p>Kanıtlar arasındaki bağı birlikte sına.</p><b>✦</b></article>`;
  $$(".quick-card").forEach(kart => kart.addEventListener("click", () => {
    if (kart.dataset.hizli === "mekan") { panelAc("mekanlar"); mekanAra(kart.dataset.id); }
    else if (kart.dataset.hizli === "supheli") sorguAc(kart.dataset.id);
    else panelAc("zihin");
  }));
}

function renderMekanlar() {
  $("#mekan-listesi").innerHTML = durum.oyun.mekanlar.map(m => `
    <article class="location-card ${m.arandi ? "is-searched" : ""}" data-mekan="${guvenli(m.id)}">
      <div class="location-card__image" style="--sprite:url('/assets/${guvenli(m.gorsel)}');--sprite-x:${mekanKonumu(m.gorsel_konumu).split(" ")[0]};--sprite-y:${mekanKonumu(m.gorsel_konumu).split(" ")[1]}"></div>
      <span class="location-card__status">${m.arandi ? "ARANDI ✓" : `${m.kanit_sayisi} OLASI BULGU`}</span>
      <div class="location-card__body"><small>MEKÂN ${String(m.gorsel_konumu + 1).padStart(2, "0")}</small><h2>${guvenli(m.ad)}</h2><p>${guvenli(m.betimleme)}</p></div>
    </article>`).join("");
  $$("[data-mekan]").forEach(kart => kart.addEventListener("click", () => mekanAra(kart.dataset.mekan)));
}

async function mekanAra(id) {
  try {
    yukle(true, "Olay yeri inceleniyor…");
    const veri = await api(`/api/oyun/${durum.oyun.oturum_id}/ara/${encodeURIComponent(id)}`, {method: "POST"});
    oyunGoster(veri.durum);
    bildir(veri.mesaj);
    if (veri.yeni_kanitlar.length) panelAc("kanitlar");
  } catch (hata) { bildir(hata.message); }
  finally { yukle(false); }
}

function renderSupheliler() {
  $("#supheli-listesi").innerHTML = durum.oyun.supheliler.map(s => `
    <article class="suspect-card ${s.sorgulandi ? "is-interviewed" : ""}" data-supheli="${guvenli(s.id)}">
      <div class="suspect-card__portrait" style="--portrait-sprite:url('/assets/${guvenli(s.portre)}');--portrait-pos:${portreKonumu(s.portre_konumu)}"></div>
      <span class="suspect-card__tag">${s.sorgulandi ? "SORGU TAMAMLANDI" : "SORGULANMADI"}</span>
      <div class="suspect-card__body"><small>${guvenli(s.rol)}</small><h2>${guvenli(s.ad)}</h2><p>${guvenli(s.kisilik)}</p><p class="suspect-card__motive"><b>Güdü:</b> ${guvenli(s.gorunen_gudusu)}</p></div>
    </article>`).join("");
  $$("[data-supheli]").forEach(kart => kart.addEventListener("click", () => sorguAc(kart.dataset.supheli)));
}

function sorguAc(id) {
  const s = durum.oyun.supheliler.find(oge => oge.id === id);
  if (!s) return;
  durum.aktifSupheli = s;
  $("#sorgu-ad").textContent = s.ad;
  $("#sorgu-rol").textContent = `${s.rol} · ${s.kisilik}`;
  $("#sorgu-portre").style.setProperty("--portrait-sprite", `url('/assets/${s.portre}')`);
  $("#sorgu-portre").style.setProperty("--portrait-pos", portreKonumu(s.portre_konumu));
  const gecmis = durum.sorguGecmisi[id] || [];
  $("#sorgu-gecmisi").innerHTML = gecmis.length ? gecmis.map(balonHtml).join("") : `<div class="bubble bubble--ai">${guvenli(s.ad)} sessizce karşınıza oturdu. İlk sorunuzu bekliyor.</div>`;
  $("#sorgu").showModal();
  setTimeout(() => $("#sorgu-soru").focus(), 120);
}

function balonHtml(ileti) {
  const kullanici = ileti.rol === "dedektif" || ileti.rol === "kullanıcı";
  return `<div class="bubble ${kullanici ? "bubble--user" : "bubble--ai"}">${guvenli(ileti.metin)}</div>`;
}

function renderKanitlar() {
  const varMi = durum.oyun.kanitlar.length > 0;
  $("#kanit-bos").classList.toggle("is-hidden", varMi);
  $("#kanit-listesi").innerHTML = durum.oyun.kanitlar.map((k, i) => {
    const mekan = durum.oyun.mekanlar.find(m => m.id === k.mekan_id);
    return `<article class="evidence-card" data-no="${String(i + 1).padStart(2, "0")}"><small>${guvenli(k.onem.toUpperCase())} ÖNEM · ${guvenli(mekan?.ad || "BİLİNMEYEN")}</small><h2>${guvenli(k.ad)}</h2><p>${guvenli(k.aciklama)}</p><blockquote>${guvenli(k.cikarim)}</blockquote></article>`;
  }).join("");
}

function renderSuclama() {
  $("#suclanan").innerHTML = durum.oyun.supheliler.map(s => `<option value="${guvenli(s.id)}">${guvenli(s.ad)} — ${guvenli(s.rol)}</option>`).join("");
}

const agKonumlari = [{x:.25,y:.29},{x:.75,y:.29},{x:.27,y:.72},{x:.73,y:.72}];
function renderIliskiler() {
  const tahta = $("#iliski-agi");
  tahta.innerHTML = durum.oyun.supheliler.map((s, i) => {
    const k = agKonumlari[i];
    return `<div class="relation-person" data-kisi="${guvenli(s.id)}" style="left:${k.x*100}%;top:${k.y*100}%;--portrait-sprite:url('/assets/${guvenli(s.portre)}');--portrait-pos:${portreKonumu(s.portre_konumu)}"><span>${guvenli(s.ad)}</span></div>`;
  }).join("");
  requestAnimationFrame(iliskiCizgileri);
}

function iliskiCizgileri() {
  const tahta = $("#iliski-agi");
  if (!tahta || !durum.oyun) return;
  $$(".relation-line", tahta).forEach(c => c.remove());
  const gen = tahta.clientWidth, yuk = tahta.clientHeight;
  const harita = Object.fromEntries(durum.oyun.supheliler.map((s, i) => [s.id, agKonumlari[i]]));
  durum.oyun.iliskiler.forEach(iliski => {
    const a = harita[iliski.kaynak_id], b = harita[iliski.hedef_id];
    if (!a || !b) return;
    const x1 = a.x*gen, y1 = a.y*yuk, x2 = b.x*gen, y2 = b.y*yuk;
    const cizgi = document.createElement("div");
    cizgi.className = "relation-line";
    cizgi.style.left = `${x1}px`; cizgi.style.top = `${y1}px`;
    cizgi.style.width = `${Math.hypot(x2-x1, y2-y1)}px`;
    cizgi.style.transform = `rotate(${Math.atan2(y2-y1, x2-x1)*180/Math.PI}deg)`;
    cizgi.innerHTML = `<span>${guvenli(iliski.tur)}</span>`;
    tahta.prepend(cizgi);
  });
}

async function yardimciyaSor(soru) {
  if (!soru.trim()) return;
  const gecmis = $("#danisma-gecmisi");
  gecmis.insertAdjacentHTML("beforeend", balonHtml({rol:"kullanıcı", metin:soru}));
  gecmis.scrollTop = gecmis.scrollHeight;
  try {
    const veri = await api(`/api/oyun/${durum.oyun.oturum_id}/danis`, {method:"POST", body:JSON.stringify({soru})});
    gecmis.insertAdjacentHTML("beforeend", balonHtml({rol:"yardımcı", metin:veri.cevap}));
    oyunGoster(veri.durum);
    panelAc("zihin");
  } catch (hata) { bildir(hata.message); }
  gecmis.scrollTop = gecmis.scrollHeight;
}

$("#dosya-ac").addEventListener("click", () => $("#yeni-vaka").showModal());
$("#nasil-oynanir").addEventListener("click", () => $("#kilavuz").showModal());
$("#eve-don").addEventListener("click", olay => { olay.preventDefault(); clearInterval(durum.sayac); $("#oyun").classList.add("is-hidden"); $("#acilis").classList.remove("is-hidden"); });
$$(".case-nav button").forEach(dugme => dugme.addEventListener("click", () => panelAc(dugme.dataset.panel)));
$("#suclama-ac").addEventListener("click", () => $("#suclama").showModal());
$("#sorgu-kapat").addEventListener("click", () => $("#sorgu").close());
window.addEventListener("resize", iliskiCizgileri);

$("#yeni-vaka-formu").addEventListener("submit", async olay => {
  olay.preventDefault();
  $("#yeni-vaka").close();
  yukle(true);
  try {
    const veri = await api("/api/oyun", {method:"POST", body:JSON.stringify({tema:$("#tema").value, zorluk:$("#zorluk").value, sure_dakika:Number($("#sure").value)})});
    durum.sorguGecmisi = {};
    oyunGoster(veri);
    panelAc("dosya");
    bildir(veri.ai_uretimi ? "Yerel yapay zekâ yeni bir vaka mühürledi." : "Doğrulanmış çevrimdışı vaka açıldı.");
  } catch (hata) { bildir(hata.message); }
  finally { yukle(false); }
});

$("#sorgu-formu").addEventListener("submit", async olay => {
  olay.preventDefault();
  const alan = $("#sorgu-soru"), soru = alan.value.trim();
  if (!soru || !durum.aktifSupheli) return;
  alan.value = ""; alan.disabled = true;
  const gecmis = $("#sorgu-gecmisi");
  gecmis.insertAdjacentHTML("beforeend", balonHtml({rol:"dedektif", metin:soru}));
  gecmis.scrollTop = gecmis.scrollHeight;
  try {
    const veri = await api(`/api/oyun/${durum.oyun.oturum_id}/sorgula`, {method:"POST", body:JSON.stringify({supheli_id:durum.aktifSupheli.id, soru})});
    durum.sorguGecmisi[durum.aktifSupheli.id] = veri.gecmis;
    gecmis.insertAdjacentHTML("beforeend", balonHtml({rol:"şüpheli", metin:veri.cevap}));
    oyunGoster(veri.durum);
    panelAc("supheliler");
  } catch (hata) { bildir(hata.message); }
  finally { alan.disabled = false; alan.focus(); gecmis.scrollTop = gecmis.scrollHeight; }
});

$("#danisma-formu").addEventListener("submit", async olay => {
  olay.preventDefault(); const alan = $("#danisma-soru"), soru = alan.value; alan.value = ""; await yardimciyaSor(soru);
});
$("#kanit-analiz").addEventListener("click", () => { panelAc("zihin"); yardimciyaSor("Topladığım kanıtları zaman çizelgesi ve çelişkiler bakımından birlikte yorumla."); });

$("#suclama-formu").addEventListener("submit", async olay => {
  olay.preventDefault();
  $("#suclama").close(); yukle(true, "Hüküm kayda geçiriliyor…");
  try {
    const veri = await api(`/api/oyun/${durum.oyun.oturum_id}/sucla`, {method:"POST", body:JSON.stringify({supheli_id:$("#suclanan").value, gerekce:$("#gerekce").value})});
    clearInterval(durum.sayac); oyunGoster(veri.durum); clearInterval(durum.sayac);
    const sinif = veri.dogru ? "result-good" : "result-bad";
    $("#sonuc-icerik").innerHTML = `<div class="result-seal ${sinif}">${veri.dogru ? "✓" : "×"}</div><p class="eyebrow">DOSYA KAPANDI · ${veri.puan} PUAN</p><h2>${veri.dogru ? "Vaka çözüldü." : "Katil gölgede kaldı."}</h2><p>${guvenli(veri.suclanan)} hakkındaki hükmünüz ${veri.dogru ? "kanıtlarla doğrulandı" : "gerçeği karşılamadı"}.</p><div class="result-solution ${sinif}">${guvenli(veri.cozum)}</div><button id="yeniden" class="button button--primary button--full">Yeni bir dosya aç <span>→</span></button>`;
    $("#sonuc").showModal();
    $("#yeniden").addEventListener("click", () => { $("#sonuc").close(); $("#yeni-vaka").showModal(); });
  } catch (hata) { bildir(hata.message); }
  finally { yukle(false); }
});

sistemDurumu();
