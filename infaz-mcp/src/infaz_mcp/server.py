"""infaz-mcp — yerel MCP sunucusu (stdio).

Araçlar:
  infaz_hesapla      — tarihleri ve hesap dökümünü döndürür
  muddetname_taslagi — sonucu müddetname düzeninde Markdown belge yapar
  kategori_bul       — TCK madde/fıkradan kategori önizlemesi
  kural_listesi      — yüklü kural sürümü, son doğrulama, yürürlük bilgisi

Kurulum (Claude Code):
  claude mcp add infaz -- uv run --directory /YOL/infaz-mcp python -m infaz_mcp.server
"""

from __future__ import annotations

from datetime import date

from fastmcp import FastMCP

from . import engine
from .kategori import KategoriBulunamadi, kategori_belirle
from .models import ds_kurallari_yukle, kategori_map_yukle, oranlar_yukle
from .muddetname import muddetname_markdown
from .tipler import InfazGirdisi, TutuklulukAraligi

mcp = FastMCP(
    name="infaz",
    instructions=(
        "5275 sayılı Kanun'a göre koşullu salıverilme, denetimli serbestlik ve "
        "bihakkın tahliye tarihlerini hesaplar. Çıktılar TAHMİNÎDİR; resmî "
        "müddetname savcılıkça düzenlenir. Suç kategorisi kullanıcıdan istenmez; "
        "TCK madde/fıkra verilir, araç eşler. Eşleşme yoksa kullanıcıya sorulur."
    ),
)

# Kurallar başlangıçta bir kez yüklenir.
_ORAN = oranlar_yukle()
_DS = ds_kurallari_yukle()
_KMAP = kategori_map_yukle()


def _girdi_kur(
    tck_madde: str,
    suc_tarihi: str,
    infaz_baslangici: str,
    ceza_yil: int = 0,
    ceza_ay: int = 0,
    ceza_gun: int = 0,
    tutukluluk_araliklari: list[dict] | None = None,
    cocuk_fail: bool = False,
    mukerrir: bool = False,
    mukerrir_ikinci: bool = False,
    orgut_kapsaminda: bool = False,
    teror_kapsaminda: bool = False,
    adli_para_cevrilen: bool = False,
    acik_kurumda: bool = False,
    ad_soyad: str | None = None,
    mahkeme: str | None = None,
    esas_no: str | None = None,
    karar_no: str | None = None,
) -> InfazGirdisi:
    araliklar = [
        TutuklulukAraligi(
            baslangic=date.fromisoformat(a["baslangic"]),
            bitis=date.fromisoformat(a["bitis"]),
        )
        for a in (tutukluluk_araliklari or [])
    ]
    return InfazGirdisi(
        ceza_yil=ceza_yil,
        ceza_ay=ceza_ay,
        ceza_gun=ceza_gun,
        tck_madde=tck_madde,
        suc_tarihi=date.fromisoformat(suc_tarihi),
        infaz_baslangici=date.fromisoformat(infaz_baslangici),
        tutukluluk_araliklari=araliklar,
        cocuk_fail=cocuk_fail,
        mukerrir=mukerrir,
        mukerrir_ikinci=mukerrir_ikinci,
        orgut_kapsaminda=orgut_kapsaminda,
        teror_kapsaminda=teror_kapsaminda,
        adli_para_cevrilen=adli_para_cevrilen,
        acik_kurumda=acik_kurumda,
        ad_soyad=ad_soyad,
        mahkeme=mahkeme,
        esas_no=esas_no,
        karar_no=karar_no,
    )


@mcp.tool
def infaz_hesapla(
    tck_madde: str,
    suc_tarihi: str,
    infaz_baslangici: str,
    ceza_yil: int = 0,
    ceza_ay: int = 0,
    ceza_gun: int = 0,
    tutukluluk_araliklari: list[dict] | None = None,
    cocuk_fail: bool = False,
    mukerrir: bool = False,
    mukerrir_ikinci: bool = False,
    orgut_kapsaminda: bool = False,
    teror_kapsaminda: bool = False,
    adli_para_cevrilen: bool = False,
    acik_kurumda: bool = False,
) -> dict:
    """Koşullu salıverilme, denetimli serbestlik ve bihakkın tahliye tarihlerini hesaplar.

    Tarihler ISO 'YYYY-MM-DD'. tck_madde örn. '86/1', '188', '102/2'.
    tutukluluk_araliklari: [{"baslangic": "2023-01-10", "bitis": "2023-02-08"}].
    Sonuç TAHMİNÎDİR; resmî müddetname savcılıkça düzenlenir.
    """
    try:
        girdi = _girdi_kur(
            tck_madde, suc_tarihi, infaz_baslangici, ceza_yil, ceza_ay, ceza_gun,
            tutukluluk_araliklari, cocuk_fail, mukerrir, mukerrir_ikinci,
            orgut_kapsaminda, teror_kapsaminda, adli_para_cevrilen, acik_kurumda,
        )
        sonuc = engine.hesapla(girdi, _ORAN, _DS, _KMAP)
        return sonuc.model_dump(mode="json")
    except KategoriBulunamadi as e:
        return {
            "hata": "kategori_bulunamadi",
            "mesaj": str(e),
            "olasi_maddeler": e.adaylar,
            "oneri": "Lütfen TCK madde/fıkrayı (ör. '102/2') netleştirin "
                     "veya kategori_bul aracını kullanın.",
        }
    except ValueError as e:
        return {"hata": "gecersiz_girdi", "mesaj": str(e)}


