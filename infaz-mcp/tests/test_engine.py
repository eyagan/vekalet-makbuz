"""Faz 2 golden senaryoları — hesap motoru kural mantığı.

Tarih beklentileri, girdiden timedelta ile türetilir (Python'un tarih
toplamasını değil, motorun seçtiği GÜN sayısı ve KURALLARI test ederiz).
Oran/kategori/rejim değerleri kanun metnine sabitlenmiştir.

Mutlak takvim doğruluğu (ör. gerçek müddetname ile birebir) Faz 5 kabul
kapısıdır; bu testler regresyonu yakalar.
"""

from datetime import date, timedelta

import pytest

from infaz_mcp.engine import hesapla
from infaz_mcp.kategori import KategoriBulunamadi
from infaz_mcp.models import (
    ds_kurallari_yukle,
    kategori_map_yukle,
    oranlar_yukle,
)
from infaz_mcp.tipler import InfazGirdisi, TutuklulukAraligi

ORAN = oranlar_yukle()
DS = ds_kurallari_yukle()
KMAP = kategori_map_yukle()


def calc(**kw):
    return hesapla(InfazGirdisi(**kw), ORAN, DS, KMAP)


# --- 1: standart, geçici 11 öncesi (1/10 UYGULANMAZ) ---
def test_standart_yarim_oran():
    infaz = date(2024, 6, 1)
    s = calc(ceza_yil=4, tck_madde="86/1", suc_tarihi=date(2024, 1, 1), infaz_baslangici=infaz)
    assert s.uygulanan_oran == "1/2"
    assert s.uygulanan_kategori == "genel"
    assert s.bihakkin_tahliye == infaz + timedelta(days=1460)
    assert s.kosullu_saliverilme == infaz + timedelta(days=730)
    assert s.denetimli_serbestlik == infaz + timedelta(days=365)  # KS − 1 yıl
    assert "1/10" not in s.uygulanan_ds_rejimi  # geçici md. 11


# --- 1c: uyuşturucu ticareti (188 yetişkin) → 3/4, md. 108/9 ---
def test_uyusturucu_yetiskin_dortte_uc():
    infaz = date(2024, 1, 1)
    s = calc(ceza_yil=6, tck_madde="188", suc_tarihi=date(2024, 1, 1), infaz_baslangici=infaz)
    assert s.uygulanan_oran == "3/4"
    assert s.uygulanan_kategori == "m108_9_listesi"
    assert s.kosullu_saliverilme == infaz + timedelta(days=1642)  # 2190*3//4


def test_uyusturucu_cocuk_ucte_iki():
    s = calc(ceza_yil=6, tck_madde="188", suc_tarihi=date(2024, 1, 1),
             infaz_baslangici=date(2024, 1, 1), cocuk_fail=True)
    assert s.uygulanan_oran == "2/3"
    assert s.uygulanan_kategori == "m107_2_listesi"


# --- 2: geçici md. 10 (suç ≤ 31.7.2023) — DS 3 yıl erken ---
def test_gecici10_uc_yil_erken():
    s = calc(ceza_yil=12, tck_madde="188", suc_tarihi=date(2023, 1, 1),
             infaz_baslangici=date(2023, 6, 1))
    assert "geçici md. 10" in s.uygulanan_ds_rejimi
    # ds_yil = 1 (temel) + 3 (geçici10) = 4 → DS = KS − 4 yıl
    assert s.denetimli_serbestlik == s.kosullu_saliverilme - timedelta(days=4 * 365)
    assert any("tartışmalı" in u for u in s.uyarilar)


# --- 3: geçici md. 6 (suç ≤ 30.3.2020) — DS süresi 3 yıl ---
def test_gecici6_uc_yil_ds():
    # uzun ceza: hem geçici6 (3 yıl) hem geçici10 (+3) → 6 yıl, clamp olmasın
    s = calc(ceza_yil=20, tck_madde="158", suc_tarihi=date(2019, 1, 1),
             infaz_baslangici=date(2019, 6, 1))
    assert "geçici md. 6" in s.uygulanan_ds_rejimi
    assert "geçici md. 10" in s.uygulanan_ds_rejimi
    assert s.denetimli_serbestlik == s.kosullu_saliverilme - timedelta(days=6 * 365)


# --- m108/9 tarih eşiği: 28.6.2014 öncesi 2/3 ---
def test_m108_9_eski_suc_ucte_iki():
    s = calc(ceza_yil=10, tck_madde="103", suc_tarihi=date(2014, 1, 1),
             infaz_baslangici=date(2015, 1, 1))
    assert s.uygulanan_oran == "2/3"


