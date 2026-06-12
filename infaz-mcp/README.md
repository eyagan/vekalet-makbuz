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
- [ ] Faz 2 — Hesap motoru (TDD)
- [ ] Faz 3 — MCP katmanı (`infaz_hesapla`, `muddetname_taslagi`, ...)
- [ ] Faz 4+ — Entegrasyon, ampirik doğrulama, güncellik otomasyonu

## Geliştirme

```bash
uv sync          # veya: pip install pydantic pyyaml pytest
uv run pytest    # veya: python3 -m pytest
```