@mcp.tool
def muddetname_taslagi(
    tck_madde: str,
    suc_tarihi: str,
    infaz_baslangici: str,
    ceza_yil: int = 0,
    ceza_ay: int = 0,
    ceza_gun: int = 0,
    tutukluluk_araliklari: list[dict] | None = None,
    cocuk_fail: bool = False,
    mukerrir: bool = False,
    mukerrir_ikinci: bool = False,
    orgut_kapsaminda: bool = False,
    teror_kapsaminda: bool = False,
    adli_para_cevrilen: bool = False,
    acik_kurumda: bool = False,
    ad_soyad: str | None = None,
    mahkeme: str | None = None,
    esas_no: str | None = None,
    karar_no: str | None = None,
) -> str:
    """Hesap sonucunu müddetname (süre belgesi) düzeninde Markdown belge olarak üretir.

    Başlıkta kalıcı 'RESMÎ BELGE DEĞİLDİR' ibaresi bulunur. Mahkeme/esas-karar/ad
    alanları yalnız belgeye işlenir, hesabı etkilemez.
    """
    try:
        girdi = _girdi_kur(
            tck_madde, suc_tarihi, infaz_baslangici, ceza_yil, ceza_ay, ceza_gun,
            tutukluluk_araliklari, cocuk_fail, mukerrir, mukerrir_ikinci,
            orgut_kapsaminda, teror_kapsaminda, adli_para_cevrilen, acik_kurumda,
            ad_soyad, mahkeme, esas_no, karar_no,
        )
        sonuc = engine.hesapla(girdi, _ORAN, _DS, _KMAP)
        return muddetname_markdown(girdi, sonuc)
    except KategoriBulunamadi as e:
        return f"**Hesaplanamadı:** {e}\n\nOlası maddeler: {', '.join(e.adaylar) or 'yok'}"
    except ValueError as e:
        return f"**Geçersiz girdi:** {e}"


@mcp.tool
def kategori_bul(tck_madde: str, cocuk_fail: bool = False) -> dict:
    """TCK madde/fıkradan KS kategorisini ve geçici madde istisna bayraklarını önizler.

    Hesap yapmadan, hangi orana ve rejime gireceğini gösterir.
    """
    sahte = InfazGirdisi(
        ceza_yil=1, tck_madde=tck_madde, suc_tarihi=date(2024, 1, 1),
        infaz_baslangici=date(2024, 1, 1), cocuk_fail=cocuk_fail,
    )
    try:
        kat = kategori_belirle(sahte, _KMAP)
    except KategoriBulunamadi as e:
        return {"hata": "kategori_bulunamadi", "mesaj": str(e),
                "olasi_maddeler": e.adaylar}
    return {
        "tck_madde": tck_madde,
        "ks_kategori": kat.ks_kategori,
        "aciklama": kat.aciklama,
        "gecici6_istisna": kat.gecici6_istisna,
        "gecici10_istisna": kat.gecici10_istisna,
        "dayanaklar": kat.dayanaklar,
    }


@mcp.tool
def kural_listesi() -> dict:
    """Yüklü kural setinin sürümünü, son doğrulama tarihini ve kaynağını döndürür."""
    bugun = date.today()
    gecen = (bugun - _ORAN.son_dogrulama).days
    return {
        "surum": _ORAN.surum,
        "son_dogrulama": _ORAN.son_dogrulama.isoformat(),
        "gecen_gun": gecen,
        "bayat_mi": gecen > 90,
        "kaynak": _ORAN.kaynak,
        "ks_oran_kategorileri": sorted({o.kategori for o in _ORAN.ks_oranlari}),
        "ds_surum": _DS.surum,
        "uyari": (
            "Kural seti 90 günden eski; güncel mevzuatla teyit edin."
            if gecen > 90 else "Kural seti güncel sayılır."
        ),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
