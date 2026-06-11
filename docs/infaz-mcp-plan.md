# Ceza İnfaz Hesaplama MCP Sunucusu — Geliştirme Planı (rev. 3)

> Bu doküman, MacBook üzerinde Claude Code ile kodlanacak yerel bir
> "infaz hesaplama" MCP sunucusunun yol haritasıdır. Her faz, Claude Code'a
> doğrudan verilebilecek şekilde somut adımlar içerir.
>
> **Doğrulama notu:** Bölüm 4–6'daki hukuki dayanaklar 11.06.2026 tarihinde
> mevzuat.gov.tr'nin güncel metinlerinden (5275 md. 105/A, 107; TCK md. 61;
> 2324 sayılı CB Yönetmeliği md. 54; 5275 değişiklik tarihçesi listesi)
> birebir doğrulanmış; geçici md. 10 işleyişi Resmî Gazete duyuruları ve
> uzman analizleriyle (Ersan Şen, TBB) çapraz teyit edilmiştir.
>
> **Rev. 3 değişiklikleri:** 7571 (11. Yargı Paketi, RG 25.12.2025) ve
> 7550 (4.6.2025) değişiklikleri kural çekirdeğine işlendi; üç rejim eşiği
> tanımlandı; hesap yöntemi TCK 61/6 ile yasal dayanağa bağlandı;
> müddetname taslağı aracı ve Yönetmelik md. 54/3 şablonu eklendi.

---

## 1. Hedef ve Kapsam

**Hedef:** 5275 sayılı Kanun'a göre, mahkûmiyet bilgilerinden şu tarihleri
hesaplayan, Claude Desktop/Claude Code'a stdio ile bağlanan yerel MCP sunucusu:

1. Koşullu salıverilme (KS) tarihi — md. 107
2. Denetimli serbestlik (DS) tarihi — md. 105/A + geçici md. 6 ve 10
3. Bihakkın (hak ederek) tahliye tarihi
4. Talep hâlinde **müddetname taslağı** (Bölüm 7) — resmî belge değildir
5. (Faz 8) Açık ceza infaz kurumuna ayrılma tarihi

**MVP kapsamı (Faz 1–5):** Tek süreli hapis cezası, yetişkin hükümlü,
üç rejim eşiği (Bölüm 6), aralıklı mahsup, TCK madde/fıkradan otomatik
kategori eşleme, 7550'nin 1/10 şartı.
**MVP dışı (Faz 8):** İçtima, mükerrirlik (md. 108), çocuk hükümlü,
müebbet türleri, md. 110 özel infaz usulleri (konutta infaz),
0-6 yaş çocuklu kadın ve ağır hastalık DS istisnaları (md. 105/A-3).

**Uyarı (ürüne de yazılacak):** Çıktılar tahminîdir; resmî müddetname
Cumhuriyet savcılığınca düzenlenir. Araç hukuki tavsiye vermez.

---

## 2. Teknoloji Seçimi

| Bileşen | Seçim | Gerekçe |
|---|---|---|
| Dil | Python ≥ 3.12 | FastMCP ekosistemi, pydantic ile şema üretimi |
| Paket yöneticisi | `uv` | Tek araçla venv + bağımlılık + çalıştırma |
| MCP çatısı | `fastmcp` (v2) | `@mcp.tool` dekoratörüyle otomatik JSON Schema |
| Veri modeli | `pydantic` v2 | Girdi doğrulama + araç şeması |
| Test | `pytest` | Altın (golden) senaryo testleri |
| Transport | stdio | Yerel kullanım için yeterli |
| Güncellik | GitHub Actions cron + Python betiği | Bölüm 9 |

Kural seti koddan ayrı, `rules/` altında YAML olarak tutulur —
mevzuat değişikliğinde kod değil veri güncellenir.

---

## 3. Proje Yapısı

