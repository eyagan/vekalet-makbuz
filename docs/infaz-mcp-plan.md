# Ceza İnfaz Hesaplama MCP Sunucusu — Geliştirme Planı (rev. 2)

> Bu doküman, MacBook üzerinde Claude Code ile kodlanacak yerel bir
> "infaz hesaplama" MCP sunucusunun yol haritasıdır. Her faz, Claude Code'a
> doğrudan verilebilecek şekilde somut adımlar içerir.
> Hukuki dayanaklar 5275 sayılı Kanun'un mevzuat.gov.tr'deki güncel
> metninden (Haziran 2026) doğrulanmıştır.
>
> **Rev. 2 değişiklikleri:** Doğruluk stratejisi (Bölüm 4), UYAP/müddetname
> uyumlu veri modeli (Bölüm 5), zaman-bilinçli kural motoru ve düzenli
> güncellik/bakım süreci (Bölüm 8) eklendi.

---

## 1. Hedef ve Kapsam

**Hedef:** 5275 sayılı Ceza ve Güvenlik Tedbirlerinin İnfazı Hakkında Kanun'a
göre, verilen mahkûmiyet bilgilerinden şu tarihleri hesaplayan, Claude
Desktop/Claude Code'a stdio üzerinden bağlanan yerel bir MCP sunucusu:

1. Koşullu salıverilme (KS) tarihi
2. Denetimli serbestlik (DS) tarihi
3. Bihakkın (hak ederek) tahliye tarihi
4. (Faz 7) Açık ceza infaz kurumuna ayrılma tarihi

