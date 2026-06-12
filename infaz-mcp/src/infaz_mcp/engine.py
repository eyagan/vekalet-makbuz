"""İnfaz hesap motoru — saf Python, MCP'den bağımsız.

Akış (plan Bölüm 4.3 / 6):
  girdi → kategori belirle → KS oranı (suç tarihine göre) → mahsup
        → bihakkın / KS / DS tarihleri (TCK 61/6 aritmetiği)
        → dayanak + hesap dökümü + uyarılar

KAPSAM (MVP): tek süreli hapis cezası, yetişkin/çocuk fail. Müebbet türleri,
içtima ve özel infaz usulleri Faz 8 kapsamındadır.
"""

from __future__ import annotations

from datetime import date

from . import dates
from .kategori import kategori_belirle
from .models import DsKurallari, Oranlar, SucKategoriMap
from .tipler import InfazGirdisi, InfazSonucu

UYARI_TAHMIN = (
    "Bu hesap TAHMİNÎDİR; resmî müddetname Cumhuriyet savcılığınca düzenlenir. "
    "İçtima, disiplin cezalarının iyi hâle etkisi ve infaz erteleme dikkate alınmamıştır."
)


def hesapla(
    girdi: InfazGirdisi,
    oranlar: Oranlar,
    ds_kurallari: DsKurallari,
    kmap: SucKategoriMap,
) -> InfazSonucu:
    dokum: list[str] = []
    uyarilar: list[str] = [UYARI_TAHMIN]
    dayanaklar: list[str] = []

    # 1) Kategori + oran
    kat = kategori_belirle(girdi, kmap)
    dayanaklar.extend(kat.dayanaklar)
    oran_kaydi = oranlar.oran_bul(kat.ks_kategori, girdi.suc_tarihi)
    oran = oran_kaydi.kesir
    dayanaklar.append(oran_kaydi.dayanak)
    dokum.append(
        f"Kategori: {kat.ks_kategori} ({kat.aciklama}) → KS oranı {oran_kaydi.oran} "
        f"[{oran_kaydi.dayanak}]"
    )

    # 2) Süreler (TCK 61/6: yıl=365, ay=30; oran kesri atılır)
    ceza_gun = dates.sure_gune_cevir(girdi.ceza_yil, girdi.ceza_ay, girdi.ceza_gun)
    dokum.append(
        f"Ceza süresi: {girdi.ceza_yil} yıl {girdi.ceza_ay} ay {girdi.ceza_gun} gün "
        f"= {ceza_gun} gün (yıl=365, ay=30)"
    )

    mahsup = dates.araliklar_toplam_gun(
        [(a.baslangic, a.bitis) for a in girdi.tutukluluk_araliklari]
    )
    if mahsup:
        dokum.append(f"Mahsup (tutuklulukta geçen): {mahsup} gün ({dates.gun_to_metin(mahsup)})")

    # 15 yaş katlaması bu motorda uygulanmaz (kurumda fiilî gün gerektirir) —
    # girdi yaş bilgisi taşımıyorsa atlanır; Faz 8'de eklenecek.

    ks_suresi = dates.oran_uygula(ceza_gun, oran)
    dokum.append(
        f"KS için infaz kurumunda geçirilmesi gereken süre: {ceza_gun} × {oran_kaydi.oran} "
        f"= {ks_suresi} gün ({dates.gun_to_metin(ks_suresi)})"
    )

    # 3) Tarihler
    net_ks = ks_suresi - mahsup
    bihakkin = dates.gun_ekle(girdi.infaz_baslangici, ceza_gun - mahsup)
    dokum.append(
        f"Bihakkın (hak ederek) tahliye = infaz başlangıcı + ({ceza_gun} − {mahsup}) gün "
        f"= {bihakkin.isoformat()}"
    )

    if net_ks <= 0:
        ks_tarihi = girdi.infaz_baslangici
        uyarilar.append(
            "Mahsup, KS için gereken süreyi karşılıyor; KS tarihi infaz başlangıcına "
            "eşit alındı. Bu durumda derhâl salıverilme/DS değerlendirmesi gerekir."
        )
    else:
        ks_tarihi = dates.gun_ekle(girdi.infaz_baslangici, net_ks)
    dokum.append(
        f"Koşullu salıverilme = infaz başlangıcı + ({ks_suresi} − {mahsup}) gün "
        f"= {ks_tarihi.isoformat()}"
    )

    # 4) Denetimli serbestlik
    ds_tarihi, ds_rejimi = _ds_hesapla(
        girdi, ds_kurallari, kat, ks_tarihi, ks_suresi, mahsup, dokum, dayanaklar, uyarilar
    )

    return InfazSonucu(
        kosullu_saliverilme=ks_tarihi,
        denetimli_serbestlik=ds_tarihi,
        bihakkin_tahliye=bihakkin,
        uygulanan_oran=oran_kaydi.oran,
        uygulanan_kategori=kat.ks_kategori,
        uygulanan_ds_rejimi=ds_rejimi,
        mahsup_gun=mahsup,
        dayanaklar=_benzersiz(dayanaklar),
        hesap_dokumu=dokum,
        uyarilar=uyarilar,
        kural_surumu=oranlar.surum,
        son_dogrulama=oranlar.son_dogrulama,
    )


