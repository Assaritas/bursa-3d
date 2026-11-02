"""
Bursa 3D – ortak coğrafi dönüşüm modülü (Python tarafı).

bursa_fiziki.webp, Harita Genel Müdürlüğü'nün 1:180.000 ölçekli Bursa Fiziki
Haritasıdır ve konik (Lambert benzeri) bir projeksiyondadır: meridyenler
kuzeye doğru hafifçe birbirine yaklaşır, paraleller hafif kavislidir.
Bu nedenle düz bir "enlem/boylam -> piksel" doğrusal dönüşümü yerine,
haritanın kenarındaki 28°30', 29°00', 29°30' meridyen ve 40°00', 40°30'
paralel işaretlerinden piksel hassasiyetinde kalibre edilmiş bir konik
dönüşüm kullanıyoruz.

Koordinat sistemleri:
  lon/lat  : WGS84 derece
  u, v     : harita çerçevesi içinde 0..1 (u: batı->doğu, v: kuzey->güney)
  x, z     : Three.js dünya koordinatı (zemin genişliği WORLD_W birim,
             merkez 0,0; +x doğu, +z güney). Yükseklik y eksenidir.

Aynı sabitler js/geo.js içinde de var; birini değiştirirsen diğerini de değiştir.
"""
import math

# --- Orijinal 11221x8268 px fiziki haritada iç çerçeve (neatline) ---
FRAME_X0, FRAME_Y0 = 180.0, 180.0
FRAME_X1, FRAME_Y1 = 11040.0, 8087.0
FRAME_W = FRAME_X1 - FRAME_X0  # 10860
FRAME_H = FRAME_Y1 - FRAME_Y0  # 7907

# --- Konik projeksiyon kalibrasyonu (tam çözünürlüklü piksel uzayında) ---
CM_LON = 29.0            # dik duran merkez meridyen (29°00')
APEX_X = 5486.5          # 29°00' meridyeninin x konumu = koninin tepe noktası x
APEX_Y = -488024.0       # meridyenlerin kesiştiği tepe noktası (çok kuzeyde)
THETA_PER_DEG = 0.011368 # boylam derecesi başına dönüş açısı (radyan), n≈0.651
RHO_REF = 489203.8       # 40°30' paralelinin tepe noktasına uzaklığı (px)
LAT_REF = 40.5
PX_PER_DEG_LAT = 7286.6  # paraleller arası mesafe (px / derece enlem)

# --- Three.js dünya ölçeği ---
WORLD_W = 100.0
WORLD_H = WORLD_W * FRAME_H / FRAME_W  # ≈ 72.81


def lonlat_to_px(lon, lat):
    rho = RHO_REF + (LAT_REF - lat) * PX_PER_DEG_LAT
    th = THETA_PER_DEG * (lon - CM_LON)
    return APEX_X + rho * math.sin(th), APEX_Y + rho * math.cos(th)


def px_to_lonlat(x, y):
    dx, dy = x - APEX_X, y - APEX_Y
    rho = math.hypot(dx, dy)
    th = math.atan2(dx, dy)
    return CM_LON + th / THETA_PER_DEG, LAT_REF - (rho - RHO_REF) / PX_PER_DEG_LAT


def lonlat_to_uv(lon, lat):
    x, y = lonlat_to_px(lon, lat)
    return (x - FRAME_X0) / FRAME_W, (y - FRAME_Y0) / FRAME_H


def uv_to_lonlat(u, v):
    return px_to_lonlat(FRAME_X0 + u * FRAME_W, FRAME_Y0 + v * FRAME_H)


def uv_to_world(u, v):
    """Three.js zemin düzlemi üzerindeki (x, z) konumu."""
    return (u - 0.5) * WORLD_W, (v - 0.5) * WORLD_H


def in_frame(u, v, margin=0.0):
    return -margin <= u <= 1 + margin and -margin <= v <= 1 + margin


def _bbox():
    pts = [uv_to_lonlat(u, v) for u in (0, 0.5, 1) for v in (0, 1)]
    lons = [p[0] for p in pts]
    lats = [p[1] for p in pts]
    return (round(min(lats), 4), round(min(lons), 4),
            round(max(lats), 4), round(max(lons), 4))


# Haritanın kapsadığı alanın zarf kutusu (south, west, north, east)
BBOX_SWNE = _bbox()
SOUTH, WEST, NORTH, EAST = BBOX_SWNE

# Bilgi amaçlı: kuzeybatı / güneydoğu köşeler
NW = uv_to_lonlat(0, 0)
SE = uv_to_lonlat(1, 1)

if __name__ == "__main__":
    print("Çerçeve köşeleri (lon, lat):")
    for name, (u, v) in {"KB (NW)": (0, 0), "KD (NE)": (1, 0),
                         "GB (SW)": (0, 1), "GD (SE)": (1, 1)}.items():
        lon, lat = uv_to_lonlat(u, v)
        print(f"  {name}: {lat:.4f}N {lon:.4f}E")
    print("Overpass bbox (S,W,N,E):", BBOX_SWNE)
    for name, ll in {"Uludağ zirve": (29.2214, 40.0708), "İznik": (29.7211, 40.4292),
                     "Mudanya": (28.8828, 40.3755)}.items():
        print(f"  {name}: uv={tuple(round(c, 4) for c in lonlat_to_uv(*ll))}")
    print("Dünya boyutu:", WORLD_W, "x", round(WORLD_H, 3))
