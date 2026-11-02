"""
Bursa 3D – görsel hazırlama scripti (bir kez çalıştırılır).

Ham görsellerden web'e uygun, birbirine hizalı dokular üretir:
  assets/map_4096.webp   – fiziki harita, iç çerçeveye kırpılmış (masaüstü)
  assets/map_2048.webp   – aynı harita, mobil için hafif sürüm
  assets/height.png      – yükseklik haritası, fiziki haritanın çerçevesine
                           hizalanmış (gri tonlamalı, 1024 px)
  assets/icons/*.png     – PWA ikonları

Neden gerekli?
  * 11221x8268 px'lik orijinal harita mobil GPU'ların doku sınırını
    (genelde 4096 px) aşar; tarayıcı ya çöker ya da siyah ekran gösterir.
  * bursa_heightmap.webp kare (2624x2548) ve fiziki haritadan farklı bir
    alanı kapsıyor (güneye doğru daha uzun). Deniz kıyısı, Gemlik Körfezi ve
    İznik Gölü kıyı çizgileri eşleştirilerek bulunan afin dönüşümle haritaya
    oturtulur.

Kullanım:
  pip install pillow numpy
  python tools/prepare_assets.py --map ../bursa_fiziki.webp --height ../bursa_heightmap.webp
"""
import argparse
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from geo import FRAME_X0, FRAME_Y0, FRAME_X1, FRAME_Y1

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Yükseklik haritasının (u,v ∈ 0..1) fiziki harita çerçevesine (X,Y ∈ 0..1)
# dönüşümü:  X = HA*u + HB ,  Y = HC*v + HD
# (su kütlesi maskelerinin çapraz korelasyonu ile bulundu)
HA, HB = 1.048, 0.004
HC, HD = 1.266, -0.030

# Kartaltepe (Uludağ) ≈ 2543 m; yükseklik haritasındaki en parlak değer.
SUMMIT_M = 2543


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", default=os.path.join(ROOT, "..", "bursa_fiziki.webp"))
    ap.add_argument("--height", default=os.path.join(ROOT, "..", "bursa_heightmap.webp"))
    ap.add_argument("--out", default=os.path.join(ROOT, "assets"))
    args = ap.parse_args()
    os.makedirs(os.path.join(args.out, "icons"), exist_ok=True)

    # 1) Fiziki harita: çerçeveye kırp + yeniden boyutlandır
    src = Image.open(args.map).convert("RGB")
    frame = src.crop((int(FRAME_X0), int(FRAME_Y0), int(FRAME_X1), int(FRAME_Y1)))
    fw, fh = frame.size
    for w, q in ((4096, 82), (2048, 80)):
        h = round(w * fh / fw)
        out = os.path.join(args.out, f"map_{w}.webp")
        frame.resize((w, h), Image.LANCZOS).save(out, "WEBP", quality=q, method=6)
        print("yazıldı:", out, (w, h), f"{os.path.getsize(out) / 1e6:.2f} MB")

    # 2) Yükseklik haritası: harita çerçevesine hizala
    hm = Image.open(args.height).convert("L")
    hw, hh = hm.size
    OW = 1024
    OH = round(OW * fh / fw)
    # çıktı pikseli (x,y) -> girdi pikseli: u = ((x/OW) - HB)/HA
    coef = (hw / (HA * OW), 0, -HB / HA * hw,
            0, hh / (HC * OH), -HD / HC * hh)
    aligned = hm.transform((OW, OH), Image.AFFINE, coef, Image.BICUBIC, fillcolor=0)
    # webp sıkıştırma basamaklarını yumuşat
    aligned = aligned.filter(ImageFilter.GaussianBlur(1.2))
    arr = np.array(aligned)
    out = os.path.join(args.out, "height.png")
    aligned.save(out, optimize=True)
    print("yazıldı:", out, (OW, OH), "min/max:", arr.min(), arr.max(),
          f"→ 1 birim ≈ {SUMMIT_M / max(1, int(np.array(hm).max())):.1f} m")

    # 3) PWA ikonları
    for s in (192, 512):
        im = Image.new("RGB", (s, s), (18, 32, 38))
        d = ImageDraw.Draw(im)
        k = s / 512
        d.polygon([(40 * k, 400 * k), (200 * k, 150 * k), (280 * k, 260 * k),
                   (340 * k, 190 * k), (472 * k, 400 * k)], fill=(214, 170, 110))
        d.polygon([(200 * k, 150 * k), (240 * k, 212 * k), (215 * k, 200 * k),
                   (180 * k, 222 * k)], fill=(245, 245, 240))
        d.rectangle([40 * k, 400 * k, 472 * k, 430 * k], fill=(80, 170, 210))
        d.ellipse([330 * k, 70 * k, 400 * k, 140 * k], fill=(240, 200, 90))
        out = os.path.join(args.out, "icons", f"icon-{s}.png")
        im.save(out)
        print("yazıldı:", out)


if __name__ == "__main__":
    main()