**MVP kapsamı (Faz 1–5):** Tek süreli hapis cezası, yetişkin hükümlü,
suç tarihine göre rejim seçimi (30.03.2020 eşiği), çoklu tutukluluk
aralıklı mahsup, TCK madde/fıkradan otomatik suç kategorisi eşleme.
**MVP dışı (Faz 7'ye ertelenen):** Birden fazla cezanın içtimaı, çocuk
hükümlü (15 yaş altı gün katlama), müebbet/ağırlaştırılmış müebbet,
0-6 yaş çocuklu kadın hükümlü ve ağır hastalık istisnaları.

**Uyarı (ürüne de yazılacak):** Çıktılar tahminîdir; resmî müddetname
Cumhuriyet savcılığınca düzenlenir. Araç hukuki tavsiye vermez.

---

## 2. Teknoloji Seçimi

| Bileşen | Seçim | Gerekçe |
|---|---|---|
| Dil | Python ≥ 3.12 | FastMCP ekosistemi, pydantic ile şema üretimi |
| Paket yöneticisi | `uv` | Tek araçla venv + bağımlılık + çalıştırma (`uvx`) |
| MCP çatısı | `fastmcp` (v2) | `@mcp.tool` dekoratörüyle otomatik JSON Schema |
| Veri modeli | `pydantic` v2 | Girdi doğrulama + araç şeması |
| Test | `pytest` | Altın (golden) senaryo testleri |
| Transport | stdio | Yerel Claude Desktop/Code için yeterli; HTTP gerekmez |
| Güncellik kontrolü | GitHub Actions (cron) + Python betiği | Bölüm 8'deki otomatik mevzuat izleme |

Kural seti **koddan ayrı**, `rules/` altında YAML olarak tutulacak —
yargı paketi değişikliklerinde kod değil veri güncellenecek.

---

## 3. Proje Yapısı

Yeni ve bağımsız bir depo olarak açılacak (`infaz-mcp`):

```
infaz-mcp/
├── pyproject.toml
├── README.md
├── src/infaz_mcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP araç tanımları (ince katman)
│   ├── engine.py          # Saf hesaplama motoru (MCP'den bağımsız)
│   ├── models.py          # Pydantic girdi/çıktı modelleri
│   ├── regime.py          # Zaman-bilinçli rejim seçici + lehe karşılaştırma
│   ├── kategori.py        # TCK madde/fıkra → suç kategorisi eşleyici
│   └── dates.py           # Takvim aritmetiği (ay/yıl ekleme, mahsup)
├── rules/
│   ├── oranlar.yaml           # TÜM rejimler, yürürlük aralıklarıyla (Bölüm 6)
│   ├── suc_kategori_map.yaml  # TCK madde/fıkra → kategori tablosu
│   ├── CHANGELOG.md           # Her kural güncellemesinin kaydı
│   └── kaynak_durumu.json     # İzlenen mevzuatın son doğrulama imzaları
├── scripts/
│   └── guncellik_kontrol.py   # Mevzuat değişiklik dedektörü (Bölüm 8)
├── .github/workflows/
│   └── guncellik.yml          # Aylık cron → değişiklikte issue açar
└── tests/
    ├── test_engine.py
    ├── test_kategori.py
    └── golden/            # Doğrulanmış örnek senaryolar (JSON)
```

Tasarım ilkesi: `engine.py` MCP'yi hiç bilmez → birim testleri saniyeler
içinde koşar; `server.py` sadece sarmalayıcıdır.

---

## 4. Doğruluk Stratejisi — "en doğru hesap" neye göre?

Doğruluğun ölçütü **UYAP'ın ürettiği resmî müddetnamedir**; araç ona
yakınsamayı hedefler. Bunun için dört katmanlı bir doğruluk hiyerarşisi
uygulanır — alttaki katman üsttekiyle çelişirse üstteki kazanır:

1. **Kanun metni (birincil):** 5275 md. 105/A, 107, 108, geçici md. 6;
   TMK md. 17. Tek kaynak: mevzuat.gov.tr güncel metni. Kurallar YAML'a
   madde/fıkra `dayanak` alanıyla işlenir.
2. **İkincil mevzuat:** Açık Ceza İnfaz Kurumlarına Ayrılma Yönetmeliği,
   Denetimli Serbestlik Hizmetleri Yönetmeliği, Adalet Bakanlığı CTE
   genelgeleri (özellikle hesap yöntemi ve açık kuruma ayrılma süreleri).
3. **İçtihat:** Hesap *yöntemine* dair Yargıtay/CGK kararları —
   özellikle ay/yıl hesabının takvim esasıyla yapılması, oranın ceza
   süresine uygulanma biçimi, lehe kanun değerlendirmesi. Geliştirme
   sırasında bu kararlar Bedesten/Yargıtay karar arama üzerinden taranıp
   golden testlere gerekçesiyle işlenir.
4. **Ampirik doğrulama:** Gerçek (anonimleştirilmiş) müddetname örnekleri
   nihai golden testlerdir. Piyasa hesaplayıcıları (kararara.com,
   ilme.av.tr) yalnızca çapraz kontrol içindir; ground truth sayılmaz.

**Hesap yöntemi sözleşmesi (engine.py'de sabitlenecek):**
- Yıl/ay eklemeleri **takvim esaslı** yapılır (`relativedelta`); ceza
  süresi güne çevrilmez. Oran uygulaması süre cinsinden yapılır
  (örn. 5 yıl × 1/2 = 2 yıl 6 ay), kalan kesirler güne dönüştürülürken
  ay = 30 gün kabulü ancak içtihatla doğrulanırsa kullanılır — bu kabul
  Faz 2'de Yargıtay kararlarıyla teyit edilmeden kodlanmaz.
- Mahsup, tutukluluk **aralıklarından** gün olarak hesaplanır ve tarih
  eklemelerinden sonra düşülür; aralıklar çakışma kontrolünden geçer.
- Her sonuç, kullanılan kural sürümünü, dayanak maddeleri ve hesap
  adımlarının dökümünü (`hesap_dokumu`) içerir — böylece bir sapma
  bulunduğunda hangi adımın yanlış olduğu görülebilir.

**Doğruluğu artıran girdi tasarımı:** Kullanıcıdan "suç kategorisi"
seçmesi istenmez; **TCK madde + fıkra** alınır ve `suc_kategori_map.yaml`
ile kategoriye otomatik eşlenir (örn. `TCK 188/3` → uyuşturucu ticareti).
Eşleşme bulunamazsa araç tahmin etmez; olası kategorileri ve dayanaklarını
listeleyip kullanıcıya sorar. Yanlış kategori = yanlış oran olduğundan,
en büyük hata kaynağı bu tasarımla kapatılır.

---

## 5. Veri Modeli (UYAP müddetname girdileriyle hizalı)

`InfazGirdisi` (pydantic):

| Alan | Tip | Not |
|---|---|---|
| `ceza_yil / ceza_ay / ceza_gun` | int | Kesinleşmiş toplam ceza, ayrı alanlar |
| `tck_madde`, `tck_fikra` | str | Kategori eşleme için; serbest metin değil |
| `suc_tarihi` | date | Rejim seçiminin anahtarı |
| `kesinlesme_tarihi` | date? | Lehe değerlendirme ve mükerrirlik için |
| `infaz_baslangici` | date | Cezaevine giriş / infazın başladığı tarih |
| `tutukluluk_araliklari` | list[(date, date)] | Mahsup; çoklu aralık desteklenir |
| `dogum_tarihi` | date? | Çocuk hükümlü kuralları (Faz 7) için şimdiden alınır |
| `mukerrir` | bool | md. 108 (Faz 7'de oran etkisi) |
| `orgut_kapsaminda` | bool | md. 107/4 |
| `terör_kapsaminda` | bool | TMK 17 |

`InfazSonucu`: KS / DS / bihakkın tarihleri + `uygulanan_rejim`,
`dayanaklar[]`, `hesap_dokumu[]`, `kural_surumu`, `son_dogrulama_tarihi`,
`uyari` (tahminîlik + kural seti 90 günden eskiyse bayatlık uyarısı).

---

## 6. Zaman-Bilinçli Kural Motoru

İnfaz hukukunda doğru sonuç, **suç tarihinde hangi kuralın yürürlükte
olduğunu ve lehe kanunu** bilmeyi gerektirir. Bu yüzden `oranlar.yaml`
rejim dosyalarına bölünmez; her kural kendi yürürlük aralığını taşır:

```yaml
surum: "2026-06"
son_dogrulama: 2026-06-11
kurallar:
  - kategori: genel
    oran: 1/2
    dayanak: "5275 md. 107/2 (7242 ile değişik)"
    yururluk: { suc_tarihi_baslangic: 2020-03-30, bitis: null }
  - kategori: genel
    oran: 1/2
    ds_suresi_yil: 3
    dayanak: "5275 geçici md. 6"
    yururluk: { suc_tarihi_baslangic: null, bitis: 2020-03-29 }
  - kategori: kasten_oldurme
    oran: 2/3
    dayanak: "5275 md. 107/2-a"
    yururluk: { suc_tarihi_baslangic: 2020-03-30, bitis: null }
  # ... 107/2 a-h listesi, örgütlü (107/4), terör (TMK 17),
  #     müebbet sabitleri, çoklu mahkûmiyet üst sınırları
```

`regime.py` davranışı:
1. Suç tarihine göre yürürlükteki kural(lar)ı seçer.
2. Birden fazla rejim uygulanabilir görünüyorsa (geçiş hükümleri),
   **her iki rejimde de hesaplar**, lehe olanı uygular ve sonuçta iki
   hesabı birden raporlar (`alternatif_hesap` alanı) — kullanıcı hâkim
   değerlendirmesine girecek belirsizliği görür.
3. Hiçbir kural eşleşmezse hata döndürür; asla "en yakın" kuralı uygulamaz.

Doğrulanmış oran çekirdeği (mevzuat.gov.tr, Haziran 2026 — 5275 md. 107):
genel 1/2 · md. 107/2 a-h listesi 2/3 (kasten öldürme 81-83; 87/2-d;
işkence/eziyet 94-96; cinsel suçlar 102*, 104*, 105; çocuklarda cinsel
suçlar ve uyuşturucu ticareti; özel hayat 132-138; casusluk 326-339) ·
örgütlü 2/3 (müebbet 30, ağırlaştırılmış müebbet 36 yıl) · terör 3/4
(TMK 17) · müebbet 24 / ağırlaştırılmış müebbet 30 yıl · çoklu mahkûmiyet
üst sınırları 28/30/36 (örgütlüde 32/34/40) · 15 yaş altı 1 gün = 2 gün ·
DS: KS'ye 1 yıl kala (md. 105/A), 30.03.2020 öncesi suçta 3 yıl (geçici md. 6).

---

## 7. Fazlar

### Faz 0 — MacBook ortam kurulumu (~15 dk)
```bash
brew install uv
npm install -g @anthropic-ai/claude-code   # kurulu değilse
mkdir infaz-mcp && cd infaz-mcp && git init
uv init --package . && uv add fastmcp pydantic python-dateutil pyyaml
uv add --dev pytest
```

### Faz 1 — Kural seti ve kategori eşleme (~yarım gün)
- Bölüm 6'daki şemayla `rules/oranlar.yaml` üret (yürürlük aralıklı).
- `rules/suc_kategori_map.yaml`: md. 107/2 a-h'deki TCK madde/fıkraları
  kategorilere eşle; TMK kapsamı ve örgüt bayrakları ayrı alan.
- YAML şemasını doğrulayan pydantic modeli + testi.
- `rules/CHANGELOG.md`'ye ilk kayıt: kaynak, tarih, doğrulayan.

### Faz 2 — Hesap yöntemi teyidi + motor (~1 gün)
- Önce: ay/yıl hesabının takvim esası ve kesir çevrimi için Yargıtay
  kararı taraması (Bedesten/karararama); bulgular `docs/hesap-yontemi.md`'ye
  kararlarıyla işlenir. **Yöntem teyit edilmeden kod yazılmaz.**
- `models.py` (Bölüm 5), `kategori.py`, `regime.py`, `engine.py`,
  `dates.py` implementasyonu; `hesap_dokumu` zorunlu.
- `tests/golden/`: Bölüm 9 matrisi. Kabul: `uv run pytest` yeşil.

### Faz 3 — MCP katmanı (~2 saat)
- `server.py` araçları: `infaz_hesapla`, `kural_listesi` (yüklü kural
  sürümü, son doğrulama tarihi, yürürlük aralıkları), `kategori_bul`
  (TCK madde/fıkradan kategori önizleme).
- Türkçe, yönlendirici hata mesajları; her sonuçta uyarı + dayanak.

### Faz 4 — Claude Code/Desktop entegrasyonu (~30 dk)
```bash
claude mcp add infaz -- uv run --directory /path/to/infaz-mcp \
  python -m infaz_mcp.server
```
- Duman testi: "TCK 86/1'den 4 yıl 2 ay, suç tarihi 15.05.2021, infaz
  başlangıcı 01.02.2024, 12.01.2023–11.04.2023 tutuklu — hesapla."

### Faz 5 — Ampirik doğrulama (~yarım gün)
- En az 5 senaryo kararara.com / ilme.av.tr ile çapraz kontrol; her sapma
  `hesap_dokumu` üzerinden kök nedene indirilir, sonuç golden teste işlenir.
- Mümkünse gerçek (anonimleştirilmiş) müddetname ile birebir karşılaştırma —
  MVP'nin kabul ölçütü budur.

### Faz 6 — Güncellik otomasyonu (~yarım gün, Bölüm 8)
- `scripts/guncellik_kontrol.py` + `.github/workflows/guncellik.yml`.
- İlk çalıştırma `rules/kaynak_durumu.json` imzalarını üretir.

### Faz 7 — Genişletmeler (isteğe bağlı, sıralı)
1. Müebbet / ağırlaştırılmış müebbet sabit süreleri
2. Mükerrirlik (md. 108) oran yükseltmesi
3. Birden fazla cezanın içtimaı ve 107/3 üst sınırları
4. Çocuk hükümlü: 15 yaş altı gün katlama (107/5)
5. Açık kuruma ayrılma tarihi (yönetmelik kurallaştırılarak)
6. Kadın hükümlü (0-6 yaş çocuk) ve ağır hastalık DS istisnaları

---

## 8. Güncellik ve Bakım Süreci (düzenli aralıklarla)

İnfaz değişkenlerinin güncel kalması üç mekanizmaya bağlanır:

### 8.1 Otomatik izleme — aylık
`scripts/guncellik_kontrol.py`, GitHub Actions cron'uyla **ayda bir**
(her ayın 1'i) koşar ve şunları yapar:

1. İzlenen kaynakların (5275, TMK, ilgili yönetmelikler) mevzuat.gov.tr
   üzerindeki güncel metnini çeker, normalize edip SHA-256 imzasını
   `rules/kaynak_durumu.json`'daki son imzayla karşılaştırır.
2. Resmî Gazete'de son aydan itibaren `5275`, `infaz`, `koşullu
   salıverilme` geçen değişiklik mevzuatını arar.
3. Fark bulursa depoda **issue açar**: hangi kaynak değişti, diff özeti,
   etkilenebilecek `rules/` kayıtları. Fark yoksa sessizce imza tarihini
   günceller.

> Not: Otomasyon değişikliği **tespit eder**, kuralı kendisi değiştirmez.
> Oran/sürelerin güncellenmesi her zaman insan onaylı bir PR'dır
> (aşağıdaki 8.3 prosedürü) — yanlış otomatik güncelleme, bayat kuraldan
> daha tehlikelidir.

### 8.2 Bayatlık emniyeti — her sorguda
- `oranlar.yaml` içindeki `son_dogrulama` tarihi **90 günü** aşmışsa her
  hesap sonucuna görünür uyarı eklenir: "Kural seti en son …'de
  doğrulandı; güncel mevzuatla teyit edin."
- `kural_listesi` aracı sürüm + son doğrulama + izleme durumunu gösterir,
  böylece Claude içinden tek soruyla tazelik denetlenir.

### 8.3 İnsan onaylı güncelleme prosedürü — değişiklik tespitinde
1. Issue'daki diff'ten etkilenen maddeler belirlenir; mevzuat.gov.tr'den
   yeni metin okunur (gerekirse Claude Code + yargi/mevzuat-mcp ile).
2. `rules/oranlar.yaml`'da eski kuralın `yururluk.bitis` tarihi kapatılır,
   **yeni kural yeni yürürlük aralığıyla eklenir** — eski kural silinmez
   (eski tarihli suçlar için hâlâ gereklidir).
3. `surum` ve `son_dogrulama` güncellenir, `CHANGELOG.md`'ye kayıt düşülür.
4. Yeni rejim için en az 2 golden test eklenir; eski testler aynen geçmeli
   (geriye dönük hesaplar değişmemeli). `uv run pytest` yeşilse PR merge.
5. Üç ayda bir (cron bulgusuz da olsa) 15 dakikalık manuel tur: yeni yargı
   paketi haberleri + piyasa hesaplayıcılarıyla 2 senaryoluk karşılaştırma.

---

## 9. Test Matrisi (golden senaryolar)

| # | Senaryo | Sınanan kural |
|---|---|---|
| 1 | 4 yıl hapis, adli suç (TCK 86/1), suç tarihi 2022 | 1/2 oranı, DS 1 yıl |
| 2 | Aynı ceza, suç tarihi 2019 | geçici md. 6: 1/2 + DS 3 yıl |
| 3 | 6 yıl, kasten öldürmeye teşebbüs (TCK 81) | 2/3 oranı + kategori eşleme |
| 4 | 10 yıl, TMK kapsamı | 3/4 oranı |
| 5 | İki tutukluluk aralığı (toplam 180 gün) | aralıklı mahsup |
| 6 | DS tarihi infaz başlangıcından önce çıkan kısa ceza | alt sınır kuralı |
| 7 | Ay sonu taşması (31 Oca + 1 ay) ve kesirli oran (5 yıl × 1/2) | takvim aritmetiği |
| 8 | Suç tarihi tam 30.03.2020 sınırında | rejim sınırı + lehe çift hesap raporu |
| 9 | Eşleşmeyen TCK maddesi | tahmin etmeme, kullanıcıya sorma |
| 10 | Geçersiz girdi (negatif süre, çakışan tutukluluk aralığı) | doğrulama hataları |

---

## 10. Riskler

- **Mevzuat değişkenliği:** Bölüm 8 süreciyle yönetilir; kalan risk,
  cron'un yakalayamadığı genelge düzeyi değişikliklerdir → üç aylık
  manuel tur bunun için vardır.
- **Hesap yöntemi belirsizliği:** Kanun oranı söyler, *yöntemi* içtihat
  belirler. Faz 2'deki yöntem teyidi atlanamaz (kabul kapısıdır).
- **Doğruluk sorumluluğu:** Araç şahsi araştırma/ön değerlendirme içindir;
  her çıktıda kalıcı uyarı metni bulunur.
- **Kapsam sürünmesi:** İnfaz erteleme, disiplin/hücre, özel infaz usulleri
  MVP dışıdır; Faz 7 sırası korunmalı.

---

## 11. MacBook'ta Claude Code Başlangıç Komutu

Depo klonlandıktan sonra Claude Code'a verilecek ilk prompt:

```
docs/infaz-mcp-plan.md dosyasını oku. Faz 0 ve Faz 1'i uygula:
infaz-mcp projesini plandaki yapıyla oluştur; rules/oranlar.yaml'ı
Bölüm 6'daki şema ve doğrulanmış oran çekirdeğiyle, suc_kategori_map.yaml'ı
md. 107/2 a-h listesiyle üret; YAML doğrulama testini yaz.
Bitince `uv run pytest` çıktısını göster. Faz 2'ye benden onay almadan geçme.
```
