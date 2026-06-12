"""Hesap motorunun girdi/çıktı tipleri (MCP'den bağımsız).

Bu tipler UYAP müddetname alanlarıyla hizalıdır (bkz. plan Bölüm 5).
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TutuklulukAraligi(BaseModel):
    model_config = ConfigDict(extra="forbid")

    baslangic: date
    bitis: date

    @model_validator(mode="after")
    def _sira(self) -> "TutuklulukAraligi":
        if self.bitis < self.baslangic:
            raise ValueError("tutukluluk bitişi başlangıçtan önce olamaz")
        return self


class InfazGirdisi(BaseModel):
    """Tek süreli hapis cezası için infaz hesabı girdisi (MVP kapsamı)."""

    model_config = ConfigDict(extra="forbid")

    ceza_yil: int = Field(ge=0, default=0)
    ceza_ay: int = Field(ge=0, default=0)
    ceza_gun: int = Field(ge=0, default=0)

    tck_madde: str = Field(description="TCK madde/fıkra, ör. '86/1', '188', '102/2'")
    suc_tarihi: date
    infaz_baslangici: date

    tutukluluk_araliklari: list[TutuklulukAraligi] = Field(default_factory=list)

    # Failin suç tarihindeki durumu
    cocuk_fail: bool = False          # suç tarihinde 18 yaşından küçük
    mukerrir: bool = False            # md. 108/1
    mukerrir_ikinci: bool = False     # md. 108/3 (ikinci tekerrür)
    orgut_kapsaminda: bool = False    # md. 107/4
    teror_kapsaminda: bool = False    # 3713
    adli_para_cevrilen: bool = False  # md. 105/A-4: DS yok

    # Geçici md. 10 değerlendirmesi için
    acik_kurumda: bool = False        # hükümlü açık kurumda mı

    # Müddetname taslağı için (hesabı etkilemez)
    ad_soyad: str | None = None
    mahkeme: str | None = None
    esas_no: str | None = None
    karar_no: str | None = None

    @model_validator(mode="after")
    def _ceza_pozitif(self) -> "InfazGirdisi":
        if self.ceza_yil == 0 and self.ceza_ay == 0 and self.ceza_gun == 0:
            raise ValueError("ceza süresi sıfır olamaz")
        if self.infaz_baslangici < self.suc_tarihi:
            raise ValueError("infaz başlangıcı suç tarihinden önce olamaz")
        return self


class InfazSonucu(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kosullu_saliverilme: date
    denetimli_serbestlik: date | None
    bihakkin_tahliye: date

    uygulanan_oran: str
    uygulanan_kategori: str
    uygulanan_ds_rejimi: str

    mahsup_gun: int
    dayanaklar: list[str]
    hesap_dokumu: list[str]
    uyarilar: list[str]

    kural_surumu: str
    son_dogrulama: date
