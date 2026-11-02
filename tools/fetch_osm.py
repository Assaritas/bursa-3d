"""
Bursa 3D – OpenStreetMap (Overpass API) otomatik veri çekme scripti.

Bursa il sınırı (ISO3166-2 = TR-16) içindeki tarihi, dini, doğal, müze ve
ulaşım noktalarını; teleferik/demiryolu/fay çizgilerini ve il/ilçe
sınırlarını çeker, Three.js'in doğrudan okuyabileceği koordinatlara çevirir
ve ../data/data.js dosyasına yazar.

Ek olarak OSM'deki "wikipedia" / "wikidata" etiketlerinden Vikipedi
özetlerini indirip dosyaya gömer → uygulama tamamen çevrimdışı bilgi verir.

Bağımlılık YOK (yalnızca Python 3.8+ standart kütüphanesi).

Kullanım:
  python tools/fetch_osm.py                 # varsayılan: il sınırı + Vikipedi özetleri
  python tools/fetch_osm.py --no-wiki       # Vikipedi'siz, hızlı
  python tools/fetch_osm.py --mode bbox     # il sınırı yerine dikdörtgen kutu
  python tools/fetch_osm.py --max-wiki 150  # en fazla 150 özet indir
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import curated  # noqa: E402
from geo import (BBOX_SWNE, WORLD_W, WORLD_H, in_frame, lonlat_to_uv,  # noqa: E402
                 uv_to_world)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "tools", ".cache")
OUT_FILE = os.path.join(ROOT, "data", "data.js")

UA = "Bursa3D-TurRehberi/1.0 (egitim amacli; github pages)"
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
PROVINCE_ISO = "TR-16"
DISTRICT_NAMES = {"Osmangazi", "Nilüfer", "Yıldırım", "Gemlik", "İnegöl", "Mudanya",
                  "Mustafakemalpaşa", "Karacabey", "Orhangazi", "Yenişehir", "Gürsu",
                  "Kestel", "İznik", "Orhaneli", "Keles", "Büyükorhan", "Harmancık"}

# ---------------------------------------------------------------- HTTP

def http_get_json(url, data=None, timeout=240):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def overpass(query, label):
    cache = os.path.join(CACHE_DIR, f"overpass_{label}.json")
    body = urllib.parse.urlencode({"data": query}).encode()
    last = None
    for ep in ENDPOINTS:
        for attempt in range(2):
            try:
                print(f"  → {label}: {ep} (deneme {attempt + 1})", flush=True)
                res = http_get_json(ep, body)
                os.makedirs(CACHE_DIR, exist_ok=True)
                with open(cache, "w", encoding="utf-8") as f:
                    json.dump(res, f)
                print(f"    {len(res.get('elements', []))} öğe")
                return res
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                last = e
                print(f"    hata: {e}")
                time.sleep(5 * (attempt + 1))
    if os.path.exists(cache):
        print(f"  ! Sunuculara ulaşılamadı, önbellek kullanılıyor: {cache}")
        with open(cache, encoding="utf-8") as f:
            return json.load(f)
    raise RuntimeError(f"Overpass sorgusu başarısız ({label}): {last}")


# ---------------------------------------------------------------- sorgular

def scope_header(mode):
    s, w, n, e = BBOX_SWNE
    if mode == "bbox":
        return f"[out:json][timeout:240][bbox:{s},{w},{n},{e}];\n", ""
    return (f"[out:json][timeout:240];\n"
            f'area["ISO3166-2"="{PROVINCE_ISO}"]["admin_level"="4"]->.b;\n', "(area.b)")


def q_points(mode):
    head, A = scope_header(mode)
    return head + f"""(
  nwr["historic"]{A};
  nwr["tourism"="museum"]{A};
  nwr["amenity"="place_of_worship"]["religion"!="muslim"]{A};
  nwr["amenity"="place_of_worship"]["wikidata"]{A};
  nwr["amenity"="place_of_worship"]["wikipedia"]{A};
  nwr["amenity"="place_of_worship"]["heritage"]{A};
  nwr["amenity"="place_of_worship"]["historic"]{A};
  nwr["amenity"="place_of_worship"]["start_date"]{A};
  nwr["amenity"~"^(madrasa|caravanserai)$"]{A};
  nwr["building"~"^(madrasa|caravanserai|tomb|mausoleum)$"]["name"]{A};
  nwr["natural"~"^(peak|volcano|cave_entrance|waterfall|tree|gorge|cape|bay)$"]["name"]{A};
  nwr["natural"="spring"]["wikidata"]{A};
  nwr["waterway"="waterfall"]{A};
  nwr["natural"="water"]["name"]["water"~"^(lake|reservoir|lagoon)$"]{A};
  nwr["boundary"~"^(national_park|protected_area)$"]["name"]{A};
  nwr["leisure"="nature_reserve"]["name"]{A};
  nwr["tourism"="viewpoint"]["name"]{A};
  nwr["tourism"="attraction"]["name"]{A};
  nwr["aeroway"="aerodrome"]{A};
  nwr["aerialway"="station"]{A};
  nwr["railway"~"^(station|halt)$"]["name"]{A};
  nwr["amenity"="ferry_terminal"]{A};
);
out center tags;"""


def q_lines(mode):
    head, A = scope_header(mode)
    return head + f"""(
  way["geological"="fault"]{A};
  way["aerialway"~"^(cable_car|gondola|chair_lift|mixed_lift)$"]{A};
  way["railway"="rail"]["service"!~"."]{A};
  way["railway"="light_rail"]{A};
  way["route"="ferry"]{A};
);
out geom;"""


def q_boundaries():
    return f"""[out:json][timeout:240];
