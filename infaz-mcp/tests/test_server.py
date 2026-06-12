"""MCP sunucu katmanı duman testi. fastmcp kurulu değilse atlanır
(motor testleri fastmcp gerektirmez)."""

import pytest

pytest.importorskip("fastmcp")

from infaz_mcp import server  # noqa: E402


def _call(f, **kw):
    return f.fn(**kw) if hasattr(f, "fn") else f(**kw)


def test_infaz_hesapla_basit():
    r = _call(
        server.infaz_hesapla,
        tck_madde="86/1", ceza_yil=4, suc_tarihi="2024-01-01",
        infaz_baslangici="2024-06-01",
    )
    assert r["uygulanan_oran"] == "1/2"
    assert "kosullu_saliverilme" in r


def test_infaz_hesapla_kategori_hatasi():
    r = _call(server.infaz_hesapla, tck_madde="999", ceza_yil=2,
              suc_tarihi="2024-01-01", infaz_baslangici="2024-01-01")
    assert r["hata"] == "kategori_bulunamadi"
    assert "olasi_maddeler" in r


def test_kategori_bul_188_yetiskin():
    r = _call(server.kategori_bul, tck_madde="188")
    assert r["ks_kategori"] == "m108_9_listesi"


def test_kural_listesi_alanlari():
    r = _call(server.kural_listesi)
    assert r["surum"]
    assert "bayat_mi" in r and "gecen_gun" in r


def test_muddetname_taslagi_uyari_basligi():
    m = _call(server.muddetname_taslagi, tck_madde="158", ceza_yil=6,
              suc_tarihi="2022-03-01", infaz_baslangici="2024-01-01")
    assert "RESMÎ BELGE DEĞİLDİR" in m
