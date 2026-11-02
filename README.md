# Bursa 3D Rehber

Bursa'nın yer şekillerini, tarihini ve coğrafyasını gösteren, **çevrimdışı çalışan** (PWA)
interaktif 3B harita. Three.js + OpenStreetMap + Vikipedi.

## Klasör yapısı

```
bursa-3d/
├── index.html               ← uygulama sayfası (importmap ile yerel Three.js)
├── manifest.webmanifest     ← PWA tanımı (ana ekrana ekle)
├── sw.js                    ← service worker: çevrimdışı önbellek
├── css/style.css            ← arayüz (lejant, bilgi kartı, mobil alt sayfa)
├── js/
│   ├── main.js              ← sahne, kamera, OrbitControls, etkileşim, PWA kaydı
│   ├── config.js            ← katmanlar, renkler, ikonlar, kaydırıcı aralığı
│   ├── geo.js               ← enlem/boylam ↔ harita (u,v) ↔ Three.js (x,z) dönüşümü
│   ├── terrain.js           ← zemin: harita dokusu + displacement map + kenar blokları
│   ├── layers.js            ← pinler, fay/sınır/teleferik çizgileri, ilçe etiketleri
│   └── ui.js                ← lejant menüsü, kaydırıcı, arama, tooltip, bilgi kartı
├── data/data.js             ← OTOMATİK üretilir (tools/fetch_osm.py)
├── assets/
│   ├── map_4096.webp        ← fiziki harita (masaüstü)   } tools/prepare_assets.py
│   ├── map_2048.webp        ← fiziki harita (mobil)      } üretir
│   ├── height.png           ← hizalanmış yükseklik haritası
│   └── icons/               ← PWA ikonları
├── vendor/                  ← Three.js r170 (CDN'e bağımlılık yok → tam çevrimdışı)
│   ├── three.module.min.js
│   ├── controls/OrbitControls.js
│   └── lines/*.js           ← kalın çizgiler (Line2)
└── tools/
    ├── geo.py               ← bounding box + projeksiyon (js/geo.js ile aynı sabitler)
    ├── prepare_assets.py    ← ham görselleri web'e hazırlar (bir kez)
    ├── fetch_osm.py         ← Overpass + Vikipedi → data/data.js
    ├── curated.py           ← rehber notları, şematik fay hatları, ilçe merkezleri
    └── requirements.txt
```

## Koordinatlar (bounding box)

Fiziki harita HGK 1:180.000 ölçekli olup **konik projeksiyondadır**. Kenarındaki
28°30′, 29°00′, 29°30′ meridyen ve 40°00′, 40°30′ paralel işaretleri piksel
hassasiyetinde ölçülerek kalibre edildi:

| Köşe | Enlem | Boylam |
|---|---|---|
| Kuzeybatı (NW) | 40.6333° K | 28.0439° D |
| Güneydoğu (SE) | 39.5478° K | 29.9847° D |
| Overpass bbox (S,W,N,E) | `39.5478, 28.0439, 40.6372, 30.0006` | |

Yükseklik haritası (`bursa_heightmap.webp`) kare olduğu ve güneye doğru daha geniş bir
alanı kapsadığı için, deniz/göl kıyı çizgileri eşleştirilerek fiziki haritaya oturtuldu
(`prepare_assets.py` içindeki `HA, HB, HC, HD`).

`data.js` içinde her nokta için `lon/lat`, harita oranı `u/v` (0–1) ve Three.js dünya
koordinatı `x/z` bulunur (zemin 100 × 72.8 birim, merkez 0,0; +x doğu, +z güney).

## Bilgisayarında çalıştırma

```bash
# 1) Python bağımlılıkları (yalnızca görsel hazırlama için)
pip install -r tools/requirements.txt

# 2) Görselleri hazırla (bir kez; ham dosyalar bir üst klasördeyse yol vermene gerek yok)
python tools/prepare_assets.py --map ../bursa_fiziki.webp --height ../bursa_heightmap.webp

# 3) OSM + Vikipedi verisini çek (1-5 dk; sunucu yoğunsa kendisi yeniden dener)
python tools/fetch_osm.py
#   --no-wiki        Vikipedi özetlerini atla
#   --mode bbox      il sınırı yerine dikdörtgen kutuyla sorgula
#   --offline        yalnızca tools/.cache'teki son veriyi kullan (internet yokken)

# 4) Yerel sunucu (ES modülleri file:// ile çalışmaz)
python -m http.server 8000
#   → http://localhost:8000
```