area["ISO3166-2"="{PROVINCE_ISO}"]["admin_level"="4"]->.b;
(
  rel["ISO3166-2"="{PROVINCE_ISO}"]["admin_level"="4"];
  rel["boundary"="administrative"]["admin_level"="6"](area.b);
);
out geom;"""


# ---------------------------------------------------------------- sınıflandırma

SKIP_HISTORIC = {"memorial", "wayside_cross", "wayside_shrine", "boundary_stone", "milestone",
                 "yes", "building", "house", "district", "railway_car", "locomotive", "aircraft",
                 "vehicle", "cannon", "anchor", "highwater_mark", "creamery", "charcoal_pile"}
ANTIK_HISTORIC = {"archaeological_site", "ruins", "tumulus", "ancient_city", "city_gate"}
TARIHI_HISTORIC = {"castle", "fort", "city_walls", "citywalls", "tower", "aqueduct", "bridge",
                   "caravanserai", "monument", "fountain", "bath", "hammam", "manor",
                   "church", "mosque", "tomb", "monastery", "palace", "mill", "well", "school"}
NAME_HAN = re.compile(r"\b(han|hanı|kervansaray)", re.I)
NAME_MEDRESE = re.compile(r"medrese", re.I)
NAME_TURBE = re.compile(r"türbe", re.I)
NAME_HOYUK = re.compile(r"höyü|hoyu|tümülüs", re.I)


def classify(t):
    """OSM etiketlerinden katman ve alt tür döndürür (yoksa None)."""
    name = t.get("name", "") or t.get("name:tr", "")
    h = t.get("historic")
    notable = any(k in t for k in ("wikidata", "wikipedia", "heritage"))

    if t.get("tourism") == "museum":
        return "muze", "Müze"
    if t.get("aeroway") == "aerodrome":
        return "ulasim", "Havalimanı"
    if t.get("aerialway") == "station":
        return "ulasim", "Teleferik istasyonu"
    if t.get("railway") in ("station", "halt"):
        return "ulasim", "Tren istasyonu"
    if t.get("amenity") == "ferry_terminal":
        return "ulasim", "İskele"

    if t.get("amenity") == "place_of_worship" or h in ("mosque", "church", "tomb", "monastery") \
            or t.get("building") in ("tomb", "mausoleum") or NAME_TURBE.search(name):
        rel = t.get("religion", "")
        if h == "tomb" or t.get("building") in ("tomb", "mausoleum") or NAME_TURBE.search(name):
            return "dini", "Türbe"
        if rel == "jewish":
            return "dini", "Havra / Sinagog"
        if rel == "christian" or h in ("church", "monastery"):
            return "dini", "Kilise"
        return "dini", "Tarihi cami"

    if h in ANTIK_HISTORIC or NAME_HOYUK.search(name):
        sub = {"archaeological_site": "Ören yeri", "ruins": "Kalıntı", "tumulus": "Tümülüs / Höyük",
               "city_gate": "Antik kapı"}.get(h, "Antik kent")
        if NAME_HOYUK.search(name):
            sub = "Höyük"
        return "antik", sub
    if t.get("amenity") == "madrasa" or t.get("building") == "madrasa" or NAME_MEDRESE.search(name):
        return "tarihi", "Medrese"
    if h == "caravanserai" or t.get("amenity") == "caravanserai" or t.get("building") == "caravanserai" \
            or (h and NAME_HAN.search(name)):
        return "tarihi", "Han / Kervansaray"
    if h in TARIHI_HISTORIC:
        sub = {"castle": "Kale", "fort": "Kale", "city_walls": "Sur", "citywalls": "Sur",
               "bridge": "Tarihi köprü", "aqueduct": "Su kemeri", "tower": "Kule",
               "fountain": "Çeşme", "bath": "Hamam", "hammam": "Hamam"}.get(h, "Tarihi yapı")
        if h in ("fountain", "mill", "well", "school") and not notable:
            return None
        return "tarihi", sub
    if h and h not in SKIP_HISTORIC:
        return "tarihi", "Tarihi yapı"
    if h in SKIP_HISTORIC and notable and name:
        return "tarihi", "Anıt / tarihi yer"

    n = t.get("natural")
    if n in ("peak", "volcano"):
        return "doga", "Zirve"
    if n == "waterfall" or t.get("waterway") == "waterfall":
        return "doga", "Şelale"
    if n == "cave_entrance":
        return "doga", "Mağara"
    if n == "water":
        return "doga", "Göl / Baraj gölü"
    if n == "tree":
        return "doga", "Anıt ağaç"
    if n in ("gorge", "cape", "bay", "spring"):
        return "doga", {"gorge": "Kanyon", "cape": "Burun", "bay": "Koy", "spring": "Kaynak"}[n]
    if t.get("boundary") in ("national_park", "protected_area") or t.get("leisure") == "nature_reserve":
        return "doga", "Milli park / Koruma alanı"
    if t.get("tourism") == "viewpoint":
        return "doga", "Seyir noktası"
    if t.get("tourism") == "attraction":
        return ("tarihi", "Turistik yer") if notable else None
    return None


def element_lonlat(el):
    if "lat" in el:
        return el["lon"], el["lat"]
    c = el.get("center")
    if c:
        return c["lon"], c["lat"]
    return None


# ---------------------------------------------------------------- geometri

def rdp(pts, eps):
    """Ramer–Douglas–Peucker çizgi sadeleştirme (u,v uzayında)."""
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-12
    dmax, idx = 0.0, 0
    for i in range(1, len(pts) - 1):
        x0, y0 = pts[i]
        d = abs(dy * x0 - dx * y0 + x2 * y1 - y2 * x1) / L
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def r5(x):
    return round(x, 5)


def to_uv_line(lonlats, eps=0.0006):
    uv = [lonlat_to_uv(lon, lat) for lon, lat in lonlats]
    uv = rdp(uv, eps)
    return [[r5(u), r5(v)] for u, v in uv]


def dist_m(lon1, lat1, lon2, lat2):
    k = 111320.0
    return math.hypot((lon2 - lon1) * k * math.cos(math.radians(lat1)), (lat2 - lat1) * k)


# ---------------------------------------------------------------- Vikipedi

def load_cache(name):
    p = os.path.join(CACHE_DIR, name)
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(name, obj):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def wikidata_sitelinks(qids, cache):
    todo = [q for q in qids if q not in cache]
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        url = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
               "&props=sitelinks|descriptions&sitefilter=trwiki|enwiki&languages=tr|en&ids="
               + "|".join(chunk))
        try:
            res = http_get_json(url, timeout=60)
        except Exception as e:  # noqa: BLE001
            print("    wikidata hata:", e)
            continue
        for q, ent in res.get("entities", {}).items():
            sl = ent.get("sitelinks", {})
            ds = ent.get("descriptions", {})
            cache[q] = {
                "tr": sl.get("trwiki", {}).get("title"),
                "en": sl.get("enwiki", {}).get("title"),
                "desc": (ds.get("tr") or ds.get("en") or {}).get("value"),
            }
        time.sleep(0.3)
    return cache


def wiki_fetch_batch(lang, titles, cache):
    """Vikipedi giriş paragraflarını 20'şerli toplu sorgu ile indirir (az istek = hız sınırı yok)."""
    titles = [t for t in dict.fromkeys(titles) if f"{lang}:{t}" not in cache]
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        url = (f"https://{lang}.wikipedia.org/w/api.php?action=query&format=json&formatversion=2"
               "&prop=extracts|info&inprop=url&exintro=1&explaintext=1&exlimit=20&redirects=1&titles="
               + urllib.parse.quote("|".join(chunk)))
        res = None
        for attempt in range(4):
            try:
                res = http_get_json(url, timeout=60)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    wait = int(e.headers.get("Retry-After", "0") or 0) or 10 * (attempt + 1)
                    print(f"    Vikipedi {e.code}, {wait} sn bekleniyor…")
                    time.sleep(wait)
                    continue
                print("    Vikipedi hata:", e)
                break
            except Exception as e:  # noqa: BLE001
                print("    Vikipedi hata:", e)
                time.sleep(3)
        if not res:
            continue  # önbelleğe yazma → sonraki çalıştırmada tekrar denenir
        q = res.get("query", {})
        # istenen başlık → son başlık (normalize + yönlendirme)
        alias = {t: t for t in chunk}
        for n in q.get("normalized", []):
            for k, v in alias.items():
                if v == n["from"]:
                    alias[k] = n["to"]
        for r in q.get("redirects", []):
            for k, v in alias.items():
                if v == r["from"]:
                    alias[k] = r["to"]
        pages = {p.get("title"): p for p in q.get("pages", [])}
        for t in chunk:
            p = pages.get(alias[t])
            if not p or p.get("missing") or not p.get("extract"):
                cache[f"{lang}:{t}"] = None
            else:
                cache[f"{lang}:{t}"] = {"extract": p["extract"], "title": p["title"],
                                        "url": p.get("fullurl") or
                                        f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(p['title'])}"}
        time.sleep(1.0)
    return cache


