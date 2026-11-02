// Bursa 3D – genel ayarlar ve katman tanımları

export const ASSETS = {
  mapHi: 'assets/map_4096.webp',   // masaüstü
  mapLo: 'assets/map_2048.webp',   // mobil / zayıf GPU
  height: 'assets/height.png',     // fiziki haritaya hizalı yükseklik haritası
};

// Yükseklik haritasında 1.0 (beyaz) ≈ 2625 m (Kartaltepe 2543 m ≈ 247/255)
export const HEIGHT_MAX_M = 2625;
// Harita çerçevesinin doğu-batı genişliği ≈ 166.7 km → 100 dünya birimi
export const WORLD_KM = 166.7;

export const DISPLACEMENT = {
  min: 0,
  max: 16,
  default: 5,
};

// Katmanlar: id'ler data.js içindeki "layer" alanıyla aynı olmalı
export const LAYERS = [
  { id: 'antik',  label: 'Antik Kentler & Ören Yerleri', color: '#d9893b', icon: '🏛️', type: 'point', on: true },
  { id: 'tarihi', label: 'Kaleler, Hanlar, Medreseler',  color: '#b8603e', icon: '🏰', type: 'point', on: true },
  { id: 'dini',   label: 'Camiler & Dini Yapılar',       color: '#2f9e8f', icon: '🕌', type: 'point', on: true },
  { id: 'muze',   label: 'Müzeler',                      color: '#7b5cc4', icon: '🖼️', type: 'point', on: true },
  { id: 'doga',   label: 'Doğal Güzellikler',            color: '#3f9a3a', icon: '⛰️', type: 'point', on: true },
  { id: 'ulasim', label: 'Ulaşım (Teleferik, Havalimanı, Tren)', color: '#3577c9', icon: '🚡', type: 'mixed', on: false },
  { id: 'fay',    label: 'Fay Hatları',                  color: '#e03131', icon: '〰️', type: 'line', on: true, dashed: true, width: 3.5 },
  { id: 'sinir',  label: 'İl / İlçe Sınırları',          color: '#fdfdfd', icon: '▭', type: 'line', on: true, width: 1.6 },
];

export const LAYER_BY_ID = Object.fromEntries(LAYERS.map((l) => [l.id, l]));

export const PIN_PX = { desktop: 34, mobile: 38 };
export const LABEL_PX = 15;