def _ds_hesapla(
    girdi, ds, kat, ks_tarihi, ks_suresi, mahsup, dokum, dayanaklar, uyarilar
) -> tuple[date | None, str]:
    if girdi.adli_para_cevrilen:
        dokum.append("DS yok: adli para cezasından çevrilen hapis (md. 105/A-4).")
        dayanaklar.append(ds.temel.dayanak)
        return None, "Yok (adli para çevrimi — md. 105/A-4)"

    # DS temel süresi (yıl)
    ds_yil = ds.temel.sure_yil
    rejim = f"md. 105/A — {ds_yil} yıl"
    dayanaklar.append(ds.temel.dayanak)

    if girdi.suc_tarihi <= ds.gecici6.suc_tarihi_bitis and not kat.gecici6_istisna:
        ds_yil = ds.gecici6.sure_yil
        rejim = f"geçici md. 6 — {ds_yil} yıl"
        dayanaklar.append(ds.gecici6.dayanak)
        dokum.append(
            f"Geçici md. 6 uygulanır (suç ≤ {ds.gecici6.suc_tarihi_bitis.isoformat()}): "
            f"DS süresi {ds_yil} yıl."
        )

    gecici10 = (
        girdi.suc_tarihi <= ds.gecici10.suc_tarihi_bitis and not kat.gecici10_istisna
    )
    if gecici10:
        ds_yil += ds.gecici10.ds_erken_yil
        rejim += f" + geçici md. 10 (+{ds.gecici10.ds_erken_yil} yıl erken)"
        dayanaklar.append(ds.gecici10.dayanak)
        dokum.append(
            f"Geçici md. 10/6 uygulanır (suç ≤ {ds.gecici10.suc_tarihi_bitis.isoformat()}): "
            f"DS'den {ds.gecici10.ds_erken_yil} yıl erken yararlanma eklendi."
        )
        uyarilar.append(
            "Geçici md. 10/6 koşulları girdiden tam doğrulanamaz: açık kurumda en az 3 ay "
            "kalmış olmak; kapalıda toplam ceza <10 yıl ise 1 ay, ≥10 yıl ise 3 ay geçirmiş "
            "olmak gerekir. Geçici md. 6 ile birlikte uygulanmasının (kümülasyon) caiz olup "
            "olmadığı öğretide tartışmalıdır — infaz hâkimi takdiri esastır."
        )

    ds_suresi_gun = ds_yil * dates.GUN_YIL
    ds_tarihi = dates.gun_ekle(ks_tarihi, -ds_suresi_gun)
    dokum.append(
        f"DS = KS − {ds_yil} yıl ({ds_suresi_gun} gün) = {ds_tarihi.isoformat()} "
        f"[{rejim}]"
    )

    # 1/10 şartı (geçici md. 11: yalnız 4.6.2025 ve sonrası suçlar)
    if girdi.suc_tarihi >= ds.onda_bir_sarti.suc_tarihi_baslangic:
        min_kurum = max(ds.onda_bir_sarti.min_gun, ks_suresi // 10)
        en_erken_ds = dates.gun_ekle(girdi.infaz_baslangici, max(0, min_kurum - mahsup))
        dayanaklar.append(ds.onda_bir_sarti.dayanak)
        if en_erken_ds > ds_tarihi:
            dokum.append(
                f"1/10 şartı (md. 105/A son cümle): KS için gereken {ks_suresi} günün en az "
                f"1/10'u ({min_kurum} gün, asgari {ds.onda_bir_sarti.min_gun}) kurumda "
                f"geçirilmeli → DS en erken {en_erken_ds.isoformat()}'e ötelendi."
            )
            ds_tarihi = en_erken_ds
            rejim += " (1/10 şartıyla ötelendi)"
        else:
            dokum.append(
                f"1/10 şartı sağlandı (asgari {min_kurum} gün, mevcut hesap zaten karşılıyor)."
            )

    # Sınırlar: DS infaz başlangıcından önce ve KS'den sonra olamaz
    if ds_tarihi < girdi.infaz_baslangici:
        ds_tarihi = girdi.infaz_baslangici
        rejim += " (infaz başlangıcına çekildi)"
        uyarilar.append(
            "Hesaplanan DS tarihi infaz başlangıcından önce; kısa ceza nedeniyle DS, "
            "infaz başlangıcına çekildi. Pratikte doğrudan DS/açık kurum değerlendirmesi gerekir."
        )
    if ds_tarihi > ks_tarihi:
        ds_tarihi = ks_tarihi

    return ds_tarihi, rejim


def _benzersiz(items: list[str]) -> list[str]:
    gorulen: dict[str, None] = {}
    for i in items:
        gorulen.setdefault(i, None)
    return list(gorulen)
