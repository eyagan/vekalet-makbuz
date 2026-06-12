# infaz-mcp

5275 sayılı Ceza ve Güvenlik Tedbirlerinin İnfazı Hakkında Kanun'a göre
koşullu salıverilme, denetimli serbestlik ve bihakkın tahliye tarihlerini
hesaplayan yerel MCP sunucusu.

> ⚠️ **Çıktılar tahminîdir ve hukuki tavsiye değildir.** Resmî müddetname
> Cumhuriyet savcılığınca düzenlenir. Bu araç avukatın iç çalışması,
> müvekkil bilgilendirmesi ve savcılık müddetnamesinin kontrolü içindir.

Yol haritası ve hukuki dayanak dokümanı: `../docs/infaz-mcp-plan.md`

## Durum

- [x] Faz 1 — Kural seti (`rules/*.yaml`) + şema doğrulama testleri
- [x] Faz 2 — Hesap motoru (`engine.py` + `regime`/`kategori`/`dates`) + golden testler
- [x] Faz 3 — MCP katmanı: `infaz_hesapla`, `muddetname_taslagi`, `kategori_bul`, `kural_listesi`
- [ ] Faz 4 — Claude Code/Desktop entegrasyonu (aşağıdaki komut)
- [ ] Faz 5 — Ampirik doğrulama (gerçek müddetname ile birebir — kabul kapısı)
- [ ] Faz 6+ — Güncellik otomasyonu, Faz 8 genişletmeleri (içtima, müebbet, mükerrirlik)

## Geliştirme

```bash
uv sync          # veya: pip install fastmcp pydantic pyyaml pytest python-dateutil
uv run pytest    # 41 test
```

## Claude Code'a ekleme (yerel MCP, stdio)

```bash
claude mcp add infaz -- uv run --directory /MUTLAK/YOL/infaz-mcp python -m infaz_mcp.server
```

Claude Desktop için `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "infaz": {
      "command": "uv",
      "args": ["run", "--directory", "/MUTLAK/YOL/infaz-mcp", "python", "-m", "infaz_mcp.server"]
    }
  }
}
```

## Araçlar

| Araç | İşlev |
|---|---|
| `infaz_hesapla` | KS / DS / bihakkın tarihleri + hesap dökümü + dayanaklar |
| `muddetname_taslagi` | Sonucu müddetname düzeninde Markdown belge (RESMÎ BELGE DEĞİLDİR) |
| `kategori_bul` | TCK madde/fıkradan kategori + oran önizlemesi |
| `kural_listesi` | Kural sürümü, son doğrulama, bayatlık denetimi |

## Yöntem notu (avukat için)

İnfaz hesabında süre, TCK 61/6 uyarınca **1 yıl = 365, 1 ay = 30 gün** sayılarak
güne çevrilir; KS oranı uygulanırken kesirli gün atılır (hükümlü lehine). Bir
tarihe gün eklenirken gerçek takvim kullanılır. Bu sözleşme `dates.py` içinde
tek yerde toplanmıştır ve **gerçek bir müddetname ile birebir doğrulama (Faz 5)
yapılana kadar geçicidir**. Her sonuç adım adım `hesap_dokumu` döker; bir sapma
bulunduğunda hangi adımdan kaynaklandığı görülür.
