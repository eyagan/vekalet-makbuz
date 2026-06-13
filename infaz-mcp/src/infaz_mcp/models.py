"""Kural dosyası (rules/*.yaml) şema modelleri ve yükleyiciler.

Tüm kural verisi koddan ayrı YAML'da tutulur; bu modül yalnızca şemayı
doğrular ve tip güvenli erişim sağlar. Mevzuat değişikliğinde kod değil
YAML güncellenir (bkz. docs/infaz-mcp-plan.md Bölüm 9).
"""

from __future__ import annotations

from datetime import date
from fractions import Fraction
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

RULES_DIR = Path(__file__).resolve().parents[2] / "rules"

ORAN_PATTERN = r"^\d+/\d+$"


class Yururluk(BaseModel):
    """Suç tarihine göre uygulama aralığı (her iki uç da kapsayıcı)."""

    model_config = ConfigDict(extra="forbid")

    suc_tarihi_baslangic: date | None = None
    suc_tarihi_bitis: date | None = None

    def kapsar(self, suc_tarihi: date) -> bool:
        if self.suc_tarihi_baslangic and suc_tarihi < self.suc_tarihi_baslangic:
            return False
        if self.suc_tarihi_bitis and suc_tarihi > self.suc_tarihi_bitis:
            return False
        return True


class KsOrani(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kategori: str
    oran: str = Field(pattern=ORAN_PATTERN)
    dayanak: str
    yururluk: Yururluk | None = None

    @field_validator("oran")
    @classmethod
    def oran_bir_asagi(cls, v: str) -> str:
        f = Fraction(*map(int, v.split("/")))
        if not (0 < f <= 1):
            raise ValueError(f"oran 0-1 aralığında olmalı: {v}")
        return v

    @property
    def kesir(self) -> Fraction:
        return Fraction(*map(int, self.oran.split("/")))


class YasKatlamaGenel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    on_bes_yas_alti_carpan: int = Field(ge=1)


class YasKatlamaGecici6(YasKatlamaGenel):
    suc_tarihi_bitis: date
    on_sekiz_yas_alti_carpan: int = Field(ge=1)


class YasKatlama(BaseModel):
    model_config = ConfigDict(extra="forbid")
    genel: YasKatlamaGenel
    gecici6: YasKatlamaGecici6


class DenetimSuresi(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    kural: str


class Oranlar(BaseModel):
    """rules/oranlar.yaml kök şeması."""

    model_config = ConfigDict(extra="forbid")

    surum: str
    son_dogrulama: date
    kaynak: str
    ks_oranlari: list[KsOrani]
    sabit_sureler_yil: dict[str, int]
    coklu_mahkumiyet_ust_sinirlari_yil: dict[str, dict[str, int]]
    yas_katlama: YasKatlama
    denetim_suresi: DenetimSuresi

    def oran_bul(self, kategori: str, suc_tarihi: date) -> KsOrani:
        adaylar = [
            o
            for o in self.ks_oranlari
            if o.kategori == kategori
            and (o.yururluk is None or o.yururluk.kapsar(suc_tarihi))
        ]
        if not adaylar:
            raise KeyError(
                f"'{kategori}' kategorisi için {suc_tarihi} suç tarihinde "
                f"uygulanabilir oran bulunamadı"
            )
        if len(adaylar) > 1:
            raise ValueError(
                f"'{kategori}' için {suc_tarihi} tarihinde birden fazla oran "
                f"eşleşti — yürürlük aralıkları çakışıyor"
            )
        return adaylar[0]


class OndaBirSarti(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    suc_tarihi_baslangic: date
    oran: str = Field(pattern=ORAN_PATTERN)
    min_gun: int = Field(ge=1)


class Gecici6(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    suc_tarihi_bitis: date
    sure_yil: int = Field(ge=1)
    kapali_kurumda_da_uygulanir: bool
    istisna_kategorileri: list[str]


class Gecici10KapaliMin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    toplam_ceza_10_yildan_az: int
    toplam_ceza_10_yil_ve_ustu: int


class Gecici10(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    suc_tarihi_bitis: date
    ds_erken_yil: int = Field(ge=1)
    acik_kurum_min_ay: int = Field(ge=0)
    kapali_min_ay: Gecici10KapaliMin
    acige_ayrilmaya_kalan_max_yil: int
    istisna_kategorileri: list[str]


class DsTemel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    sure_yil: int = Field(ge=1)
    sartlar: list[str]


class OzelDurumKadin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    sure_yil: int
    gecici6_sure_yil: int


class OzelDurumHastalik(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dayanak: str
    sure_yil: int
    gecici6_65_yas_ustu_sinirsiz: bool


class OzelDurumlar(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kadin_0_6_yas_cocuk: OzelDurumKadin
    agir_hastalik_engellilik_kocama: OzelDurumHastalik


class DsKurallari(BaseModel):
    """rules/ds_kurallari.yaml kök şeması."""

    model_config = ConfigDict(extra="forbid")

    surum: str
    son_dogrulama: date
    temel: DsTemel
    onda_bir_sarti: OndaBirSarti
    gecici6: Gecici6
    gecici10: Gecici10
    ozel_durumlar: OzelDurumlar
    adli_para_cevrilen_yararlanamaz: bool


class SucEslemesi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    madde: str
    ad: str
    ks_kategori: str
    cocuk_ks_kategori: str | None = None
    gecici6_istisna: bool = False
    gecici10_istisna: bool = False
    not_: str | None = Field(default=None, alias="not")


class BayrakKurali(BaseModel):
    model_config = ConfigDict(extra="allow")  # serbest açıklama alanları


class SucKategoriMap(BaseModel):
    """rules/suc_kategori_map.yaml kök şeması."""

    model_config = ConfigDict(extra="forbid")

    surum: str
    esleme: list[SucEslemesi]
    bayrak_kurallari: dict[str, BayrakKurali]

    def bul(self, madde: str) -> SucEslemesi | None:
        for e in self.esleme:
            if e.madde == madde:
                return e
        return None


def _yukle(dosya: str) -> dict:
    with open(RULES_DIR / dosya, encoding="utf-8") as f:
        return yaml.safe_load(f)


def oranlar_yukle() -> Oranlar:
    return Oranlar.model_validate(_yukle("oranlar.yaml"))


def ds_kurallari_yukle() -> DsKurallari:
    return DsKurallari.model_validate(_yukle("ds_kurallari.yaml"))


def kategori_map_yukle() -> SucKategoriMap:
    return SucKategoriMap.model_validate(_yukle("suc_kategori_map.yaml"))