```
infaz-mcp/
├── pyproject.toml
├── README.md
├── src/infaz_mcp/
│   ├── server.py          # FastMCP araçları (ince katman)
│   ├── engine.py          # Saf hesaplama motoru (MCP'den bağımsız)
│   ├── models.py          # Pydantic girdi/çıktı modelleri
│   ├── regime.py          # Üç eşikli rejim seçici + lehe çift hesap
│   ├── kategori.py        # TCK madde/fıkra → kategori eşleyici
│   ├── dates.py           # TCK 61/6 uyumlu takvim aritmetiği
│   └── muddetname.py      # Yönetmelik md. 54/3 şablonlu taslak üretici
├── rules/
│   ├── oranlar.yaml           # KS oranları, yürürlük aralıklarıyla
│   ├── ds_kurallari.yaml      # DS süreleri, 1/10 şartı, geçici 10 katmanı
│   ├── suc_kategori_map.yaml  # TCK madde/fıkra → kategori + istisna listeleri
│   ├── CHANGELOG.md
│   └── kaynak_durumu.json     # İzlenen mevzuatın imzaları
├── scripts/guncellik_kontrol.py
├── .github/workflows/guncellik.yml
└── tests/
    ├── test_engine.py
    ├── test_kategori.py
    └── golden/
```

---

## 4. Doğruluk Stratejisi

Doğruluğun ölçütü **UYAP'ın ürettiği resmî müddetnamedir**. Dört katmanlı
hiyerarşi (çelişkide üst katman kazanır):

1. **Kanun metni:** 5275 (md. 105/A, 107, 108, 110, geçici md. 6, 9, 10, 11),
   TCK md. 61/6, TMK md. 17. Tek kaynak: mevzuat.gov.tr.
2. **İkincil mevzuat:** 2324 sayılı CB Yönetmeliği (süre belgesi md. 54,
   iyi hâl md. 110), Açık Ceza İnfaz Kurumlarına Ayrılma Yönetmeliği,
   Denetimli Serbestlik Hizmetleri Yönetmeliği, CTE genelgeleri.
3. **İçtihat:** Hesap yöntemine dair Yargıtay/CGK kararları (Faz 2 taraması).
4. **Ampirik:** Gerçek (anonim) müddetnameler nihai golden testlerdir;
   piyasa hesaplayıcıları yalnız çapraz kontroldür.

### Hesap yöntemi sözleşmesi (yasal dayanaklı — TCK md. 61/6)

Doğrulanmış metin: *"Hapis cezasının süresi gün, ay ve yıl hesabıyla
belirlenir. Bir gün, yirmidört saat; bir ay, otuz gündür. Yıl, resmî
takvime göre hesap edilir. Hapis cezası için bir günün … artakalanı
hesaba katılmaz ve bu cezalar infaz edilmez."*

Buna göre `dates.py` kuralları:
- **Yıl** eklemeleri resmî takvimle (`relativedelta(years=n)`),
  **ay** çarpım/kesir hesaplarında **30 gün** sabitiyle yapılır.
- Oran uygulaması süre cinsinden: önce yıl/ay/gün bileşenleri orana
  çarpılır; çıkan **gün kesri atılır** (artakalan infaz edilmez — lehe).
- Mahsup, tutukluluk aralıklarından gün olarak hesaplanır (çakışma
  kontrolüyle) ve tarih eklemelerinden sonra düşülür.
- Faz 2'de bu sözleşme UYAP uygulamasıyla (Yargıtay kararları + gerçek
  müddetname) çapraz test edilir; sapma çıkarsa sözleşme güncellenir.
- Her sonuç `hesap_dokumu` (adım adım ara değerler), `dayanaklar[]` ve
  `kural_surumu` taşır.

### Girdi doğruluğu

Kullanıcı suç kategorisi seçmez; **TCK madde + fıkra** girer,
`suc_kategori_map.yaml` eşler. Eşleşme yoksa araç tahmin etmez —
olası kategorileri dayanaklarıyla listeleyip sorar. Geçici md. 10
istisna listesi (Bölüm 6) ayrı bir bayrak kümesi olarak aynı dosyada tutulur.

---

## 5. Veri Modeli

`InfazGirdisi` (pydantic):

