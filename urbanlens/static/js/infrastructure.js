// ════════════════════════════════════════
// INFRASTRUCTURE
// ════════════════════════════════════════
let infrastructureData = [];

function buildInfraPopup(item) {
  const canEdit = currentUser.role !== 'Researcher';
  const editBtn = canEdit
    ? `<button class="btn btn-outline btn-sm" onclick="editInfra(${item.id})">Edit</button>
       <button class="btn btn-danger btn-sm" onclick="deleteInfra(${item.id})">Delete</button>`
    : '';
  return `<div style="min-width:180px;padding:4px">
      <div class="popup-name">${escHtml(item.name)}</div>
      <div class="popup-row"><span class="popup-label">Type</span><span class="popup-value">${escHtml(item.type)}</span></div>
      <div class="popup-row"><span class="popup-label">Condition</span><span class="popup-value">${item.condition || '\u2014'}</span></div>
      ${item.notes ? `<div class="popup-row"><span class="popup-label">Notes</span><span class="popup-value">${escHtml(item.notes)}</span></div>` : ''}
      ${editBtn ? `<div class="popup-actions">${editBtn}</div>` : ''}
    </div>`;
}

async function loadInfrastructure() {
  try {
    const res = await fetch('/infrastructure');
    if (!res.ok) return;
    infrastructureData = await res.json();
    renderInfraOnMap();
  } catch(e) { console.error(e); }
}

function renderInfraOnMap() {
  // Clear infrastructure layers
  if (typeof layerGroups !== 'undefined') {
    Object.keys(layerGroups).forEach(key => {
      if (key.startsWith('infra_')) {
        layerGroups[key].clearLayers();
      }
    });
  }

  infrastructureData.forEach(item => addInfraToMap(item));
}

function addInfraToMap(item) {
  const color = INFRA_COLORS[item.type] || '#9ca3af';
  let layer;

  if (item.geometry_type === 'Point' && item.coordinates.length >= 2) {
    const icon = createInfraIcon(item.type);
    layer = L.marker([item.coordinates[0], item.coordinates[1]], { icon });
  } else if (item.geometry_type === 'LineString' && item.coordinates.length >= 2) {
    const latLngs = item.coordinates.map(c => L.latLng(c[0], c[1]));
    if (item.type === 'Road') {
      // Road casing (dark outline) for Google Maps-like appearance
      const casing = L.polyline(latLngs, {
        color: '#1a1a2e', weight: 8, opacity: 0.9, lineCap: 'round', lineJoin: 'round'
      });
      // Road fill (lighter center line)
      const fill = L.polyline(latLngs, {
        color: '#4a5568', weight: 5, opacity: 1, lineCap: 'round', lineJoin: 'round'
      });
      // Group casing + fill as a single interactive layer
      layer = L.layerGroup([casing, fill]);
      // Bind popup to fill line so clicks work
      fill.bindPopup(buildInfraPopup(item), { maxWidth: 260 });
      fill.on('mouseover', function() { fill.setStyle({ color: '#718096', weight: 6 }); });
      fill.on('mouseout',  function() { fill.setStyle({ color: '#4a5568', weight: 5 }); });
      fill._infraId = item.id;
    } else {
      layer = L.polyline(latLngs, { color, weight: 3, opacity: 0.8 });
    }
  } else if (item.geometry_type === 'Polygon' && item.coordinates.length >= 3) {
    const latLngs = item.coordinates.map(c => L.latLng(c[0], c[1]));
    layer = L.polygon(latLngs, { color, fillColor: color, fillOpacity: 0.15, weight: 2 });
  }

  if (!layer) return;

  // Roads already have popup bound above; bind for all other types
  if (item.type !== 'Road' || item.geometry_type !== 'LineString') {
    layer.bindPopup(buildInfraPopup(item), { maxWidth: 260 });
    layer._infraId = item.id;
  }

  // Add to appropriate layer group
  const layerKey = 'infra_' + item.type.replace(/\s+/g, '_');
  if (typeof layerGroups !== 'undefined' && layerGroups[layerKey]) {
    layerGroups[layerKey].addLayer(layer);
  } else if (typeof layerGroups !== 'undefined' && layerGroups.infrastructure) {
    layerGroups.infrastructure.addLayer(layer);
  } else {
    drawnItems.addLayer(layer);
  }
}

// ── INFRA MODAL ──
let editingInfraId = null;

