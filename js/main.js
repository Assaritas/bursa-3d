// Bursa 3D – giriş noktası
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { DISPLACEMENT, LAYERS } from './config.js';
import { WORLD_W, WORLD_H, uvToWorld } from './geo.js';
import { createTerrain } from './terrain.js';
import { createLayers } from './layers.js';
import { createUI } from './ui.js';

const loaderMsg = document.querySelector('#loader-msg');
const setMsg = (t) => { if (loaderMsg) loaderMsg.textContent = t; };

const data = window.BURSA_DATA || { points: [], lines: [], labels: [], meta: {} };

// --- Cihaz gücü: dokunmatik / küçük ekran / zayıf GPU → hafif mod ---
const probe = document.createElement('canvas').getContext('webgl2');
const maxTex = probe ? probe.getParameter(probe.MAX_TEXTURE_SIZE) : 2048;
const lowPower = matchMedia('(pointer: coarse)').matches || Math.min(screen.width, screen.height) < 700 || maxTex < 8192;

// --- Renderer ---
const container = document.querySelector('#scene');
const renderer = new THREE.WebGLRenderer({ antialias: !lowPower, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, lowPower ? 1.5 : 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
container.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xdfe9ef);
scene.fog = new THREE.Fog(0xdfe9ef, 140, 260);

const camera = new THREE.PerspectiveCamera(45, 1, 0.3, 600);

// Işıklar: haritadaki gölgelendirme ile uyumlu olsun diye ışık kuzeybatıdan gelir
scene.add(new THREE.AmbientLight(0xffffff, 2.45));
const sun = new THREE.DirectionalLight(0xffffff, 1.05);
sun.position.set(-40, 60, -45);
scene.add(sun);

// --- Kontroller (OrbitControls; dokunmatikte harita tarzı) ---
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.09;
controls.screenSpacePanning = false;          // zemin düzleminde kaydır
controls.minDistance = 4;
controls.maxDistance = 150;
controls.maxPolarAngle = THREE.MathUtils.degToRad(80);
controls.zoomToCursor = true;
controls.touches = { ONE: THREE.TOUCH.PAN, TWO: THREE.TOUCH.DOLLY_ROTATE };
controls.mouseButtons = { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.DOLLY, RIGHT: THREE.MOUSE.PAN };
controls.keyPanSpeed = 20;
controls.listenToKeyEvents(window);

// Masaüstünde sol panel haritanın batısını kapatmasın diye hedef biraz batıya kaydırılır
const wide = matchMedia('(min-width: 721px)').matches;
const HOME = wide
  ? { target: new THREE.Vector3(-10, 0, 4), pos: new THREE.Vector3(-10, 84, 78) }
  : { target: new THREE.Vector3(0, 0, 3), pos: new THREE.Vector3(0, 95, 70) };
camera.position.copy(HOME.pos);
controls.target.copy(HOME.target);

let needsRender = true;
const requestRender = () => { needsRender = true; };
controls.addEventListener('change', requestRender);

// Hedefi harita sınırları içinde tut
function clampTarget() {
  const t = controls.target;
  const cx = THREE.MathUtils.clamp(t.x, -WORLD_W / 2, WORLD_W / 2);
  const cz = THREE.MathUtils.clamp(t.z, -WORLD_H / 2, WORLD_H / 2);
  if (cx !== t.x || cz !== t.z) {
    const dx = cx - t.x, dz = cz - t.z;
    t.x = cx; t.z = cz;
    camera.position.x += dx; camera.position.z += dz;
  }
}

// --- Kamera animasyonu ---
let anim = null;
function flyTo(target, pos, ms = 1300) {
  anim = {
    t0: performance.now(), ms,
    fromT: controls.target.clone(), toT: target.clone(),
    fromP: camera.position.clone(), toP: pos.clone(),
  };
}
const ease = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

let terrain, layers, ui;

function focusPoint(p) {
  const [x, z] = uvToWorld(p.u, p.v);
  const y = terrain.worldY(p.u, p.v);
  const target = new THREE.Vector3(x, y, z);
  // mevcut bakış yönünü koruyarak yaklaş
  const dir = camera.position.clone().sub(controls.target).normalize();
  if (dir.y < 0.45) { dir.y = 0.45; dir.normalize(); }
  flyTo(target, target.clone().add(dir.multiplyScalar(14)));
}

// --- Boyutlandırma ---
function resize() {
  const w = container.clientWidth, h = container.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  layers?.resize(w, h);
  requestRender();
}
new ResizeObserver(resize).observe(container);

// --- Etkileşim: üzerine gelme (fare) ve dokunma/tıklama ---
const el = renderer.domElement;
let down = null;
el.addEventListener('pointerdown', (e) => { down = { x: e.clientX, y: e.clientY, t: performance.now() }; });
el.addEventListener('pointerup', (e) => {
  if (!down) return;
  const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
  const dt = performance.now() - down.t;
  down = null;
  if (moved > 8 || dt > 600) return;           // sürükleme, tıklama değil
  const hit = layers.pick(e.clientX, e.clientY);
  if (hit) ui.showPopup(hit);
  else ui.hidePopup();
  ui.showTip(null);
});
let hoverRaf = 0;
el.addEventListener('pointermove', (e) => {
  if (e.pointerType !== 'mouse' || e.buttons) { ui?.showTip(null); return; }
  cancelAnimationFrame(hoverRaf);
  hoverRaf = requestAnimationFrame(() => {
    const hit = layers.pick(e.clientX, e.clientY);
    el.style.cursor = hit ? 'pointer' : '';
    ui.showTip(hit, e.clientX, e.clientY);
  });
});
el.addEventListener('pointerleave', () => ui?.showTip(null));

// --- Döngü: yalnızca bir şey değiştiğinde çiz (pil dostu) ---
function loop(now) {
  requestAnimationFrame(loop);
  if (anim) {
    const k = Math.min(1, (now - anim.t0) / anim.ms);
    const e = ease(k);
    controls.target.lerpVectors(anim.fromT, anim.toT, e);
    camera.position.lerpVectors(anim.fromP, anim.toP, e);
    if (k >= 1) anim = null;
    needsRender = true;
  }
  if (controls.update()) needsRender = true;
  clampTarget();
  if (needsRender) {
    needsRender = false;
    renderer.render(scene, camera);
  }
}

// --- Başlat ---
async function start() {
  try {
    terrain = await createTerrain(renderer, { lowPower, onProgress: setMsg });
  } catch (err) {
    setMsg('Harita yüklenemedi: ' + err.message);
    throw err;
  }
  scene.add(terrain.group);
  terrain.setScale(DISPLACEMENT.default);

  setMsg('Katmanlar hazırlanıyor…');
  layers = createLayers({ scene, terrain, data, camera, renderer });
  layers.updateHeights();

  ui = createUI({
    layers, terrain, data,
    requestRender,
    onScale: (s) => { terrain.setScale(s); layers.updateHeights(); requestRender(); },
    onFocus: focusPoint,
    onReset: () => flyTo(HOME.target, HOME.pos),
  });

  resize();
  document.querySelector('#loader').classList.add('done');
  requestAnimationFrame(loop);

  if (!data.points?.length) ui.notify('data/data.js bulunamadı – önce tools/fetch_osm.py çalıştırın.', 8000);
  openFromURL();
  registerSW();
}

// Derin bağlantı: ...?yer=Ulu%20Cami  → o noktaya uçar ve bilgi kartını açar.
// Rehber, her durak için ayrı QR kod / link paylaşabilir.
function openFromURL() {
  const q = new URLSearchParams(location.search).get('yer');
  if (!q) return;
  const n = (s) => s.toLocaleLowerCase('tr');
  const nq = n(q);
  // en iyi eşleşme: tam ad > ad ile başlar > adı içerir; eşitlikte rehber kaydı ve ulaşım dışı katman önde
  const rank = (x) => {
    const nm = n(x.name);
    const m = nm === nq ? 0 : nm.startsWith(nq) ? 1 : nm.includes(nq) ? 2 : 9;
    return m * 10 + (x.src.includes('rehber') ? 0 : 2) + (x.layer === 'ulasim' ? 1 : 0);
  };
  const p = data.points.map((x) => [rank(x), x]).filter(([r]) => r < 90).sort((a, b) => a[0] - b[0])[0]?.[1];
  if (!p) { ui.notify(`“${q}” bulunamadı`); return; }
  layers.setVisible(p.layer, true);
  const cb = document.querySelectorAll('#layer-list input')[LAYERS.findIndex((l) => l.id === p.layer)];
  if (cb) cb.checked = true;
  const sprite = layers.pins.find((s) => s.userData.point === p);
  focusPoint(p);
  ui.showPopup({ type: 'point', item: p, sprite });
}
start();

// --- PWA: çevrimdışı önbellek + yükleme düğmesi ---
function registerSW() {
  if (!('serviceWorker' in navigator) || location.protocol === 'file:') return;
  navigator.serviceWorker.register('./sw.js').then((reg) => {
    if (!navigator.serviceWorker.controller) {
      // ilk kurulum: önbelleğe alma tamamlanınca bildir
      navigator.serviceWorker.addEventListener('message', (e) => {
        if (e.data === 'cached') ui.notify('✓ Çevrimdışı kullanıma hazır');
      });
    }
    reg.addEventListener('updatefound', () => {
      const nw = reg.installing;
      nw?.addEventListener('statechange', () => {
        if (nw.state === 'activated' && navigator.serviceWorker.controller) {
          ui.notify('Yeni sürüm yüklendi – sayfayı yenileyin.', 6000);
        }
      });
    });
  }).catch(() => { /* yerel test ortamı vb. */ });
}

let deferredPrompt = null;
const installBtn = document.querySelector('#install');
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  installBtn.hidden = false;
});
installBtn.addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  installBtn.hidden = true;
});