def trim(text, n=700):
    text = (text or "").strip()
    if len(text) <= n:
        return text
    cut = text[:n]
    p = cut.rfind(". ")
    return (cut[:p + 1] if p > n * 0.5 else cut.rstrip() + "…")


def parse_wiki_tag(val):
    if not val or ":" not in val:
        return None
    lang, title = val.split(":", 1)
    return lang.strip(), title.strip()


# ---------------------------------------------------------------- ana akış

def build(args):
    points, lines = [], []
    seen_names = {}

    # 1) Noktalar
    if not args.offline:
        res = overpass(q_points(args.mode), f"points_{args.mode}")
        elements = res.get("elements", [])
    else:
        elements = load_cache(f"overpass_points_{args.mode}.json").get("elements", [])

    for el in elements:
        t = el.get("tags", {})
        name = t.get("name:tr") or t.get("name")
        if not name:
            continue
        cl = classify(t)
        ll = element_lonlat(el)
        if not cl or not ll:
            continue
        layer, kind = cl
        u, v = lonlat_to_uv(*ll)
        if not in_frame(u, v):
            continue
        key = (layer, name.lower())
        # aynı isimli yakın kayıtları (ör. hem node hem way) tekilleştir
        if key in seen_names and dist_m(*seen_names[key], *ll) < 400:
            continue
        seen_names[key] = ll
        p = {
            "id": f"osm-{el['type'][0]}{el['id']}",
            "layer": layer, "kind": kind, "name": name,
            "lon": r5(ll[0]), "lat": r5(ll[1]), "u": r5(u), "v": r5(v),
            "src": "osm",
        }
        info = {}
        for k in ("description:tr", "description", "inscription", "ele", "start_date",
                  "heritage", "architect", "wikipedia", "wikidata", "website", "opening_hours",
                  "religion", "historic:civilization"):
            if t.get(k):
                info[k] = t[k]
        if info:
            p["tags"] = info
        if t.get("description:tr") or t.get("description"):
            p["desc"] = t.get("description:tr") or t.get("description")
        points.append(p)
    print(f"OSM noktaları: {len(points)}")

    # 2) Elle derlenmiş noktaları birleştir
    added = 0
    for i, c in enumerate(curated.POINTS):
        u, v = lonlat_to_uv(c["lon"], c["lat"])
        match = None
        base = c["name"].split("(")[0].split("–")[0].strip().lower()
        for p in points:
            if p["layer"] != c["layer"]:
                continue
            d = dist_m(p["lon"], p["lat"], c["lon"], c["lat"])
            pn = p["name"].lower()
            # aynı isim (göl, dağ gibi büyük alanlar: merkezleri uzak olabilir) ya da yakın + benzer isim
            if (pn == base and d < 20000) or \
                    (d < 350 and (base[:6] in pn or pn[:6] in base)):
                match = p
                break
        if match:
            match["name"] = c["name"]
            match["desc"] = c["desc"]  # rehber metni öncelikli
            if c.get("wiki"):  # rehberin seçtiği (Türkçe) madde öncelikli
                match.setdefault("tags", {})["wikipedia"] = c["wiki"]
            match["src"] = "osm+rehber"
            continue
        p = {"id": f"cur-{i}", "layer": c["layer"], "kind": None, "name": c["name"],
             "lon": c["lon"], "lat": c["lat"], "u": r5(u), "v": r5(v),
             "desc": c["desc"], "src": "rehber"}
        tags = {}
        if c.get("wiki"):
            tags["wikipedia"] = c["wiki"]
        if c.get("ele"):
            tags["ele"] = c["ele"]
        if tags:
            p["tags"] = tags
        if c.get("approx"):
            p["approx"] = True
        points.append(p)
        added += 1
    print(f"Rehber noktaları eklendi: {added} (diğerleri OSM kaydıyla birleşti)")

    # 3) Çizgiler (teleferik, demiryolu, fay)
    if not args.offline:
        res = overpass(q_lines(args.mode), f"lines_{args.mode}")
        lel = res.get("elements", [])
    else:
        lel = load_cache(f"overpass_lines_{args.mode}.json").get("elements", [])
    for el in lel:
        t = el.get("tags", {})
        geom = el.get("geometry")
        if not geom:
            continue
        if t.get("geological") == "fault":
            layer, kind = "fay", "Fay hattı (OSM)"
        elif "aerialway" in t:
            layer, kind = "ulasim", "Teleferik / Telesiyej"
        elif t.get("route") == "ferry":
            layer, kind = "ulasim", "Feribot / Deniz otobüsü hattı"
        elif t.get("railway") in ("rail", "light_rail"):
            layer, kind = "ulasim", "Raylı sistem" if t["railway"] == "light_rail" else "Demiryolu"
        else:
            continue
        coords = to_uv_line([(g["lon"], g["lat"]) for g in geom], eps=0.0004)
        lines.append({"id": f"osm-w{el['id']}", "layer": layer, "kind": kind,
                      "name": t.get("name", kind), "coords": coords,
                      "desc": t.get("description", ""), "src": "osm"})

    for i, c in enumerate(curated.LINES):
        coords = to_uv_line([(lon, lat) for lat, lon in c["coords"]], eps=0)
        lines.append({"id": f"cur-l{i}", "layer": c["layer"], "kind": "Şematik",
                      "name": c["name"], "desc": c["desc"], "coords": coords, "src": "rehber"})

    # 4) İl / ilçe sınırları
    if args.mode == "area" and not args.offline:
        try:
            res = overpass(q_boundaries(), "boundaries")
        except RuntimeError as e:
            print("Sınırlar alınamadı:", e)
            res = {"elements": []}
    else:
        res = load_cache("overpass_boundaries.json")
    seen_ways = set()
    # önce il (4), sonra ilçe (6): ortak sınır parçaları "İl sınırı" olarak kalsın
    rels = sorted(res.get("elements", []), key=lambda e: e.get("tags", {}).get("admin_level", "9"))
    for el in rels:
        if el.get("type") != "relation":
            continue
        t = el.get("tags", {})
        lvl = t.get("admin_level")
        nm = t.get("name", "")
        if lvl == "6" and nm not in DISTRICT_NAMES:
            continue  # komşu illerin ilçeleri
        for m in el.get("members", []):
            if m.get("type") != "way" or not m.get("geometry") or m["ref"] in seen_ways:
                continue
            if m.get("role") not in ("outer", "", "inner"):
                continue
            seen_ways.add(m["ref"])
            coords = to_uv_line([(g["lon"], g["lat"]) for g in m["geometry"]], eps=0.0005)
            if len(coords) < 2:
                continue
            lines.append({"id": f"b-{m['ref']}", "layer": "sinir",
                          "kind": "İl sınırı" if lvl == "4" else "İlçe sınırı",
                          "level": int(lvl), "name": nm, "coords": coords, "src": "osm"})
    # il sınırı ile ilçe sınırı aynı yolu paylaşıyorsa "İl sınırı" olarak işaretlenir
    print(f"Çizgiler: {len(lines)}")

    labels = []
    for nm, lat, lon in curated.DISTRICTS:
        u, v = lonlat_to_uv(lon, lat)
        labels.append({"name": nm, "u": r5(u), "v": r5(v), "layer": "sinir"})

    # 5) Vikipedi özetleri
    if args.wiki:
        wcache = load_cache("wiki.json")
        qcache = load_cache("wikidata.json")
        qids = [p["tags"]["wikidata"] for p in points if p.get("tags", {}).get("wikidata")]
        if qids and not args.offline:
            print(f"Wikidata bağlantıları: {len(qids)}")
            wikidata_sitelinks(qids, qcache)
            save_cache("wikidata.json", qcache)
        # eski sürümün önbelleğe yazdığı hata kayıtlarını temizle
        wcache = {k: v for k, v in wcache.items() if not (v and "error" in v)}
        # önce rehber noktaları, sonra Vikipedi bağlantısı olanlar
        cands = sorted(points, key=lambda p: (p["src"] == "osm", p["name"]))
        wanted = []  # (nokta, dil, başlık)
        for p in cands:
            tg = p.get("tags", {})
            wt = parse_wiki_tag(tg.get("wikipedia"))
            wd = qcache.get(tg.get("wikidata", ""), {}) if tg.get("wikidata") else {}
            if wd.get("tr") and (not wt or wt[0] != "tr"):
                wt = ("tr", wd["tr"])  # Türkçe madde varsa onu tercih et
            elif not wt and wd.get("en"):
                wt = ("en", wd["en"])
            if not wt:
                if wd.get("desc") and not p.get("desc"):
                    p["desc"] = wd["desc"]
                continue
            if len(wanted) < args.max_wiki:
                wanted.append((p, wt[0], wt[1]))
        if not args.offline:
            for lang in sorted({w[1] for w in wanted}):
                titles = [w[2] for w in wanted if w[1] == lang]
                print(f"  Vikipedi ({lang}): {len(titles)} madde")
                wiki_fetch_batch(lang, titles, wcache)
                save_cache("wiki.json", wcache)
        for p, lang, title in wanted:
            s = wcache.get(f"{lang}:{title}")
            if s and s.get("extract"):
                p["wiki"] = {"lang": lang, "title": s["title"], "url": s["url"],
                             "extract": trim(s["extract"])}
        save_cache("wiki.json", wcache)
        print(f"Vikipedi özetleri: {sum(1 for p in points if 'wiki' in p)}")

    # 6) Three.js dünya koordinatları (x, z) – kolay kullanım için
    for p in points:
        x, z = uv_to_world(p["u"], p["v"])
        p["x"], p["z"] = round(x, 3), round(z, 3)

    counts = {}
    for p in points:
        counts[p["layer"]] = counts.get(p["layer"], 0) + 1
    for ln in lines:
        counts[ln["layer"]] = counts.get(ln["layer"], 0) + 1

    return {
        "meta": {
            "generated": dt.datetime.now().isoformat(timespec="seconds"),
            "source": "© OpenStreetMap katkıcıları (ODbL), Vikipedi (CC BY-SA), rehber notları",
            "mode": args.mode,
            "bbox_swne": BBOX_SWNE,
            "world": {"width": WORLD_W, "height": round(WORLD_H, 4),
                      "note": "x = (u-0.5)*width, z = (v-0.5)*height; +x doğu, +z güney"},
            "counts": counts,
        },
        "points": points,
        "lines": lines,
        "labels": labels,
    }


