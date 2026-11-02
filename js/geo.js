// Coğrafi dönüşümler – tools/geo.py ile birebir aynı sabitler.
// Fiziki harita (HGK 1:180.000) konik projeksiyondadır; kenar işaretlerinden
// (28°30', 29°00', 29°30', 40°00', 40°30') kalibre edilmiştir.

const FRAME_X0 = 180, FRAME_Y0 = 180, FRAME_W = 10860, FRAME_H = 7907;
const CM_LON = 29.0, APEX_X = 5486.5, APEX_Y = -488024.0;
const THETA_PER_DEG = 0.011368, RHO_REF = 489203.8, LAT_REF = 40.5, PX_PER_DEG_LAT = 7286.6;

export const WORLD_W = 100;
export const WORLD_H = WORLD_W * FRAME_H / FRAME_W; // ≈ 72.81

// Harita kapsama alanı (yaklaşık "bounding box")
export const BBOX = {
  north: 40.6372, south: 39.5478, west: 28.0439, east: 30.0006,
  nw: [40.6333, 28.0439], se: [39.5478, 29.9847],
};

export function lonLatToUV(lon, lat) {
  const rho = RHO_REF + (LAT_REF - lat) * PX_PER_DEG_LAT;
  const th = THETA_PER_DEG * (lon - CM_LON);
  const x = APEX_X + rho * Math.sin(th);
  const y = APEX_Y + rho * Math.cos(th);
  return [(x - FRAME_X0) / FRAME_W, (y - FRAME_Y0) / FRAME_H];
}

export function uvToLonLat(u, v) {
  const dx = FRAME_X0 + u * FRAME_W - APEX_X;
  const dy = FRAME_Y0 + v * FRAME_H - APEX_Y;
  const rho = Math.hypot(dx, dy);
  return [CM_LON + Math.atan2(dx, dy) / THETA_PER_DEG, LAT_REF - (rho - RHO_REF) / PX_PER_DEG_LAT];
}

// u,v (0..1, kuzeybatı köşe orijin) → Three.js dünya x,z (+x doğu, +z güney)
export function uvToWorld(u, v) {
  return [(u - 0.5) * WORLD_W, (v - 0.5) * WORLD_H];
}

export function worldToUV(x, z) {
  return [x / WORLD_W + 0.5, z / WORLD_H + 0.5];
}

export function formatLatLon(lat, lon) {
  const f = (d, p, n) => {
    const a = Math.abs(d), deg = Math.floor(a), min = (a - deg) * 60;
    return `${deg}°${min.toFixed(2).padStart(5, '0')}′${d >= 0 ? p : n}`;
  };
  return `${f(lat, 'K', 'G')}  ${f(lon, 'D', 'B')}`;
}
