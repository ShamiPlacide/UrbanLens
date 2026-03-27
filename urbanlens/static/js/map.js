// ════════════════════════════════════════
// MAP
// ════════════════════════════════════════
let map, drawnItems, drawControl, currentPolygon = null;
let editingSettlementId = null;
let infraDrawMode = null; // null, 'Point', 'LineString', 'Polygon'

const RISK_COLORS = { Low: '#22c55e', Medium: '#eab308', High: '#ef4444' };
const STATUS_OPACITY = { Pending: 0.14, Approved: 0.22, Rejected: 0.08 };

// Infrastructure colors
const INFRA_COLORS = {
  'Road': '#9ca3af',
  'Water Point': '#3b82f6',
  'Sanitation': '#22c55e',
  'Waste Point': '#f97316',
  'School': '#eab308',
  'Health Center': '#ef4444'
};

const INFRA_ICONS = {
  'Road': 'R',
  'Water Point': 'W',
  'Sanitation': 'S',
  'Waste Point': 'X',
  'School': 'Sc',
  'Health Center': 'H'
};

function initMap() {
  map = L.map('map', { center: [-1.9441, 30.0619], zoom: 13 });
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://openstreetmap.org">OSM</a> &copy; <a href="https://carto.com">CARTO</a>',
    subdomains: 'abcd', maxZoom: 20
  }).addTo(map);

  drawnItems = new L.FeatureGroup().addTo(map);

  drawControl = new L.Control.Draw({
    draw: {
      polygon: { allowIntersection: false, showArea: true, shapeOptions: { color: '#f59e0b', fillColor: '#f59e0b', fillOpacity: 0.18, weight: 2 } },
      polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false
    },
    edit: { featureGroup: drawnItems, remove: false }
  });

  map.on(L.Draw.Event.CREATED, function(e) {
    currentPolygon = e.layer;
    drawnItems.addLayer(currentPolygon);
    document.getElementById('draw-banner').classList.remove('show');

    if (infraDrawMode) {
      openInfraModal();
    } else {
      openSettlementModal();
    }
  });

  map.on(L.Draw.Event.DRAWSTART, function() {
    document.getElementById('draw-banner').classList.add('show');
    document.getElementById('add-btn').style.opacity = '0.5';
    document.getElementById('add-btn').style.pointerEvents = 'none';
  });

  map.on(L.Draw.Event.DRAWSTOP, function() {
    document.getElementById('draw-banner').classList.remove('show');
    document.getElementById('add-btn').style.opacity = '';
    document.getElementById('add-btn').style.pointerEvents = '';
  });

  initLayerControl();
}

function startDraw() {
  if (currentUser.role === 'Researcher') return;
  infraDrawMode = null;
  editingSettlementId = null;
  new L.Draw.Polygon(map, drawControl.options.draw.polygon).enable();
}

function startInfraDraw(geometryType) {
  if (currentUser.role === 'Researcher') return;
  infraDrawMode = geometryType;

  if (geometryType === 'Point') {
    new L.Draw.Marker(map, {}).enable();
  } else if (geometryType === 'LineString') {
    new L.Draw.Polyline(map, { shapeOptions: { color: '#9ca3af', weight: 3 } }).enable();
  } else if (geometryType === 'Polygon') {
    new L.Draw.Polygon(map, {
      allowIntersection: false,
      shapeOptions: { color: '#14b8a6', fillColor: '#14b8a6', fillOpacity: 0.2, weight: 2 }
    }).enable();
  }
}

function cancelDraw() {
  if (currentPolygon) { drawnItems.removeLayer(currentPolygon); currentPolygon = null; }
  infraDrawMode = null;
  editingSettlementId = null;
  closeSettlementModal();
  closeInfraModal();
  document.getElementById('draw-banner').classList.remove('show');
  document.getElementById('add-btn').style.opacity = '';
  document.getElementById('add-btn').style.pointerEvents = '';
}

function createInfraIcon(type) {
  const color = INFRA_COLORS[type] || '#9ca3af';
  const label = INFRA_ICONS[type] || '?';
  return L.divIcon({
    className: '',
    html: `<div class="infra-icon" style="background:${color}">${label}</div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
}
