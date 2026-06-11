# Ceza İnfaz Hesaplama MCP Sunucusu — Geliştirme Planı

> Bu doküman, MacBook üzerinde Claude Code ile kodlanacak yerel bir
> "infaz hesaplama" MCP sunucusunun yol haritasıdır. Her faz, Claude Code'a
> doğrudan verilebilecek şekilde somut adımlar içerir.
> Hukuki dayanaklar 5275 sayılı Kanun'un mevzuat.gov.tr'deki güncel
> metninden (Haziran 2026) doğrulanmıştır.

---

## 1. Hedef ve Kapsam

**Hedef:** 5275 sayılı Ceza ve Güvenlik Tedbirlerinin İnfazı Hakkında Kanun'a
göre, verilen mahkûmiyet bilgilerinden şu tarihleri hesaplayan, Claude
Desktop/Claude Code'a stdio üzerinden bağlanan yerel bir MCP sunucusu:

1. Koşullu salıverilme (KS) tarihi
2. Denetimli serbestlik (DS) tarihi
3. Bihakkın (hak ederek) tahliye tarihi
4. (Faz 6) Açık ceza infaz kurumuna ayrılma tarihi

**MVP kapsamı (Faz 1–4):** Tek süreli hapis cezası, yetişkin hükümlü,
suç tarihine göre rejim seçimi (30.03.2020 eşiği), mahsup.
**MVP dışı (Faz 6'ya ertelenen):** Birden fazla cezanın içtimaı, çocuk
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
│   ├── regime.py          # Suç tarihine göre rejim seçici
│   └── dates.py           # Takvim aritmetiği (ay/yıl ekleme, mahsup)
├── rules/
│   ├── oranlar_7242.yaml      # 30.03.2020 ve sonrası rejimi
│   └── oranlar_gecici6.yaml   # 30.03.2020 öncesi (geçici md. 6) rejimi
└── tests/
    ├── test_engine.py
    └── golden/            # Doğrulanmış örnek senaryolar (JSON)
```

Tasarım ilkesi: `engine.py` MCP'yi hiç bilmez → birim testleri saniyeler
içinde koşar; `server.py` sadece sarmalayıcıdır.

---

## 4. Hukuki Kural Seti (kanun metninden doğrulanmış)

### 4.1 Koşullu salıverilme oranları — 5275 md. 107 (7242 sonrası)

| Kategori | Eşik |
|---|---|
| Genel kural (süreli hapis) | 1/2 |
| md. 107/2 a–h listesi: kasten öldürme (TCK 81-83), neticesi sebebiyle ağırlaşmış yaralama (87/2-d), işkence/eziyet (94-96), cinsel saldırı/reşit olmayanla ilişki/taciz (102*, 104*, 105), çocukların cinsel suçları ve uyuşturucu ticareti (çocuk hükümlü), özel hayata karşı suçlar (132-138), devlet sırları/casusluk (326-339) | 2/3 |
| Örgütlü suçlar (md. 107/4) | 2/3 (müebbet 30 yıl, ağırlaştırılmış müebbet 36 yıl) |
| Terör suçları (TMK md. 17) | 3/4 |
| Mükerrirler (md. 108) | bir üst oran kuralı — Faz 6'da ayrıntılandırılacak |
| Müebbet / ağırlaştırılmış müebbet | sabit 24 / 30 yıl |
| Çoklu mahkûmiyet üst sınırları (107/3) | 28 / 30 / 36 yıl (örgütlüde 32 / 34 / 40) |
| 15 yaşını dolduruncaya kadar kurumda geçen her gün (107/5) | 2 gün sayılır |

### 4.2 Denetimli serbestlik — md. 105/A ve geçici md. 6

- Genel kural: açık kurumdaki iyi hâlli hükümlü, **KS tarihine 1 yıl veya
  daha az** kala DS'ye ayrılabilir.
- **Suç tarihi 30.03.2020'den önce** ise geçici md. 6 uygulanır:
  DS süresi **3 yıl**, genel KS oranı **1/2** (istisna listesi farklı).
  Rejim seçici (`regime.py`) bu ayrımı suç tarihinden otomatik yapar.

### 4.3 Hesap sırası (engine.py akışı)

```
girdi → rejim seç (suç tarihi) → oran tablosundan eşik bul
      → bihakkın = infaz_başlangıcı + ceza süresi (takvim bazlı) − mahsup
      → KS = infaz_başlangıcı + ceza × oran − mahsup
      → DS = KS − (1 yıl | 3 yıl)   [infaz başlangıcından önce olamaz]
      → yapılandırılmış çıktı + dayanak maddeler + uyarı metni
```

Tarih aritmetiği kuralı: yıl/ay eklemeleri takvim bazlı yapılır
(`dateutil.relativedelta`), gün eklemeleri ve mahsup gün bazlı düşülür.

---

## 5. Fazlar

### Faz 0 — MacBook ortam kurulumu (~15 dk)
```bash
# Homebrew varsa:
brew install uv
# Claude Code kurulu değilse:
npm install -g @anthropic-ai/claude-code
mkdir infaz-mcp && cd infaz-mcp && git init
uv init --package . && uv add fastmcp pydantic python-dateutil
uv add --dev pytest
```

### Faz 1 — Kural setini YAML'a dökme (~1 saat)
- Bölüm 4'teki tabloları `rules/*.yaml` dosyalarına aktar.
- Her kurala `dayanak` alanı ekle (ör. `"5275 md. 107/2"`), çıktıda gösterilecek.
- Kabul ölçütü: YAML şemasını doğrulayan bir pydantic modeli ve testi.

### Faz 2 — Hesaplama motoru (~yarım gün)
- `models.py`: `InfazGirdisi` (ceza_yil/ay/gun, suc_kategorisi enum,
  suc_tarihi, infaz_baslangici, mahsup_gun, mukerrir) ve `InfazSonucu`.
- `regime.py`: suç tarihi → rejim; `engine.py`: Bölüm 4.3 akışı.
- `tests/golden/`: en az 8 senaryo (aşağıdaki test matrisi).
- Kabul ölçütü: `uv run pytest` yeşil.

### Faz 3 — MCP katmanı (~2 saat)
- `server.py`: tek araç `infaz_hesapla`; ayrıca `kural_listesi` adında
  ücretsiz bir bilgi aracı (hangi rejim/oranların yüklü olduğunu döker).
- Hata mesajları Türkçe ve yönlendirici olmalı
  (ör. geçersiz suç kategorisinde geçerli enum listesini döndür).
- Her sonuca `uyari` ve `dayanak` alanları eklenir.

### Faz 4 — Claude Code/Desktop entegrasyonu (~30 dk)
```bash
# Claude Code (proje içinden):
claude mcp add infaz -- uv run --directory /path/to/infaz-mcp \
  python -m infaz_mcp.server
```
- Claude Desktop için `claude_desktop_config.json`'a aynı komut yazılır.
- Duman testi: "TCK 86 kasten yaralamadan 4 yıl 2 ay ceza, suç tarihi
  15.05.2021, infaza 01.02.2024'te başlandı, 90 gün tutuklu kaldı —
  tarihleri hesapla" → aracın çağrıldığını ve tarihlerin döndüğünü doğrula.

### Faz 5 — Doğrulama (~yarım gün)
- En az 5 senaryoyu piyasadaki güncel hesaplayıcılarla
  (kararara.com, ilme.av.tr) çapraz karşılaştır; sapmaları kök nedenine
  kadar incele ve golden testlere işle.
- Mümkünse gerçek (anonimleştirilmiş) bir müddetname ile karşılaştır.

### Faz 6 — Genişletmeler (isteğe bağlı, sıralı)
1. Müebbet / ağırlaştırılmış müebbet sabit süreleri
2. Mükerrirlik (md. 108) oran yükseltmesi
3. Birden fazla cezanın içtimaı ve 107/3 üst sınırları
4. Çocuk hükümlü: 15 yaş altı gün katlama (107/5)
5. Açık kuruma ayrılma tarihi (Açık Ceza İnfaz Kurumlarına Ayrılma
   Yönetmeliği — önce yönetmeliğin güncel metni çekilip kurallaştırılacak)
6. Kadın hükümlü (0-6 yaş çocuk) ve ağır hastalık DS istisnaları

---

## 6. Test Matrisi (golden senaryolar)

| # | Senaryo | Sınanan kural |
|---|---|---|
| 1 | 4 yıl hapis, adli suç, suç tarihi 2022 | 1/2 oranı, DS 1 yıl |
| 2 | Aynı ceza, suç tarihi 2019 | geçici md. 6: 1/2 + DS 3 yıl |
| 3 | 6 yıl, kasten öldürmeye teşebbüs (107/2-a) | 2/3 oranı |
| 4 | 10 yıl, TMK kapsamı | 3/4 oranı |
| 5 | Mahsup: 180 gün tutukluluk | tüm tarihlerden düşme |
| 6 | DS tarihi infaz başlangıcından önce çıkan kısa ceza | alt sınır kuralı |
| 7 | Ay sonu taşması (31 Oca + 1 ay) | takvim aritmetiği |
| 8 | Geçersiz girdi (negatif süre, bilinmeyen kategori) | hata mesajları |

---

## 7. Riskler ve Sürdürme

- **Mevzuat değişkenliği:** Her yargı paketi oranları değiştirebilir
  (en son 11. paket). `rules/*.yaml` + `dayanak` alanı sayesinde güncelleme
  kod değişikliği gerektirmez. Sürüm notu olarak YAML'a `gecerlilik_tarihi`
  alanı konacak ve çıktıda gösterilecek.
- **Doğruluk sorumluluğu:** Araç yalnızca şahsi araştırma/ön değerlendirme
  içindir; her çıktıda kalıcı uyarı metni bulunur.
- **Kapsam sürünmesi:** İnfaz hukukunun tüm istisnalarını (infaz erteleme,
  hücre cezası, disiplin) MVP'ye almayın — Faz 6 sırası korunmalı.

---

## 8. MacBook'ta Claude Code Başlangıç Komutu

Depo klonlandıktan sonra Claude Code'a verilecek ilk prompt:

```
docs/infaz-mcp-plan.md dosyasını oku. Faz 0 ve Faz 1'i uygula:
infaz-mcp projesini planda belirtilen yapıyla oluştur, kural YAML'larını
plandaki tablolardan üret ve pydantic doğrulama testini yaz.
Bitince `uv run pytest` çıktısını göster. Faz 2'ye benden onay almadan geçme.
```