| Alan | Tip | Not |
|---|---|---|
| `ceza_yil / ceza_ay / ceza_gun` | int | Kesinleşmiş toplam ceza |
| `tck_madde`, `tck_fikra` | str | Kategori eşleme; serbest metin değil |
| `suc_tarihi` | date | Üç rejim eşiğinin anahtarı |
| `kesinlesme_tarihi` | date? | Lehe değerlendirme, mükerrirlik |
| `infaz_baslangici` | date | Kuruma giriş / infaz başlangıcı |
| `tutukluluk_araliklari` | list[(date, date)] | Aralıklı mahsup |
| `mahkeme`, `esas_no`, `karar_no` | str? | Müddetname taslağı için (hesabı etkilemez) |
| `dogum_tarihi` | date? | Çocuk hükümlü kuralları (Faz 8) |
| `mukerrir` | bool | md. 108 (Faz 8) |
| `orgut_kapsaminda`, `teror_kapsaminda` | bool | md. 107/4, TMK 17, geçici 10 istisnası |
| `acik_kurumda` | bool? | Geçici 10/6 DS erken yararlanma şartı |

`InfazSonucu`: KS / DS / bihakkın + `uygulanan_rejim`, `alternatif_hesap?`,
`dayanaklar[]`, `hesap_dokumu[]`, `kural_surumu`, `son_dogrulama_tarihi`, `uyari`.

---

## 6. Kural Çekirdeği — Üç Rejim Eşiği (doğrulanmış)

`regime.py`, suç tarihine göre **birikimli** üç katman uygular
(eşik geçildiğinde ilgili katmanın avantajı düşer):

### Katman A — KS oranları (md. 107, tüm suç tarihleri; 7242 sonrası hâli)

| Kategori | Eşik |
|---|---|
| Genel kural (süreli hapis) | **1/2** |
| md. 107/2 a–h: kasten öldürme (TCK 81-83), 87/2-d, işkence/eziyet (94-96), cinsel suçlar (102*, 104*, 105), çocuklarda cinsel suç ve uyuşturucu ticareti, özel hayat (132-138), casusluk (326-339) | **2/3** |
| Örgütlü suçlar (md. 107/4) | **2/3**; müebbet 30, ağırlaştırılmış müebbet 36 yıl |
| Terör (TMK md. 17) | **3/4** |
| Müebbet / ağırlaştırılmış müebbet | sabit **24 / 30 yıl** |
| Çoklu mahkûmiyet üst sınırları (107/3) | 28/30/36 yıl (örgütlüde 32/34/40) |
| 15 yaş altı kurum günü (107/5) | 1 gün = 2 gün |
| Denetim süresi (107/6) | kurumda geçirilmesi gereken süre kadar; bihakkını aşamaz |

> Geçici md. 10, KS **oranlarını değiştirmez** — yalnızca açık kurum ve
> DS zamanlamasını etkiler (Katman C). Bu ayrım koda yorum olarak işlenecek;
> piyasa hesaplayıcılarının tipik hata kaynağıdır.

### Katman B — DS temel kuralı (md. 105/A, 7550 ile değişik)

- Açık kurumda / çocuk eğitimevinde, iyi hâlli, **KS'ye ≤ 1 yıl** kala, talep + infaz hâkimi kararı.
- **7550 şartı (4.6.2025):** KS'ye kadar kurumda geçirilmesi gereken sürenin
  **en az 1/10'u (5 günden az olmamak üzere)** kurumda geçirilmiş olmalı.
  Formül: `DS = max(KS − ds_süresi, infaz_başlangıcı + max(5 gün, gereken_süre/10))`
- İstisnalar (105/A-3): 0-6 yaş çocuklu kadın → KS'ye 2 yıl kala;
  ağır hastalık/engellilik/kocama → 3 yıl kala (raporla).
- Adli para cezasından çevrilen hapiste DS yok (105/A-4).

### Katman C — Suç tarihi eşikleri (geçici maddeler)