def main():
    ap = argparse.ArgumentParser(description="Bursa OSM verisini data/data.js'e çeker.")
    ap.add_argument("--mode", choices=["area", "bbox"], default="area",
                    help="area: il sınırı (TR-16) içi [varsayılan]; bbox: harita kutusu")
    ap.add_argument("--no-wiki", dest="wiki", action="store_false", help="Vikipedi özetlerini çekme")
    ap.add_argument("--max-wiki", type=int, default=400, help="en fazla kaç Vikipedi özeti (400)")
    ap.add_argument("--offline", action="store_true", help="yalnızca tools/.cache verisini kullan")
    ap.add_argument("--out", default=OUT_FILE)
    args = ap.parse_args()

    print("Bounding box (S,W,N,E):", BBOX_SWNE)
    data = build(args)
    if args.mode == "area" and len(data["points"]) <= len(curated.POINTS):
        print("! İl sınırı sorgusu boş döndü; bbox moduyla tekrar deneniyor…")
        args.mode = "bbox"
        data = build(args)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    js = ("/* Otomatik üretildi: tools/fetch_osm.py – elle düzenleme yerine tools/curated.py'yi düzenleyin */\n"
          "window.BURSA_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"\nYazıldı: {args.out}  ({len(js) / 1024:.0f} KB)")
    print("Katman sayıları:", data["meta"]["counts"])


if __name__ == "__main__":
    main()
