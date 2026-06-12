"""Müddetname (süre belgesi) taslağı üreticisi.

Şablon, 2324 sayılı CB Yönetmeliği md. 54/3'teki "süre belgesi" zorunlu
içeriğini esas alır. Çıktı Markdown'dır ve başında kalıcı "RESMÎ BELGE
DEĞİLDİR" ibaresi taşır.
"""

from __future__ import annotations

from datetime import date

from .tipler import InfazGirdisi, InfazSonucu


def _g(deger: str | None) -> str:
    return deger if deger else "—"


def muddetname_markdown(girdi: InfazGirdisi, sonuc: InfazSonucu) -> str:
    bugun = date.today().isoformat()
    sat: list[str] = []
    sat.append("# İNFAZ SÜRE BELGESİ (MÜDDETNAME) TASLAĞI")
    sat.append("")
    sat.append("> **RESMÎ BELGE DEĞİLDİR — TAHMİNÎ HESAPTIR.** Resmî müddetname, "
               "5275 sayılı Kanun ve 2324 sayılı Yönetmelik md. 54 uyarınca "
               "Cumhuriyet başsavcılığınca düzenlenir. Bu taslak yalnızca ön "
               "değerlendirme ve kontrol amaçlıdır.")
    sat.append("")
    sat.append(f"*Düzenlenme (taslak) tarihi: {bugun} · Kural sürümü: "
               f"{sonuc.kural_surumu} · Son doğrulama: {sonuc.son_dogrulama.isoformat()}*")
    sat.append("")
    sat.append("## Mahkûmiyet Bilgileri")
    sat.append("")
    sat.append("| Alan | Değer |")
    sat.append("|---|---|")
    sat.append(f"| Hükümlü | {_g(girdi.ad_soyad)} |")
    sat.append(f"| Mahkeme | {_g(girdi.mahkeme)} |")
    sat.append(f"| Esas / Karar No | {_g(girdi.esas_no)} / {_g(girdi.karar_no)} |")
    sat.append(f"| Suç (TCK) | madde {girdi.tck_madde} |")
    sat.append(f"| Suç tarihi | {girdi.suc_tarihi.isoformat()} |")
    sat.append(f"| Ceza süresi | {girdi.ceza_yil} yıl {girdi.ceza_ay} ay "
               f"{girdi.ceza_gun} gün |")
    sat.append(f"| İnfaza başlama | {girdi.infaz_baslangici.isoformat()} |")
    sat.append(f"| Mahsup (tutuklulukta geçen) | {sonuc.mahsup_gun} gün |")
    sat.append("")
    sat.append("## Hesaplanan Tarihler")
    sat.append("")
    sat.append("| Tarih | Değer |")
    sat.append("|---|---|")
    ds = sonuc.denetimli_serbestlik.isoformat() if sonuc.denetimli_serbestlik else "—"
    sat.append(f"| Denetimli serbestlik | {ds} |")
    sat.append(f"| Koşullu salıverilme | {sonuc.kosullu_saliverilme.isoformat()} |")
    sat.append(f"| Bihakkın (hak ederek) tahliye | {sonuc.bihakkin_tahliye.isoformat()} |")
    sat.append("")
    sat.append(f"- **Uygulanan KS oranı:** {sonuc.uygulanan_oran} "
               f"(kategori: {sonuc.uygulanan_kategori})")
    sat.append(f"- **DS rejimi:** {sonuc.uygulanan_ds_rejimi}")
    sat.append("")
    sat.append("## Hesap Dökümü")
    sat.append("")
    for d in sonuc.hesap_dokumu:
        sat.append(f"- {d}")
    sat.append("")
    sat.append("## Dayanaklar")
    sat.append("")
    for d in sonuc.dayanaklar:
        sat.append(f"- {d}")
    sat.append("")
    sat.append("## Uyarılar ve Değerlendirilmeyen Hususlar")
    sat.append("")
    for u in sonuc.uyarilar:
        sat.append(f"- {u}")
    sat.append("")
    return "\n".join(sat)
