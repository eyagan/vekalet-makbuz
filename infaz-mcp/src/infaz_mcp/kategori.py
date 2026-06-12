"""TCK madde/fıkra + fail durumundan KS kategorisini ve geçici madde
istisna bayraklarını belirler.

İlke: eşleşme yoksa TAHMİN ETME. `KategoriBulunamadi` fırlatır; çağıran
katman olası adayları kullanıcıya sorar (plan Bölüm 4 — en büyük hata
kaynağı yanlış kategoridir).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import SucKategoriMap
from .tipler import InfazGirdisi


class KategoriBulunamadi(Exception):
    def __init__(self, madde: str, adaylar: list[str]):
        self.madde = madde
        self.adaylar = adaylar
        super().__init__(
            f"'{madde}' için kategori eşleşmesi bulunamadı. "
            f"Yakın maddeler: {', '.join(adaylar) if adaylar else 'yok'}"
        )


@dataclass
class KategoriSonucu:
    ks_kategori: str
    gecici6_istisna: bool
    gecici10_istisna: bool
    aciklama: str
    dayanaklar: list[str]


def _ana_madde(madde: str) -> str:
    """'102/2' → '102'."""
    return madde.split("/", 1)[0]


def kategori_belirle(girdi: InfazGirdisi, kmap: SucKategoriMap) -> KategoriSonucu:
    dayanaklar: list[str] = []

    # 1) Bayraklar madde eşlemesinden önceliklidir (terör > örgüt en ağır oran).
    if girdi.teror_kapsaminda:
        return KategoriSonucu(
            ks_kategori="teror",
            gecici6_istisna=True,
            gecici10_istisna=True,
            aciklama="Terörle Mücadele Kanunu kapsamı (3713 md. 17)",
            dayanaklar=["3713 md. 17"],
        )
    if girdi.orgut_kapsaminda:
        return KategoriSonucu(
            ks_kategori="orgutlu",
            gecici6_istisna=False,
            gecici10_istisna=True,
            aciklama="Örgüt faaliyeti kapsamında işlenen suç (5275 md. 107/4)",
            dayanaklar=["5275 md. 107/4"],
        )

    # 2) Mükerrirlik oranı, suç kategorisinin oranından daha lehe ise göz ardı
    #    edilir; ikinci tekerrür 3/4 her hâlde uygulanır (md. 108/3).
    if girdi.mukerrir_ikinci:
        dayanaklar.append("5275 md. 108/3 (7550)")
        mukerrir_kategori = "mukerrir_ikinci"
    elif girdi.mukerrir:
        dayanaklar.append("5275 md. 108/1")
        mukerrir_kategori = "mukerrir"
    else:
        mukerrir_kategori = None

    # 3) Madde eşlemesi
    eslesme = kmap.bul(girdi.tck_madde) or kmap.bul(_ana_madde(girdi.tck_madde))
    if eslesme is None:
        adaylar = [
            e.madde
            for e in kmap.esleme
            if _ana_madde(e.madde) == _ana_madde(girdi.tck_madde)
        ]
        raise KategoriBulunamadi(girdi.tck_madde, adaylar)

    if girdi.cocuk_fail and eslesme.cocuk_ks_kategori:
        suc_kategori = eslesme.cocuk_ks_kategori
    else:
        suc_kategori = eslesme.ks_kategori
    dayanaklar.append(f"TCK {eslesme.madde} → {eslesme.ad}")

    # Mükerrirlik ile suç kategorisinden hangisi daha ağır oran veriyorsa o.
    # Sıralama: genel(1/2) < 2/3(m107_2,orgutlu,mukerrir) < 3/4(m108_9,mukerrir_ikinci)
    ks_kategori = _agir_olan(suc_kategori, mukerrir_kategori)

    return KategoriSonucu(
        ks_kategori=ks_kategori,
        gecici6_istisna=eslesme.gecici6_istisna,
        gecici10_istisna=eslesme.gecici10_istisna,
        aciklama=eslesme.ad,
        dayanaklar=dayanaklar,
    )


# Oran ağırlık sırası (büyük = daha çok infaz)
_AGIRLIK = {
    "genel": 0,
    "m107_2_listesi": 1,
    "orgutlu": 1,
    "mukerrir": 1,
    "m108_9_listesi": 2,
    "mukerrir_ikinci": 2,
    "teror": 2,
}


def _agir_olan(a: str, b: str | None) -> str:
    if b is None:
        return a
    return a if _AGIRLIK.get(a, 0) >= _AGIRLIK.get(b, 0) else b