def test_m108_9_yeni_suc_dortte_uc():
    s = calc(ceza_yil=10, tck_madde="103", suc_tarihi=date(2015, 1, 1),
             infaz_baslangici=date(2016, 1, 1))
    assert s.uygulanan_oran == "3/4"


# --- 5: aralıklı mahsup ---
def test_mahsup_iki_aralik():
    s = calc(
        ceza_yil=4, tck_madde="86/1", suc_tarihi=date(2024, 1, 1),
        infaz_baslangici=date(2024, 6, 1),
        tutukluluk_araliklari=[
            TutuklulukAraligi(baslangic=date(2023, 1, 10), bitis=date(2023, 2, 8)),  # 30
            TutuklulukAraligi(baslangic=date(2023, 5, 1), bitis=date(2023, 5, 30)),  # 30
        ],
    )
    assert s.mahsup_gun == 60
    assert s.kosullu_saliverilme == date(2024, 6, 1) + timedelta(days=730 - 60)


def test_mahsup_cakisan_aralik_birlesir():
    s = calc(
        ceza_yil=4, tck_madde="86/1", suc_tarihi=date(2024, 1, 1),
        infaz_baslangici=date(2024, 6, 1),
        tutukluluk_araliklari=[
            TutuklulukAraligi(baslangic=date(2023, 1, 1), bitis=date(2023, 1, 31)),
            TutuklulukAraligi(baslangic=date(2023, 1, 15), bitis=date(2023, 2, 14)),
        ],
    )
    assert s.mahsup_gun == 45  # 01.01–14.02 birleşik, 31+31 değil


# --- 1b / 8: 1/10 şartı (geçici md. 11 — yalnız ≥ 4.6.2025) ---
def test_onda_bir_yeni_suc_oteleme():
    infaz = date(2025, 8, 1)
    s = calc(ceza_yil=2, tck_madde="86/1", suc_tarihi=date(2025, 7, 1), infaz_baslangici=infaz)
    # ks_suresi = 730//2 = 365; 1/10 = 36 gün; DS normalde KS−365 = infaz
    assert "1/10" in s.uygulanan_ds_rejimi
    assert s.denetimli_serbestlik == infaz + timedelta(days=36)


def test_onda_bir_eski_suc_uygulanmaz():
    infaz = date(2024, 8, 1)
    s = calc(ceza_yil=2, tck_madde="86/1", suc_tarihi=date(2024, 7, 1), infaz_baslangici=infaz)
    assert "1/10" not in s.uygulanan_ds_rejimi
    assert s.denetimli_serbestlik == infaz  # KS−365 = infaz, ötelenmez


# --- adli para çevrilen: DS yok ---
def test_adli_para_ds_yok():
    s = calc(ceza_yil=1, tck_madde="86/1", suc_tarihi=date(2024, 1, 1),
             infaz_baslangici=date(2024, 1, 1), adli_para_cevrilen=True)
    assert s.denetimli_serbestlik is None
    assert "105/A-4" in s.uygulanan_ds_rejimi


# --- 11: eşleşmeyen madde → tahmin etme ---
def test_eslesmeyen_madde_hata():
    with pytest.raises(KategoriBulunamadi):
        calc(ceza_yil=2, tck_madde="999", suc_tarihi=date(2024, 1, 1),
             infaz_baslangici=date(2024, 1, 1))


# --- 12: geçersiz girdi → pydantic ---
def test_negatif_ceza_hata():
    with pytest.raises(ValueError):
        InfazGirdisi(ceza_yil=0, ceza_ay=0, ceza_gun=0, tck_madde="86/1",
                     suc_tarihi=date(2024, 1, 1), infaz_baslangici=date(2024, 1, 1))


def test_infaz_suctan_once_hata():
    with pytest.raises(ValueError):
        InfazGirdisi(ceza_yil=2, tck_madde="86/1", suc_tarihi=date(2024, 6, 1),
                     infaz_baslangici=date(2024, 1, 1))


# --- terör bayrağı oranı (3/4) ve kategori önceliği ---
def test_teror_dortte_uc():
    s = calc(ceza_yil=10, tck_madde="86/1", suc_tarihi=date(2024, 1, 1),
             infaz_baslangici=date(2024, 1, 1), teror_kapsaminda=True)
    assert s.uygulanan_oran == "3/4"
    assert s.uygulanan_kategori == "teror"


# --- hesap dökümü ve dayanaklar dolu ---
def test_dokum_ve_dayanak_dolu():
    s = calc(ceza_yil=3, tck_madde="86/1", suc_tarihi=date(2024, 1, 1),
             infaz_baslangici=date(2024, 1, 1))
    assert len(s.hesap_dokumu) >= 4
    assert any("107" in d for d in s.dayanaklar)
    assert s.uyarilar  # en az tahminîlik uyarısı
