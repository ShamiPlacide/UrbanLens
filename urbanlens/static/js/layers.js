// ════════════════════════════════════════
// DATA LAYERS
// ════════════════════════════════════════
const layerGroups = {};

function initLayerControl() {
  // Create layer groups
  layerGroups.settlements = L.layerGroup().addTo(map);
  layerGroups.infra_Road = L.layerGroup().addTo(map);
  layerGroups.infra_Water_Point = L.layerGroup().addTo(map);
  layerGroups.infra_Sanitation = L.layerGroup().addTo(map);
  layerGroups.infra_Waste_Point = L.layerGroup().addTo(map);
  layerGroups.infra_School = L.layerGroup().addTo(map);
  layerGroups.infra_Health_Center = L.layerGroup().addTo(map);

  // Load saved preferences
  const saved = localStorage.getItem('urbanlens_layers');
  if (saved) {
    try {
      const prefs = JSON.parse(saved);
      Object.keys(prefs).forEach(key => {
        if (layerGroups[key] && !prefs[key]) {
          map.removeLayer(layerGroups[key]);
        }
      });
      // Update checkboxes to match
      document.querySelectorAll('.layer-checkbox').forEach(cb => {
        const key = cb.dataset.layer;
        if (prefs[key] !== undefined) {
          cb.checked = prefs[key];
        }
      });
    } catch(e) {}
  }
}

function toggleLayer(checkbox) {
  const key = checkbox.dataset.layer;
  if (!layerGroups[key]) return;

  if (checkbox.checked) {
    map.addLayer(layerGroups[key]);
  } else {
    map.removeLayer(layerGroups[key]);
  }

  saveLayerPrefs();
}

function toggleAllInfra(checkbox) {
  const infraKeys = Object.keys(layerGroups).filter(k => k.startsWith('infra_'));
  infraKeys.forEach(key => {
    const cb = document.querySelector(`.layer-checkbox[data-layer="${key}"]`);
    if (cb) {
      cb.checked = checkbox.checked;
      if (checkbox.checked) {
        map.addLayer(layerGroups[key]);
      } else {
        map.removeLayer(layerGroups[key]);
      }
    }
  });
  saveLayerPrefs();
}

function saveLayerPrefs() {
  const prefs = {};
  document.querySelectorAll('.layer-checkbox').forEach(cb => {
    prefs[cb.dataset.layer] = cb.checked;
  });
  localStorage.setItem('urbanlens_layers', JSON.stringify(prefs));
}

function toggleLayerPanel() {
  document.getElementById('layer-control').classList.toggle('collapsed');
}
