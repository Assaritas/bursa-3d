// Katmanlar: pinler (sprite), zemine yapışık çizgiler (fay, sınır, teleferik) ve etiketler
import * as THREE from 'three';
import { LineSegments2 } from '../vendor/lines/LineSegments2.js';
import { LineSegmentsGeometry } from '../vendor/lines/LineSegmentsGeometry.js';
import { LineMaterial } from '../vendor/lines/LineMaterial.js';
import { LAYERS, LAYER_BY_ID, PIN_PX, LABEL_PX } from './config.js';
import { uvToWorld } from './geo.js';

const DPR = Math.min(window.devicePixelRatio || 1, 2);

// ---- Pin dokusu (renkli damla + emoji) ----
function makePinTexture(color, icon) {
  const W = 64 * DPR, H = 80 * DPR;
  const c = document.createElement('canvas');
  c.width = W; c.height = H;
  const g = c.getContext('2d');
  g.scale(DPR, DPR);
  g.shadowColor = 'rgba(0,0,0,.45)';
  g.shadowBlur = 6; g.shadowOffsetY = 2;
  g.beginPath();
  g.moveTo(32, 78);
  g.bezierCurveTo(26, 62, 6, 50, 6, 30);
  g.arc(32, 30, 26, Math.PI, 0);
  g.bezierCurveTo(58, 50, 38, 62, 32, 78);
  g.closePath();
  g.fillStyle = color;
  g.fill();
  g.shadowColor = 'transparent';
  g.lineWidth = 3; g.strokeStyle = '#fff'; g.stroke();
  g.beginPath(); g.arc(32, 30, 19, 0, Math.PI * 2); g.fillStyle = 'rgba(255,255,255,.92)'; g.fill();
  g.font = '22px "Segoe UI Emoji","Apple Color Emoji","Noto Color Emoji",sans-serif';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText(icon, 32, 31);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function makeLabelTexture(text) {
  const fs = 28 * DPR;
  const c = document.createElement('canvas');
  const g = c.getContext('2d');
  const font = `600 ${fs}px system-ui, "Segoe UI", Roboto, sans-serif`;
  g.font = font;
  const w = Math.ceil(g.measureText(text).width) + 16 * DPR;
  c.width = w; c.height = fs * 1.5;
  g.font = font;
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.lineJoin = 'round';
  g.lineWidth = 6 * DPR; g.strokeStyle = 'rgba(20,24,28,.85)';
  g.strokeText(text, w / 2, c.height / 2);
  g.fillStyle = '#fff';
  g.fillText(text, w / 2, c.height / 2);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return { tex: t, aspect: w / c.height };
}

// Çizgiyi u,v uzayında sıklaştır (zemin kabartısını takip etsin)
function densify(coords, step = 0.0035) {
  const out = [];
  for (let i = 0; i < coords.length - 1; i++) {
    const [u0, v0] = coords[i], [u1, v1] = coords[i + 1];
    const n = Math.max(1, Math.ceil(Math.hypot(u1 - u0, v1 - v0) / step));
    for (let k = 0; k < n; k++) out.push([u0 + (u1 - u0) * k / n, v0 + (v1 - v0) * k / n]);
  }
  out.push(coords[coords.length - 1]);
  return out;
}

export function createLayers({ scene, terrain, data, camera, renderer }) {
  const root = new THREE.Group();
  root.name = 'layers';
  scene.add(root);

  const groups = {};
  for (const L of LAYERS) {
    const g = new THREE.Group();
    g.name = L.id;
    g.visible = L.on;
    root.add(g);
    groups[L.id] = g;
  }

  const isCoarse = matchMedia('(pointer: coarse)').matches;
  const pinPx = isCoarse ? PIN_PX.mobile : PIN_PX.desktop;

  // ---------------- Pinler ----------------
  const pinMats = {};
  const pins = [];
  for (const p of data.points || []) {
    const L = LAYER_BY_ID[p.layer];
    if (!L) continue;
    if (!pinMats[L.id]) {
      pinMats[L.id] = new THREE.SpriteMaterial({
        map: makePinTexture(L.color, L.icon),
        sizeAttenuation: false, depthTest: false, transparent: true,
      });
    }
    const s = new THREE.Sprite(pinMats[L.id]);
    s.center.set(0.5, 0.02);
    s.renderOrder = 20;
    s.userData = { point: p };
    groups[L.id].add(s);
    pins.push(s);
  }

  // ---------------- Etiketler (ilçe adları) ----------------
  const labels = [];
  for (const lb of data.labels || []) {
    const { tex, aspect } = makeLabelTexture(lb.name);
    const m = new THREE.SpriteMaterial({ map: tex, sizeAttenuation: false, depthTest: false, transparent: true });
    const s = new THREE.Sprite(m);
    s.center.set(0.5, 0);
    s.renderOrder = 15;
    s.userData = { label: lb, aspect };
    (groups[lb.layer] || groups.sinir).add(s);
    labels.push(s);
  }

  // ---------------- Çizgiler ----------------
  // Aynı katman + stil için tek LineSegments2 (tek çizim çağrısı)
  const lineSets = [];
  const pickLines = []; // tıklanabilir adlandırılmış çizgiler (fay, teleferik)
  const buckets = new Map();
  for (const ln of data.lines || []) {
    const L = LAYER_BY_ID[ln.layer];
    if (!L || !ln.coords || ln.coords.length < 2) continue;
    let style = 'main';
    if (ln.layer === 'sinir') style = ln.level === 4 ? 'il' : 'ilce';
    if (ln.layer === 'ulasim') style = /Demiryolu|Raylı/.test(ln.kind || '') ? 'rail' : /Feribot/.test(ln.kind || '') ? 'ferry' : 'cable';
    const key = ln.layer + ':' + style;
    if (!buckets.has(key)) buckets.set(key, { layer: ln.layer, style, items: [] });
    const pts = densify(ln.coords);
    buckets.get(key).items.push(pts);
    if (ln.layer === 'fay' || ln.layer === 'ulasim') pickLines.push({ line: ln, pts });
  }

  const STYLE = {
    'fay:main': { color: '#e03131', width: 4, dashed: true, lift: 0.3 },
    'sinir:il': { color: '#ffffff', width: 3.2, lift: 0.28 },
    'sinir:ilce': { color: '#ffffff', width: 1.5, opacity: 0.7, lift: 0.25 },
    'ulasim:cable': { color: '#1c5fb8', width: 3, lift: 0.6 },
    'ulasim:rail': { color: '#333', width: 2.4, dashed: true, lift: 0.25 },
    'ulasim:ferry': { color: '#1f7ad1', width: 2, dashed: true, lift: 0.1 },
  };

  for (const b of buckets.values()) {
    const st = STYLE[`${b.layer}:${b.style}`] || { color: LAYER_BY_ID[b.layer].color, width: 2, lift: 0.12 };
    const mat = new LineMaterial({
      color: new THREE.Color(st.color).getHex(),
      linewidth: st.width,
      worldUnits: false,
      dashed: !!st.dashed,
      dashSize: 0.7, gapSize: 0.45,
      transparent: true,
      opacity: st.opacity ?? 1,
      depthTest: true,
    });
    // u,v dizileri – yükseklik değişince yeniden hesaplanacak
    const segUV = [];
    for (const pts of b.items) {
      for (let i = 0; i < pts.length - 1; i++) segUV.push(pts[i], pts[i + 1]);
    }
    const geo = new LineSegmentsGeometry();
    const obj = new LineSegments2(geo, mat);
    obj.renderOrder = 10;
    obj.frustumCulled = false;
    groups[b.layer].add(obj);
    lineSets.push({ obj, geo, mat, segUV, lift: st.lift, dashed: !!st.dashed });
  }

  // ---------------- Yükseklik güncelleme ----------------
  const tmp = new THREE.Vector3();
  function updateHeights() {
    const S = terrain.scale;
    for (const s of pins) {
      const p = s.userData.point;
      const [x, z] = uvToWorld(p.u, p.v);
      s.position.set(x, terrain.heightAt(p.u, p.v) * S + 0.05, z);
    }
    for (const s of labels) {
      const lb = s.userData.label;
      const [x, z] = uvToWorld(lb.u, lb.v);
      s.position.set(x, terrain.heightAt(lb.u, lb.v) * S + 0.1, z);
    }
    for (const ls of lineSets) {
      const arr = new Float32Array(ls.segUV.length * 3);
      ls.segUV.forEach(([u, v], i) => {
        const [x, z] = uvToWorld(u, v);
        arr[i * 3] = x;
        arr[i * 3 + 1] = terrain.heightAt(u, v) * S + ls.lift + S * 0.05;
        arr[i * 3 + 2] = z;
      });
      ls.geo.setPositions(arr);
      if (ls.dashed) ls.obj.computeLineDistances();
    }
  }

  // ---------------- Ekran boyutu ----------------
  function resize(w, h) {
    const k = 2 * Math.tan(THREE.MathUtils.degToRad(camera.fov) / 2) / h;
    for (const s of pins) {
      const f = s === selected ? 1.3 : 1;
      s.scale.set(pinPx * 0.8 * k * f, pinPx * k * f, 1);
    }
    for (const s of labels) s.scale.set(LABEL_PX * 1.5 * s.userData.aspect * k, LABEL_PX * 1.5 * k, 1);
    for (const ls of lineSets) ls.mat.resolution.set(w, h);
  }

  // ---------------- Seçim (ekran uzayında, dokunmatik dostu) ----------------
  function toScreen(v, rect) {
    tmp.copy(v).project(camera);
    if (tmp.z > 1) return null;
    return [(tmp.x * 0.5 + 0.5) * rect.width, (-tmp.y * 0.5 + 0.5) * rect.height];
  }

  function pick(clientX, clientY) {
    const rect = renderer.domElement.getBoundingClientRect();
    const mx = clientX - rect.left, my = clientY - rect.top;
    const tol = isCoarse ? 26 : 18;
    let best = null, bestD = Infinity;
    for (const s of pins) {
      if (!s.parent.visible) continue;
      const sp = toScreen(s.position, rect);
      if (!sp) continue;
      // pinin görsel merkezi taban noktasının ~0.6 boy yukarısında
      const d = Math.hypot(mx - sp[0], my - (sp[1] - pinPx * 0.62));
      if (d < Math.max(tol, pinPx * 0.55) && d < bestD) { bestD = d; best = { type: 'point', item: s.userData.point, sprite: s }; }
    }
    if (best) return best;
    // çizgiler
    for (const pl of pickLines) {
      if (!groups[pl.line.layer].visible) continue;
      let prev = null;
      for (let i = 0; i < pl.pts.length; i += 2) {
        const [u, v] = pl.pts[i];
        const [x, z] = uvToWorld(u, v);
        const sp = toScreen(new THREE.Vector3(x, terrain.worldY(u, v), z), rect);
        if (sp && prev) {
          const d = segDist(mx, my, prev[0], prev[1], sp[0], sp[1]);
          if (d < tol * 0.6 && d < bestD) { bestD = d; best = { type: 'line', item: pl.line }; }
        }
        prev = sp;
      }
    }
    return best;
  }

  function setVisible(id, on) {
    if (groups[id]) groups[id].visible = on;
  }

  let selected = null;
  function select(sprite) {
    if (selected) selected.scale.multiplyScalar(1 / 1.3);
    selected = sprite || null;
    if (selected) selected.scale.multiplyScalar(1.3);
  }

  const counts = {};
  for (const p of data.points || []) counts[p.layer] = (counts[p.layer] || 0) + 1;
  for (const l of data.lines || []) counts[l.layer] = (counts[l.layer] || 0) + 1;

  return { updateHeights, resize, pick, setVisible, select, counts, pins, groups };
}

function segDist(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const L = dx * dx + dy * dy || 1;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L));
  return Math.hypot(px - ax - t * dx, py - ay - t * dy);
}