| Eşik | Dayanak | Etki |
|---|---|---|
| Suç tarihi **≤ 30.03.2020** | Geçici md. 6 (671 KHK + 7242) | DS süresi **3 yıl**; genel KS oranı 1/2 (kendi istisna listesiyle — Faz 1'de birebir metinden çıkarılacak) |
| Suç tarihi **≤ 31.07.2023** | Geçici md. 10/5-6 (7456 + 7550 + **7571/11. Yargı Paketi, RG 25.12.2025**) | Kapalıdakiler: toplam ceza <10 yıl ise 1 ay, ≥10 yıl ise 3 ay kapalıda kalmak şartıyla, açık kuruma ayrılmasına **3 yıl** kala açığa ayrılabilir. Açıktakiler: en az 3 ay açık kurumda kalmış olmak şartıyla DS'den **3 yıl erken** yararlanır. |
| Suç tarihi **> 31.07.2023** | — | Yalnız Katman A + B |

Geçici 10 **istisna suçları** (7571 ile genişletilmiş, yararlanamaz):
aileye/kadına/çocuğa/savunmasıza karşı kasten öldürme (TCK 82/1 d-e-f),
deprem nedeniyle yapı yıkılması/çökmesi sonucu öldürme suçları,
cinsel dokunulmazlığa karşı suçlar (102, 103, 104/2-3), terör ve
örgütlü suçlar (TCK 220 kapsamı).

### 7550 (4.6.2025) — diğer hesap etkileri (Faz 8 kapsamı, şimdiden kayda)

- md. 108/3: ikinci kez mükerrirlik → "koşullu salıverilmez" kalktı;
  108/1 süreleri uygulanır.
- md. 110: özel infaz usulleri (konutta infaz) eşikleri büyüdü
  (örn. kadın/yaşlı için 1,5→3 yıl, 3→5 yıl).

### Değişiklik tarihçesi (rules/kaynak_durumu.json çekirdeği)

5275'i etkileyen ve hesaba dokunan kanunlar (mevzuat.gov.tr tarihçe
listesinden doğrulandı): 671 KHK (geçici 6) · 7242 (107, 105/A, geçici 6/9)
· 7256, 7331, 7343, 7407 (geçici 9) · 7445 (105/A-5) · 7456 (geçici 10)
· 7550 (105/A, 108, 110, geçici 10/11) · **7571 (geçici 10)**.

