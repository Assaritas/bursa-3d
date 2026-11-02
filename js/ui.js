// Arayüz: lejant/katman menüsü, yükseklik kaydırıcısı, arama, tooltip ve bilgi kartı
import { LAYERS, LAYER_BY_ID, DISPLACEMENT, HEIGHT_MAX_M, WORLD_KM } from './config.js';
import { formatLatLon, WORLD_W } from './geo.js';

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// Gerçek ölçekte yükseklik (dünya birimi): 2625 m / (166.7 km / 100 birim)
const REAL_SCALE = (HEIGHT_MAX_M / 1000) / (WORLD_KM / WORLD_W);

export function createUI({ layers, terrain, data, onScale, onFocus, onReset, requestRender }) {
  // ---------------- Lejant / katmanlar ----------------
  const list = $('#layer-list');
  for (const L of LAYERS) {
    const n = layers.counts[L.id] || 0;
    const row = document.createElement('label');
    row.className = 'layer';
    row.style.setProperty('--c', L.color);
    row.innerHTML = `
      <span class="swatch ${L.type === 'line' ? 'line' : ''}${L.dashed ? ' dashed' : ''}" aria-hidden="true">${L.type === 'line' ? '' : L.icon}</span>
      <span class="layer-name">${esc(L.label)}</span>
      <span class="count">${n}</span>
      <input type="checkbox" ${L.on ? 'checked' : ''} ${n ? '' : 'disabled'} aria-label="${esc(L.label)}">
      <span class="switch" aria-hidden="true"></span>`;
    const cb = row.querySelector('input');
    cb.addEventListener('change', () => {
      layers.setVisible(L.id, cb.checked);
      hidePopup();
      requestRender();
      save();
    });
    list.appendChild(row);
  }

  // Görünür katman tercihini hatırla (yalnızca bu cihazda)
  function save() {
    try {
      const st = {};
      list.querySelectorAll('input').forEach((cb, i) => (st[LAYERS[i].id] = cb.checked));
      localStorage.setItem('bursa3d.layers', JSON.stringify(st));
    } catch { /* gizli sekme vb. */ }
  }
  try {
    const st = JSON.parse(localStorage.getItem('bursa3d.layers') || 'null');
    if (st) list.querySelectorAll('input').forEach((cb, i) => {
      const id = LAYERS[i].id;
      if (id in st && !cb.disabled) { cb.checked = st[id]; layers.setVisible(id, st[id]); }
    });
  } catch { /* yok say */ }

  $('#all-on').addEventListener('click', () => toggleAll(true));
  $('#all-off').addEventListener('click', () => toggleAll(false));
  function toggleAll(on) {
    list.querySelectorAll('input').forEach((cb, i) => {
      if (cb.disabled) return;
      cb.checked = on; layers.setVisible(LAYERS[i].id, on);
    });
    hidePopup(); requestRender(); save();
  }

  // ---------------- Panel aç/kapa ----------------
  const panel = $('#panel');
  const toggleBtn = $('#panel-toggle');
  const setPanel = (open) => {
    panel.classList.toggle('open', open);
    toggleBtn.setAttribute('aria-expanded', String(open));
  };
  setPanel(!matchMedia('(max-width: 720px)').matches);
  toggleBtn.addEventListener('click', () => setPanel(!panel.classList.contains('open')));
  $('#panel-close').addEventListener('click', () => setPanel(false));

  // ---------------- Yükseklik kaydırıcısı ----------------
  const slider = $('#depth');
  const out = $('#depth-out');
  slider.min = DISPLACEMENT.min; slider.max = DISPLACEMENT.max; slider.step = 0.1;
  slider.value = DISPLACEMENT.default;
  const showScale = () => {
    const s = parseFloat(slider.value);
    out.textContent = s === 0 ? 'düz' : `×${(s / REAL_SCALE).toFixed(1)}`;
  };
  let raf = 0;
  slider.addEventListener('input', () => {
    showScale();
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => onScale(parseFloat(slider.value)));
  });
  showScale();

  $('#reset-view').addEventListener('click', () => { hidePopup(); onReset(); });

  // ---------------- Arama ----------------
  const search = $('#search');
  const results = $('#search-results');
  const points = (data.points || []).slice().sort((a, b) => a.name.localeCompare(b.name, 'tr'));
  const norm = (s) => s.toLocaleLowerCase('tr').normalize('NFD').replace(/[̀-ͯ]/g, '');
  search.addEventListener('input', () => {
    const q = norm(search.value.trim());
    results.innerHTML = '';
    if (q.length < 2) return;
    const hits = points.filter((p) => norm(p.name).includes(q)).slice(0, 8);
    for (const p of hits) {
      const L = LAYER_BY_ID[p.layer];
      const li = document.createElement('li');
      li.innerHTML = `<button type="button"><span class="dot" style="--c:${L.color}">${L.icon}</span>${esc(p.name)}</button>`;
      li.querySelector('button').addEventListener('click', () => {
        // gizli katmandaysa aç
        const idx = LAYERS.findIndex((l) => l.id === p.layer);
        const cb = list.querySelectorAll('input')[idx];
        if (cb && !cb.checked) { cb.checked = true; layers.setVisible(p.layer, true); save(); }
        search.value = ''; results.innerHTML = '';
        if (matchMedia('(max-width: 720px)').matches) setPanel(false);
        const sprite = layers.pins.find((s) => s.userData.point === p);
        onFocus(p);
        showPopup({ type: 'point', item: p, sprite });
      });
      results.appendChild(li);
    }
    if (!hits.length) results.innerHTML = '<li class="empty">Sonuç yok</li>';
  });

  // ---------------- Tooltip (masaüstü fareyle üzerine gelme) ----------------
  const tip = $('#tooltip');
  function showTip(hit, x, y) {
    if (!hit) { tip.hidden = true; return; }
    const it = hit.item;
    const L = LAYER_BY_ID[it.layer];
    tip.innerHTML = `<span class="dot" style="--c:${L.color}"></span>${esc(it.name)}`;
    tip.hidden = false;
    const r = tip.getBoundingClientRect();
    tip.style.left = Math.min(window.innerWidth - r.width - 8, x + 14) + 'px';
    tip.style.top = Math.max(8, y - r.height - 10) + 'px';
  }

  // ---------------- Bilgi kartı (popup / mobilde alt sayfa) ----------------
  const pop = $('#popup');
  const body = $('#popup-body');
  let current = null;

  function showPopup(hit) {
    current = hit;
    layers.select(hit.sprite || null);
    const it = hit.item;
    const L = LAYER_BY_ID[it.layer];
    const t = it.tags || {};
    const facts = [];
    if (hit.type === 'point') {
      const terrainM = Math.round(terrain.heightAt(it.u, it.v) * HEIGHT_MAX_M / 10) * 10;
      if (t.ele) facts.push(['Yükseklik', `${esc(t.ele)} m`]);
      else if (terrainM > 20) facts.push(['Rakım (yaklaşık)', `~${terrainM} m`]);
      if (t.start_date) facts.push(['Yapım', esc(t.start_date)]);
      if (t['historic:civilization']) facts.push(['Uygarlık', esc(t['historic:civilization'])]);
      if (t.architect) facts.push(['Mimar', esc(t.architect)]);
      if (t.opening_hours) facts.push(['Ziyaret', esc(t.opening_hours)]);
      facts.push(['Konum', formatLatLon(it.lat, it.lon)]);
    }
    const desc = it.desc ? `<p>${esc(it.desc)}</p>` : '';
    const wiki = it.wiki?.extract
      ? `<div class="wiki"><div class="wiki-h">Vikipedi${it.wiki.lang !== 'tr' ? ` (${esc(it.wiki.lang)})` : ''}</div><p>${esc(it.wiki.extract)}</p></div>`
      : '';
    const none = !desc && !wiki ? '<p class="muted">Bu nokta için kayıtlı açıklama yok.</p>' : '';
    const links = [];
    if (it.wiki?.url) links.push(`<a href="${esc(it.wiki.url)}" target="_blank" rel="noopener">Vikipedi’de aç ↗</a>`);
    if (hit.type === 'point') links.push(`<a href="https://www.google.com/maps/dir/?api=1&destination=${it.lat},${it.lon}" target="_blank" rel="noopener">Yol tarifi ↗</a>`);

    body.innerHTML = `
      <div class="pop-kind" style="--c:${L.color}"><span class="dot"></span>${esc(it.kind || L.label)}${it.approx ? ' · <span title="Konum yaklaşık">≈ konum</span>' : ''}</div>
      <h2 id="popup-title">${esc(it.name)}</h2>
      ${desc}${wiki}${none}
      ${facts.length ? `<dl>${facts.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join('')}</dl>` : ''}
      <div class="pop-actions">
        ${hit.type === 'point' ? '<button type="button" id="pop-zoom" class="btn">Yakınlaştır</button>' : ''}
        ${links.join('')}
      </div>`;
    body.querySelector('#pop-zoom')?.addEventListener('click', () => onFocus(it));
    pop.hidden = false;
    pop.scrollTop = 0;
    body.scrollTop = 0;
    requestRender();
  }

  function hidePopup() {
    if (pop.hidden) return;
    pop.hidden = true;
    current = null;
    layers.select(null);
    requestRender();
  }
  $('#popup-close').addEventListener('click', hidePopup);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hidePopup(); });

  // ---------------- Bildirim ----------------
  const toast = $('#toast');
  let toastT = 0;
  function notify(msg, ms = 3500) {
    toast.textContent = msg;
    toast.hidden = false;
    clearTimeout(toastT);
    toastT = setTimeout(() => (toast.hidden = true), ms);
  }

  // ---------------- Veri bilgisi ----------------
  const m = data.meta || {};
  $('#data-info').textContent = m.generated
    ? `Veri: ${new Date(m.generated).toLocaleDateString('tr-TR')} · ${data.points?.length || 0} nokta`
    : '';

  return { showPopup, hidePopup, showTip, notify, get current() { return current; } };
}