function openInfraModal(item = null) {
  const isEdit = !!item;
  document.getElementById('infra-modal-title').textContent = isEdit ? 'Edit Infrastructure' : 'New Infrastructure';

  document.getElementById('i-settlement').value = item ? item.settlement_id : '';
  document.getElementById('i-type').value = item ? item.type : '';
  document.getElementById('i-name').value = item ? item.name : '';
  document.getElementById('i-condition').value = item ? (item.condition || '') : '';
  document.getElementById('i-notes').value = item ? (item.notes || '') : '';

  if (isEdit) {
    editingInfraId = item.id;
  } else {
    editingInfraId = null;
  }

  // Populate settlement dropdown
  const select = document.getElementById('i-settlement');
  select.innerHTML = '<option value="">-- Select Settlement --</option>' +
    settlements.map(s => `<option value="${s.id}">${escHtml(s.name)}</option>`).join('');
  if (item) select.value = item.settlement_id;

  document.getElementById('infra-modal-overlay').classList.add('open');
  setTimeout(() => document.getElementById('i-name').focus(), 200);
}

function closeInfraModal() {
  document.getElementById('infra-modal-overlay').classList.remove('open');
  editingInfraId = null;
  infraDrawMode = null;
}

document.getElementById('infra-modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('infra-modal-overlay')) closeInfraModal();
});

async function saveInfra() {
  const settlementId = document.getElementById('i-settlement').value;
  const type = document.getElementById('i-type').value;
  const name = document.getElementById('i-name').value.trim();
  const condition = document.getElementById('i-condition').value;
  const notes = document.getElementById('i-notes').value.trim();

  if (!name) { highlightError('i-name'); return; }
  if (!type) { highlightError('i-type'); return; }
  if (!settlementId) { highlightError('i-settlement'); return; }

  const payload = {
    settlement_id: parseInt(settlementId),
    type,
    name,
    condition: condition || null,
    notes
  };

  if (editingInfraId) {
    // Edit mode
    if (currentPolygon) {
      if (infraDrawMode === 'Point') {
        const ll = currentPolygon.getLatLng();
        payload.coordinates = [ll.lat, ll.lng];
      } else if (infraDrawMode === 'LineString') {
        payload.coordinates = currentPolygon.getLatLngs().map(ll => [ll.lat, ll.lng]);
      } else if (infraDrawMode === 'Polygon') {
        payload.coordinates = currentPolygon.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);
      }
      payload.geometry_type = infraDrawMode;
    }

    try {
      const res = await fetch(`/infrastructure/${editingInfraId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        closeInfraModal();
        currentPolygon = null;
        showToast('Infrastructure updated');
        await loadInfrastructure();
      } else {
        const d = await res.json();
        showToast(d.error || 'Failed to update', true);
      }
    } catch(e) { showToast('Network error', true); }
  } else {
    // Create mode
    if (!currentPolygon) { showToast('No geometry drawn', true); return; }

    if (infraDrawMode === 'Point') {
      const ll = currentPolygon.getLatLng();
      payload.coordinates = [ll.lat, ll.lng];
      payload.geometry_type = 'Point';
    } else if (infraDrawMode === 'LineString') {
      payload.coordinates = currentPolygon.getLatLngs().map(ll => [ll.lat, ll.lng]);
      payload.geometry_type = 'LineString';
    } else if (infraDrawMode === 'Polygon') {
      payload.coordinates = currentPolygon.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);
      payload.geometry_type = 'Polygon';
    }

    try {
      const res = await fetch('/infrastructure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        closeInfraModal();
        currentPolygon = null;
        showToast('Infrastructure added');
        await loadInfrastructure();
      } else {
        const d = await res.json();
        showToast(d.error || 'Failed to save', true);
      }
    } catch(e) { showToast('Network error', true); }
  }
}

function editInfra(id) {
  const item = infrastructureData.find(i => i.id === id);
  if (!item) return;
  openInfraModal(item);
}

async function deleteInfra(id) {
  if (!confirm('Delete this infrastructure?')) return;
  try {
    const res = await fetch(`/infrastructure/${id}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Infrastructure deleted');
      await loadInfrastructure();
    } else {
      const d = await res.json();
      showToast(d.error || 'Delete failed', true);
    }
  } catch(e) { showToast('Delete failed', true); }
}

function showInfraDrawOptions() {
  const menu = document.getElementById('infra-draw-menu');
  if (menu.style.display === 'block') {
    menu.style.display = 'none';
  } else {
    menu.style.display = 'block';
  }
}
