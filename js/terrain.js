// 3B zemin: fiziki harita dokusu + yükseklik haritası (displacement map)
import * as THREE from 'three';
import { ASSETS } from './config.js';
import { WORLD_W, WORLD_H } from './geo.js';

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = 'async';
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('Görsel yüklenemedi: ' + url));
    img.src = url;
  });
}

// Yükseklik haritasını CPU'da da okuyoruz: pinleri ve çizgileri zemine oturtmak için.
function readHeights(img) {
  const c = document.createElement('canvas');
  c.width = img.width; c.height = img.height;
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);
  const px = ctx.getImageData(0, 0, c.width, c.height).data;
  const h = new Float32Array(c.width * c.height);
  for (let i = 0; i < h.length; i++) h[i] = px[i * 4] / 255;
  return { w: c.width, h: c.height, data: h };
}

// Yükseklik verisinden teğet-uzay normal haritası üretir (kabartma gölgesi için).
// 1 birim yükseklik ölçeğine göre hesaplanır; normalScale ile ölçek takip edilir.
function buildNormalMap(H) {
  const { w, h, data } = H;
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const ctx = c.getContext('2d');
  const out = ctx.createImageData(w, h);
  const px = WORLD_W / w, pz = WORLD_H / h;
  const at = (x, y) => data[Math.min(h - 1, Math.max(0, y)) * w + Math.min(w - 1, Math.max(0, x))];
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const gx = (at(x + 1, y) - at(x - 1, y)) / (2 * px);         // doğuya eğim
      const gy = (at(x, y - 1) - at(x, y + 1)) / (2 * pz);         // kuzeye eğim
      let nx = -gx, ny = -gy, nz = 1;
      const l = Math.hypot(nx, ny, nz);
      nx /= l; ny /= l; nz /= l;
      const i = (y * w + x) * 4;
      out.data[i] = (nx * 0.5 + 0.5) * 255;
      out.data[i + 1] = (ny * 0.5 + 0.5) * 255;
      out.data[i + 2] = (nz * 0.5 + 0.5) * 255;
      out.data[i + 3] = 255;
    }
  }
  ctx.putImageData(out, 0, 0);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.NoColorSpace;
  return t;
}

export async function createTerrain(renderer, { lowPower, onProgress }) {
  const mapUrl = lowPower ? ASSETS.mapLo : ASSETS.mapHi;
  onProgress?.('Harita dokusu yükleniyor…');
  const [mapImg, hImg] = await Promise.all([loadImage(mapUrl), loadImage(ASSETS.height)]);

  onProgress?.('Yer şekilleri hesaplanıyor…');
  const H = readHeights(hImg);

  const mapTex = new THREE.Texture(mapImg);
  mapTex.colorSpace = THREE.SRGBColorSpace;
  mapTex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  mapTex.needsUpdate = true;

  const dispTex = new THREE.Texture(hImg);
  dispTex.colorSpace = THREE.NoColorSpace;
  dispTex.generateMipmaps = false;
  dispTex.minFilter = THREE.LinearFilter;
  dispTex.needsUpdate = true;

  const normalTex = buildNormalMap(H);

  // Vertex yoğunluğu: mobilde ~48 bin, masaüstünde ~190 bin vertex
  const segX = lowPower ? 256 : 512;
  const segZ = Math.round(segX * WORLD_H / WORLD_W);
  const geo = new THREE.PlaneGeometry(WORLD_W, WORLD_H, segX, segZ);
  geo.rotateX(-Math.PI / 2);

  const mat = new THREE.MeshLambertMaterial({
    map: mapTex,
    displacementMap: dispTex,
    displacementScale: 1,
    normalMap: normalTex,
    normalScale: new THREE.Vector2(1, 1),
  });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'terrain';
  mesh.frustumCulled = false; // displacement sınır küresini değiştirir

  // --- Diorama kenarları (zemin bloğunun yan yüzleri) ---
  const group = new THREE.Group();
  group.add(mesh);
  const BASE = -1.2;
  const skirtMat = new THREE.MeshLambertMaterial({ color: 0x5b4a3a, side: THREE.DoubleSide });
  const edges = [];
  const N = 200;
  const mkEdge = (fn) => {
    const pos = new Float32Array((N + 1) * 2 * 3);
    const idx = [];
    for (let i = 0; i < N; i++) {
      const a = i * 2, b = a + 1, c = a + 2, d = a + 3;
      idx.push(a, b, c, b, d, c);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    g.setIndex(idx);
    const m = new THREE.Mesh(g, skirtMat);
    group.add(m);
    edges.push({ g, pos, fn });
  };
  mkEdge((t) => [t, 0]);
  mkEdge((t) => [t, 1]);
  mkEdge((t) => [0, t]);
  mkEdge((t) => [1, t]);
  const bottom = new THREE.Mesh(new THREE.PlaneGeometry(WORLD_W, WORLD_H), skirtMat);
  bottom.rotation.x = Math.PI / 2;
  bottom.position.y = BASE;
  group.add(bottom);

  // Bilineer örnekleme (u: batı→doğu, v: kuzey→güney, 0..1) → 0..1
  function heightAt(u, v) {
    const x = Math.min(H.w - 1, Math.max(0, u * (H.w - 1)));
    const y = Math.min(H.h - 1, Math.max(0, v * (H.h - 1)));
    const x0 = Math.floor(x), y0 = Math.floor(y);
    const x1 = Math.min(H.w - 1, x0 + 1), y1 = Math.min(H.h - 1, y0 + 1);
    const fx = x - x0, fy = y - y0;
    const d = H.data, w = H.w;
    const a = d[y0 * w + x0] * (1 - fx) + d[y0 * w + x1] * fx;
    const b = d[y1 * w + x0] * (1 - fx) + d[y1 * w + x1] * fx;
    return a * (1 - fy) + b * fy;
  }

  let scale = 1;
  function setScale(s) {
    scale = s;
    mat.displacementScale = s;
    // Normal haritası 1 birim ölçeğe göre; abartı arttıkça gölgeler de derinleşir
    const ns = Math.max(0.0001, s * 0.55);
    mat.normalScale.set(ns, ns);
    for (const e of edges) {
      for (let i = 0; i <= N; i++) {
        const [u, v] = e.fn(i / N);
        const x = (u - 0.5) * WORLD_W, z = (v - 0.5) * WORLD_H;
        const k = i * 6;
        e.pos[k] = x; e.pos[k + 1] = heightAt(u, v) * s; e.pos[k + 2] = z;
        e.pos[k + 3] = x; e.pos[k + 4] = BASE; e.pos[k + 5] = z;
      }
      e.g.attributes.position.needsUpdate = true;
      e.g.computeVertexNormals();
      e.g.computeBoundingSphere();
    }
  }

  return {
    group, mesh, heightAt, setScale,
    get scale() { return scale; },
    worldY: (u, v) => heightAt(u, v) * scale,
  };
}