Windows'ta Türkçe karakterler bozuk görünürse: `python -X utf8 tools/fetch_osm.py`

## Kendi anlatımını ekleme

`tools/curated.py` → `POINTS` listesine ekle ya da `desc` metinlerini değiştir, sonra
`python tools/fetch_osm.py --offline` çalıştır (internet gerekmez). Rehber metni, aynı yerin
OSM açıklamasının önüne geçer.

**Derin bağlantı:** `https://.../bursa-3d/?yer=Ulu Cami` doğrudan o noktaya uçar ve bilgi
kartını açar. Her durak için QR kod hazırlayabilirsin.

## GitHub Pages'e yükleme (tek link)

1. https://github.com adresinde hesap aç → sağ üstte **+ → New repository**.
   Ad: `bursa-3d`, **Public**, "Add a README" işaretleme → **Create repository**.
2. Bilgisayarında bu klasörde:
   ```bash
   git init
   git add .
   git commit -m "Bursa 3D rehber"
   git branch -M main
   git remote add origin https://github.com/KULLANICI_ADIN/bursa-3d.git
   git push -u origin main
   ```
   (Git kullanmak istemezsen: repo sayfasında **Add file → Upload files** ile klasörün
   içeriğini sürükle-bırak yap. `tools/.cache` klasörünü yüklemene gerek yok.)
3. Repo → **Settings → Pages** → *Source*: **Deploy from a branch**, *Branch*: `main`,
   klasör `/ (root)` → **Save**.
4. 1-2 dakika sonra link hazır: `https://KULLANICI_ADIN.github.io/bursa-3d/`

### Misafirlere sunma

- Linki veya QR kodunu paylaş. Misafir **bir kez internetteyken** açtığında (otel Wi-Fi'si)
  tüm dosyalar telefona kaydedilir; ekranda "✓ Çevrimdışı kullanıma hazır" yazar.
- Sonrasında uçak modunda bile çalışır. Android/Chrome'da **Uygulamayı yükle** düğmesi,
  iPhone/Safari'de **Paylaş → Ana Ekrana Ekle** ile uygulama gibi açılır.
- Toplam indirme mobilde ≈ 2 MB, masaüstünde ≈ 4 MB.

### Güncelleme yaptığında

Dosyaları değiştirdikten sonra `sw.js` içindeki `VERSION` değerini artır
(`bursa3d-v1` → `bursa3d-v2`) ve tekrar push et. Aksi halde misafirlerin cihazı eski
önbelleği kullanmaya devam eder.

### Alternatifler

- **Netlify Drop** (https://app.netlify.com/drop): klasörü sürükle-bırak → anında link.
- **Cloudflare Pages**: GitHub reposunu bağla; şifre korumalı erişim (Cloudflare Access) eklenebilir.

## Telif ve lisans notları

- **Fiziki harita © Harita Genel Müdürlüğü.** Haritanın üzerindeki not, yazılı izin
  alınmadan çoğaltılmasını ve yayımlanmasını yasaklıyor. Herkese açık bir siteye
  koymadan önce HGK'dan izin al ya da linki yalnızca misafirlerinle paylaşabileceğin
  şifreli bir ortamda (ör. Cloudflare Access) yayımla. Alternatif olarak açık lisanslı
  bir doku (OpenTopoMap, Sentinel-2 uydu görüntüsü) kullanılabilir.
- OSM verisi ODbL lisanslıdır: "© OpenStreetMap katkıcıları" atfı uygulamada mevcut.
- Vikipedi özetleri CC BY-SA lisanslıdır.
- Fay hatları MTA Diri Fay Haritası'ndan sadeleştirilmiş **şematik** çizimlerdir.
  Yalnızca anlatım içindir.
