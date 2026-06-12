"""Takvim aritmetiği — TCK md. 61/6 sözleşmesi.

TCK 61/6: "Hapis cezasının süresi gün, ay ve yıl hesabıyla belirlenir.
Bir gün, yirmidört saat; bir ay, otuz gündür. Yıl, resmî takvime göre
hesap edilir. Hapis cezası için bir günün artakalanı hesaba katılmaz."

⚠️ YÖNTEM NOTU (Faz 5'te gerçek müddetname ile doğrulanacak):
İnfaz hesabında yaygın uygulama, cezayı GÜN cinsine çevirirken 1 yıl = 365,
1 ay = 30 gün saymaktır. Oran (KS) uygulanırken çıkan kesirli gün ATILIR
(artakalan infaz edilmez — hükümlü lehine). Bir tarihe gün eklenirken
gerçek takvim kullanılır (timedelta). Bu modül o sözleşmeyi tek yerde
toplar; doğrulama sonrası yalnız burası değişir.
"""

from __future__ import annotations

from datetime import date, timedelta
from fractions import Fraction

GUN_YIL = 365
GUN_AY = 30


def sure_gune_cevir(yil: int, ay: int, gun: int) -> int:
    """Yıl/ay/gün cinsinden süreyi toplam güne çevirir (yıl=365, ay=30)."""
    return yil * GUN_YIL + ay * GUN_AY + gun


def oran_uygula(toplam_gun: int, oran: Fraction) -> int:
    """Süreye oran uygular; kesirli gün atılır (TCK 61/6 — lehe yuvarlama)."""
    return (toplam_gun * oran.numerator) // oran.denominator


def gun_ekle(baslangic: date, gun: int) -> date:
    """Bir tarihe gerçek takvim günü ekler/çıkarır."""
    return baslangic + timedelta(days=gun)


def araliklar_toplam_gun(araliklar: list[tuple[date, date]]) -> int:
    """Tutukluluk aralıklarından toplam mahsup gününü hesaplar.

    Her aralık her iki ucu dahil sayılır (giriş günü de mahsup edilir).
    Çakışan aralıklar birleştirilerek çift sayım önlenir.
    """
    if not araliklar:
        return 0
    sirali = sorted(araliklar, key=lambda a: a[0])
    birlesik: list[list[date]] = [[sirali[0][0], sirali[0][1]]]
    for bas, bit in sirali[1:]:
        son = birlesik[-1]
        if bas <= son[1] + timedelta(days=1):  # bitişik veya çakışan
            son[1] = max(son[1], bit)
        else:
            birlesik.append([bas, bit])
    return sum((bit - bas).days + 1 for bas, bit in birlesik)


def gun_to_metin(gun: int) -> str:
    """Gün sayısını 'X yıl Y ay Z gün' biçiminde okunur metne çevirir."""
    isaret = "-" if gun < 0 else ""
    g = abs(gun)
    yil, kalan = divmod(g, GUN_YIL)
    ay, gn = divmod(kalan, GUN_AY)
    parcalar = []
    if yil:
        parcalar.append(f"{yil} yıl")
    if ay:
        parcalar.append(f"{ay} ay")
    if gn or not parcalar:
        parcalar.append(f"{gn} gün")
    return isaret + " ".join(parcalar)