> ⚠️ Teknik ders (bu araştırmada yaşandı): mevzuat.gov.tr madde ağacında
> **geçici maddeler ayrı düğüm olarak görünmüyor**. Faz 1'de geçici md.
> 6, 9, 10, 11'in birebir metinleri kanunun TAM METİN çıktısından
> (chunk'lı indirme) alınacak; Bölüm 9'daki izleme de tam metin imzası
> üzerinden yapılacak, madde bazlı değil.

---

## 7. Müddetname Taslağı (`muddetname_taslagi` aracı)

Resmî dayanak şablonu — 2324 sayılı Yönetmelik md. 54/3'teki "süre belgesi"
zorunlu içeriği (doğrulanmış): kimlik/tebligat/iletişim bilgileri, infaz
defteri no, kuruma alınma tarihi, tutukluluk/gözaltı süresi, ceza süresi,
**hakederek ve koşullu salıverilme tarihleri**, cezanın hangi hükme ilişkin olduğu.

- Çıktı: Markdown (isteğe bağlı PDF). Başlıkta kalıcı ibare:
  **"RESMÎ BELGE DEĞİLDİR — TAHMİNÎ HESAPTIR"**. `.udf` üretimi bilinçli
  olarak kapsam dışı (resmî belgeyle karışma riski).
- Ek bölümler: mahsup tablosu, hesap dökümü, dayanak maddeler,
  "değerlendirilmeyen hususlar" şerhi (disiplin, içtima, adli para çevirme).
- Sınır: çok cezalı/içtimalı dosyada araç hesap üretmez,
  "içtima desteği Faz 8'te" uyarısı döndürür.
- Kullanım amacı README'ye yazılır: avukatın iç çalışması, müvekkil
  bilgilendirmesi ve savcılık müddetnamesini **kontrol** aracı.

---

## 8. Fazlar

### Faz 0 — MacBook ortamı (~15 dk)
```bash
brew install uv
npm install -g @anthropic-ai/claude-code   # kurulu değilse
mkdir infaz-mcp && cd infaz-mcp && git init
uv init --package . && uv add fastmcp pydantic python-dateutil pyyaml
uv add --dev pytest
```
İsteğe bağlı: `/plugin install superpowers` (TDD ve sistematik debugging
skill'leri Faz 2 ve 5'te kullanılacak; brainstorm/plan skill'leri atlanır —
plan bu dokümandır).

### Faz 1 — Kural seti (~1 gün)
- 5275 tam metnini chunk'lı indirip **geçici md. 6, 9, 10, 11 birebir
  metinlerini** çıkar; Bölüm 6 tablolarıyla karşılaştır, fark varsa
  Bölüm 6'yı değil METNİ esas al ve CHANGELOG'a yaz.
- `oranlar.yaml`, `ds_kurallari.yaml`, `suc_kategori_map.yaml` üret
  (yürürlük aralıklı; geçici 6 ve geçici 10 istisna listeleri ayrı).
- YAML şema doğrulama testleri. Kabul: `uv run pytest` yeşil.

### Faz 2 — Hesap motoru, TDD ile (~1 gün)
- Önce golden test, sonra kod (RED-GREEN-REFACTOR).
- `dates.py` TCK 61/6 sözleşmesi; UYAP teyidi için Yargıtay taraması
  (sonuçlar `docs/hesap-yontemi.md`'ye karar künyeleriyle).
- `regime.py` üç katman + lehe çift hesap raporu; `engine.py` akışı;
  `hesap_dokumu` zorunlu.

### Faz 3 — MCP katmanı (~3 saat)
- Araçlar: `infaz_hesapla`, `muddetname_taslagi`, `kural_listesi`
  (sürüm + son doğrulama + yürürlük aralıkları), `kategori_bul`.
- Türkçe, yönlendirici hata mesajları; her sonuçta uyarı + dayanak.

### Faz 4 — Entegrasyon (~30 dk)
```bash
claude mcp add infaz -- uv run --directory /path/to/infaz-mcp \
  python -m infaz_mcp.server
```
Duman testi: "TCK 86/1'den 4 yıl 2 ay, suç tarihi 15.05.2021, infaz
başlangıcı 01.02.2024, 12.01.2023–11.04.2023 tutuklu — hesapla ve
müddetname taslağı çıkar."

### Faz 5 — Ampirik doğrulama (~yarım gün)
- ≥5 senaryo kararara.com / ilme.av.tr ile çapraz; sapmalar
  `hesap_dokumu` üzerinden kök nedene indirilir.
- **Kabul kapısı:** gerçek (anonim) bir müddetname ile birebir eşleşme.

### Faz 6 — Güncellik otomasyonu (~yarım gün, Bölüm 9)

### Faz 7 — Müddetname taslağının PDF çıktısı (isteğe bağlı)

### Faz 8 — Genişletmeler (sıralı)
1. Müebbet türleri → 2. Mükerrirlik (md. 108, 7550 hâli) → 3. İçtima +
107/3 üst sınırları + çok cezalı müddetname → 4. Çocuk hükümlü (107/5) →
5. Açık kuruma ayrılma tarihi (yönetmelik) → 6. md. 105/A-3 istisnaları →
7. md. 110 özel infaz usulleri.

---

## 9. Güncellik ve Bakım (düzenli aralıklarla)

### 9.1 Otomatik izleme — aylık (GitHub Actions cron, her ayın 1'i)
`scripts/guncellik_kontrol.py`:
1. İzlenen kaynakların (**5275 tam metni**, TCK 61, TMK 17, Yönetmelik 2324)
   normalize edilmiş **tam metin** SHA-256 imzasını `kaynak_durumu.json`
   ile karşılaştırır (madde bazlı değil — geçici maddeler ağaçta görünmüyor).
2. Resmî Gazete'de son aydan itibaren `5275`, `infaz`, `koşullu salıverilme`
   geçen değişiklik mevzuatını arar.
3. Fark varsa depoda issue açar (diff özeti + etkilenebilecek `rules/`
   kayıtları); yoksa imza tarihini sessizce günceller.

> Otomasyon değişikliği **tespit eder**, kuralı değiştirmez. Güncelleme
> her zaman insan onaylı PR'dır.

### 9.2 Bayatlık emniyeti — her sorguda
`son_dogrulama` 90 günü aştıysa her sonuçta görünür uyarı; `kural_listesi`
aracı tazeliği Claude içinden raporlar.

### 9.3 İnsan onaylı güncelleme prosedürü
1. Diff'ten etkilenen maddeler belirlenir; yeni metin mevzuat.gov.tr'den okunur.
2. Eski kuralın `yururluk.bitis` tarihi kapatılır, **yeni kural yeni
   aralıkla eklenir** — eski kural silinmez (eski tarihli suçlar için gerekir).
3. `surum` + `son_dogrulama` güncellenir, CHANGELOG'a işlenir.
4. Yeni rejim için ≥2 golden test; eski testler aynen geçmeli.
5. Üç ayda bir 15 dk manuel tur: yargı paketi haberleri + 2 senaryoluk
   piyasa karşılaştırması.

---

## 10. Test Matrisi (golden senaryolar)

| # | Senaryo | Sınanan kural |
|---|---|---|
| 1 | 4 yıl, TCK 86/1, suç tarihi 2024 | Standart: 1/2 + DS 1 yıl + 1/10 şartı |
| 2 | Aynı ceza, suç tarihi 2022 | Geçici 10: DS'den 3 yıl erken (açık kurum + 3 ay şartıyla) |
| 3 | Aynı ceza, suç tarihi 2019 | Geçici 6: DS 3 yıl + Geçici 10 etkileşimi (lehe raporu) |
| 4 | 6 yıl, TCK 81 teşebbüs | 2/3 oranı + kategori eşleme |
| 5 | 10 yıl, TMK kapsamı | 3/4 + geçici 10 istisnası (yararlanamaz) |
| 6 | 12 yıl, TCK 103, suç tarihi 2023 | 2/3 + geçici 10 istisnası (cinsel suç) |
| 7 | İki tutukluluk aralığı (180 gün) | Aralıklı mahsup |
| 8 | Kısa ceza: 7550 1/10 şartı DS'yi geciktiriyor | `max()` alt sınırı |
| 9 | Suç tarihi tam 31.07.2023 ve 30.03.2020 | Eşik sınırları + lehe çift hesap |
| 10 | 5 yıl × 1/2 = 2,5 yıl; 31 Oca + 1 ay | TCK 61/6: ay=30 gün, artık gün atılır |
| 11 | Eşleşmeyen TCK maddesi | Tahmin etmeme, kullanıcıya sorma |
| 12 | Geçersiz girdi (negatif süre, çakışan aralık) | Doğrulama hataları |

---

## 11. Riskler

- **Mevzuat değişkenliği:** Bölüm 9 süreci + tam metin imzası. Kalan risk:
  genelge düzeyi değişiklikler → üç aylık manuel tur.
- **Geçici madde etkileşimi:** Geçici 6 + geçici 10 aynı dosyada
  çakışabilir (öğretide de tartışmalı). Motor tek "doğru" dayatmaz;
  iki hesabı da raporlar (`alternatif_hesap`), kararı avukata bırakır.
- **Hesap yöntemi:** TCK 61/6 yasal çapa; UYAP uygulamasıyla Faz 2'de
  çapraz teyit kabul kapısıdır.
- **Doğruluk sorumluluğu:** Her çıktıda kalıcı tahminîlik uyarısı;
  müddetname taslağında "RESMÎ BELGE DEĞİLDİR" ibaresi.
- **Kapsam sürünmesi:** Faz 8 sırası korunmalı.

---

## 12. MacBook'ta Claude Code Başlangıç Komutu

```
docs/infaz-mcp-plan.md dosyasını oku. Mevcut plan budur; yeniden
brainstorm/plan yapma. Faz 0 ve Faz 1'i uygula: projeyi plandaki yapıyla
kur; 5275'in geçici madde 6, 9, 10, 11 birebir metinlerini mevzuat.gov.tr
tam metninden çıkarıp Bölüm 6 ile karşılaştır (fark varsa metni esas al);
rules/ YAML'larını üret ve şema doğrulama testlerini yaz.
Bitince `uv run pytest` çıktısını ve metin-tablo karşılaştırma raporunu
göster. Faz 2'ye benden onay almadan geçme.
```
