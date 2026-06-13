"""Faz 1 kabul testleri: kural YAML'ları şemaya uyuyor ve kanun metniyle
doğrulanmış kritik değerleri taşıyor mu?

Beklenen değerlerin kaynağı: 5275 tam metni (mevzuat.gov.tr, 12.06.2026) —
bkz. docs/infaz-mcp-plan.md Bölüm 6.
"""

from datetime import date
from fractions import Fraction

import pytest

from infaz_mcp.models import (
    ds_kurallari_yukle,
    kategori_map_yukle,
    oranlar_yukle,
)


@pytest.fixture(scope="module")
def oranlar():
    return oranlar_yukle()


@pytest.fixture(scope="module")
def ds():
    return ds_kurallari_yukle()


@pytest.fixture(scope="module")
def kmap():
    return kategori_map_yukle()


# --- oranlar.yaml ---


def test_genel_oran_yarim(oranlar):
    o = oranlar.oran_bul("genel", date(2024, 1, 1))
    assert o.kesir == Fraction(1, 2)
    assert "107" in o.dayanak


def test_m107_2_listesi_ucte_iki(oranlar):
    assert oranlar.oran_bul("m107_2_listesi", date(2024, 1, 1)).kesir == Fraction(2, 3)


def test_teror_dortte_uc(oranlar):
    o = oranlar.oran_bul("teror", date(2024, 1, 1))
    assert o.kesir == Fraction(3, 4)
    assert "3713" in o.dayanak


def test_m108_9_tarih_esigi(oranlar):
    """TCK 102/2, 103, 104/2-3, 188: 28.06.2014 öncesi 2/3, sonrası 3/4
    (md. 108/9 + geçici md. 9/4)."""
    assert oranlar.oran_bul("m108_9_listesi", date(2014, 6, 27)).kesir == Fraction(2, 3)
    assert oranlar.oran_bul("m108_9_listesi", date(2014, 6, 28)).kesir == Fraction(3, 4)
    assert oranlar.oran_bul("m108_9_listesi", date(2024, 1, 1)).kesir == Fraction(3, 4)


def test_sabit_sureler(oranlar):
    s = oranlar.sabit_sureler_yil
    assert s["muebbet"] == 24
    assert s["agirlastirilmis_muebbet"] == 30
    assert s["orgutlu_agirlastirilmis_muebbet"] == 36
    assert s["mukerrir_muebbet"] == 33


def test_coklu_ust_sinirlar(oranlar):
    g = oranlar.coklu_mahkumiyet_ust_sinirlari_yil
    assert g["genel"]["birden_fazla_sureli"] == 28
    assert g["orgutlu"]["birden_fazla_sureli"] == 32


def test_yas_katlama_gecici6_daha_lehe(oranlar):
    """Geçici md. 6/4: 30.03.2020 öncesi suçlarda 15 yaş altı 1 gün = 3 gün."""
    yk = oranlar.yas_katlama
    assert yk.genel.on_bes_yas_alti_carpan == 2
    assert yk.gecici6.on_bes_yas_alti_carpan == 3
    assert yk.gecici6.on_sekiz_yas_alti_carpan == 2
    assert yk.gecici6.suc_tarihi_bitis == date(2020, 3, 30)


def test_bilinmeyen_kategori_hata(oranlar):
    with pytest.raises(KeyError):
        oranlar.oran_bul("olmayan_kategori", date(2024, 1, 1))


# --- ds_kurallari.yaml ---


def test_ds_temel_bir_yil(ds):
    assert ds.temel.sure_yil == 1


def test_onda_bir_sarti_sadece_yeni_suclara(ds):
    """Geçici md. 11: 1/10 şartı yalnız 4.6.2025 ve sonrası suçlarda."""
    assert ds.onda_bir_sarti.suc_tarihi_baslangic == date(2025, 6, 4)
    assert ds.onda_bir_sarti.min_gun == 5
    assert ds.onda_bir_sarti.oran == "1/10"


def test_gecici6_uc_yil_ve_kapali_kurum(ds):
    assert ds.gecici6.suc_tarihi_bitis == date(2020, 3, 30)
    assert ds.gecici6.sure_yil == 3
    assert ds.gecici6.kapali_kurumda_da_uygulanir is True
    assert "cinsel_dokunulmazlik" in ds.gecici6.istisna_kategorileri
    assert "uyusturucu_imal_ticaret" in ds.gecici6.istisna_kategorileri


def test_gecici10_esik_ve_kosullar(ds):
    g = ds.gecici10
    assert g.suc_tarihi_bitis == date(2023, 7, 31)
    assert g.ds_erken_yil == 3
    assert g.acik_kurum_min_ay == 3
    assert g.kapali_min_ay.toplam_ceza_10_yildan_az == 1
    assert g.kapali_min_ay.toplam_ceza_10_yil_ve_ustu == 3
    assert "k82_1def_oldurme" in g.istisna_kategorileri
    assert "deprem_oldurme" in g.istisna_kategorileri
    assert "orgut_faaliyeti" in g.istisna_kategorileri


def test_ozel_durumlar(ds):
    assert ds.ozel_durumlar.kadin_0_6_yas_cocuk.sure_yil == 2
    assert ds.ozel_durumlar.kadin_0_6_yas_cocuk.gecici6_sure_yil == 4
    assert ds.ozel_durumlar.agir_hastalik_engellilik_kocama.sure_yil == 3
    assert ds.adli_para_cevrilen_yararlanamaz is True


# --- suc_kategori_map.yaml ---


def test_uyusturucu_yetiskin_m108_9(kmap):
    """TCK 188 yetişkin fail → 3/4 kategorisi (md. 108/9); çocuk fail → 2/3."""
    e = kmap.bul("188")
    assert e is not None
    assert e.ks_kategori == "m108_9_listesi"
    assert e.cocuk_ks_kategori == "m107_2_listesi"
    assert e.gecici6_istisna is True


def test_nitelikli_cinsel_m108_9(kmap):
    for m in ("102/2", "103", "104/2", "104/3"):
        e = kmap.bul(m)
        assert e is not None, m
        assert e.ks_kategori == "m108_9_listesi", m
        assert e.gecici10_istisna is True, m


def test_basit_cinsel_saldiri_107_2(kmap):
    e = kmap.bul("102/1")
    assert e.ks_kategori == "m107_2_listesi"


def test_kadina_karsi_oldurme_gecici10_istisna(kmap):
    for m in ("82/1-d", "82/1-e", "82/1-f"):
        e = kmap.bul(m)
        assert e is not None and e.gecici10_istisna is True, m


def test_genel_kategori_ornekleri(kmap):
    for m in ("86", "141", "157"):
        assert kmap.bul(m).ks_kategori == "genel", m


def test_eslesmeyen_madde_none(kmap):
    assert kmap.bul("999") is None
