// ════════════════════════════════════════
// SETTLEMENTS
// ════════════════════════════════════════
let settlements = [];

// ── MODAL ──
function openSettlementModal(settlement = null) {
  const isEdit = !!settlement;
  document.getElementById('modal-title').textContent = isEdit ? 'Edit Settlement' : 'New Settlement';
  document.getElementById('modal-subtitle').textContent = isEdit
    ? 'Update settlement details below.'
    : 'Polygon captured — enter settlement details below.';

  document.getElementById('s-name').value = settlement ? settlement.name : '';
  document.getElementById('s-pop').value = settlement ? (settlement.population_estimate || '') : '';
  document.getElementById('s-risk').value = settlement ? settlement.risk_level : 'Medium';
  document.getElementById('s-housing').value = settlement ? (settlement.housing_type || '') : '';
  document.getElementById('s-notes').value = settlement ? (settlement.notes || '') : '';

  if (isEdit) {
    editingSettlementId = settlement.id;
  }

  document.getElementById('modal-overlay').classList.add('open');
  setTimeout(() => document.getElementById('s-name').focus(), 200);
}

function closeSettlementModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  editingSettlementId = null;
  cancelBoundaryEdit();
}

document.getElementById('modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('modal-overlay')) cancelDraw();
});

// ── SAVE ──
async function saveSettlement() {
  const name = document.getElementById('s-name').value.trim();
  if (!name) { highlightError('s-name'); return; }

  const payload = {
    name,
    population_estimate: document.getElementById('s-pop').value ? parseInt(document.getElementById('s-pop').value) : null,
    risk_level: document.getElementById('s-risk').value,
    housing_type: document.getElementById('s-housing').value,
    notes: document.getElementById('s-notes').value.trim()
  };

  if (editingSettlementId) {
    // Edit mode — check for edited boundary
    if (editableLayer && editableLayer.editing && editableLayer.editing.enabled()) {
      const coords = editableLayer.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);
      payload.polygon_coordinates = coords;
    } else if (currentPolygon) {
      // New polygon was drawn
      const coords = currentPolygon.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);
      payload.polygon_coordinates = coords;
    }

    try {
      const res = await fetch(`/settlements/${editingSettlementId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        cancelBoundaryEdit();
        closeSettlementModal();
        currentPolygon = null;
        editingSettlementId = null;
        showToast('Settlement updated');
        await loadSettlements();
      } else {
        const d = await res.json();
        showToast(d.error || 'Failed to update', true);
      }
    } catch(e) { showToast('Network error', true); }
  } else {
    // Create mode
    if (!currentPolygon) { showToast('No polygon drawn', true); return; }
    const coords = currentPolygon.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);
    payload.polygon_coordinates = coords;

    try {
      const res = await fetch('/settlements', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        closeSettlementModal();
        currentPolygon = null;
        showToast('Settlement saved (Pending approval)');
        await loadSettlements();
      } else {
        const d = await res.json();
        showToast(d.error || 'Failed to save', true);
      }
    } catch(e) { showToast('Network error', true); }
  }
}

// ── LOAD & RENDER ──
async function loadSettlements() {
  try {
    const params = new URLSearchParams();
    const search = document.getElementById('search-input');
    const riskFilter = document.getElementById('filter-risk');
    const statusFilter = document.getElementById('filter-status');

    if (search && search.value.trim()) params.set('search', search.value.trim());
    if (riskFilter && riskFilter.value) params.set('risk_level', riskFilter.value);
    if (statusFilter && statusFilter.value) params.set('status', statusFilter.value);

    const url = '/settlements' + (params.toString() ? '?' + params.toString() : '');
    const res = await fetch(url);
    if (!res.ok) return;
    settlements = await res.json();
    renderSidebar();
    renderMapPolygons();
  } catch(e) { console.error(e); }
}

function renderMapPolygons() {
  // Clear only settlement layers (not infrastructure)
  if (typeof layerGroups !== 'undefined' && layerGroups.settlements) {
    layerGroups.settlements.clearLayers();
  }
  settlements.forEach(s => addPolygonToMap(s));
}

function addPolygonToMap(s) {
  const color   = RISK_COLORS[s.risk_level] || '#f59e0b';
  const opacity = STATUS_OPACITY[s.status]  || 0.15;
  const latLngs = s.polygon_coordinates.map(c => L.latLng(c[0], c[1]));
  const poly = L.polygon(latLngs, {
    color, fillColor: color, fillOpacity: opacity,
    weight: s.status === 'Rejected' ? 1 : 2,
    dashArray: s.status === 'Pending' ? '6 4' : null
  });

  const canApprove = currentUser.role === 'Planner' || currentUser.role === 'Authority';
  const canEdit = currentUser.role !== 'Researcher';
  const approveBtn = canApprove && s.status !== 'Approved'
    ? `<button class="btn btn-approve btn-sm" onclick="updateStatus(${s.id},'Approved')">Approve</button>` : '';
  const rejectBtn  = canApprove && s.status !== 'Rejected'
    ? `<button class="btn btn-reject btn-sm" onclick="updateStatus(${s.id},'Rejected')">Reject</button>`  : '';
  const editBtn = canEdit
    ? `<button class="btn btn-outline btn-sm" onclick="editSettlement(${s.id})">Edit</button>` : '';

  const areaText = s.area ? `${s.area} km&sup2;` : '—';
  const densityText = s.density ? `${s.density.toLocaleString()}/km&sup2;` : '—';

  poly.bindPopup(`
    <div style="min-width:220px;padding:4px">
      <div class="popup-name">${escHtml(s.name)}</div>
      <div class="popup-row"><span class="popup-label">Status</span><span class="status-badge status-${s.status}">${s.status}</span></div>
      <div class="popup-row"><span class="popup-label">Risk</span><span class="risk-badge risk-${s.risk_level}">${s.risk_level}</span></div>
      <div class="popup-row"><span class="popup-label">Population</span><span class="popup-value">${s.population_estimate ? s.population_estimate.toLocaleString() : '—'}</span></div>
      <div class="popup-row"><span class="popup-label">Area</span><span class="popup-value">${areaText}</span></div>
      <div class="popup-row"><span class="popup-label">Density</span><span class="popup-value">${densityText}</span></div>
      ${s.housing_type ? `<div class="popup-row"><span class="popup-label">Housing</span><span class="popup-value">${escHtml(s.housing_type)}</span></div>` : ''}
      <div class="popup-row"><span class="popup-label">Mapped</span><span class="popup-value" style="font-size:11px">${formatDate(s.created_at)}</span></div>
      ${(approveBtn || rejectBtn || editBtn) ? `<div class="popup-actions">${editBtn}${approveBtn}${rejectBtn}</div>` : ''}
    </div>`, { maxWidth: 300 });

  poly.on('mouseover', function() { this.setStyle({ fillOpacity: Math.min(opacity + 0.2, 0.5), weight: 3 }); });
  poly.on('mouseout',  function() { this.setStyle({ fillOpacity: opacity, weight: s.status === 'Rejected' ? 1 : 2 }); });
  poly._settlementId = s.id;

  if (typeof layerGroups !== 'undefined' && layerGroups.settlements) {
    layerGroups.settlements.addLayer(poly);
  } else {
    drawnItems.addLayer(poly);
  }
}

function renderSidebar() {
  const list  = document.getElementById('sidebar-list');
  const badge = document.getElementById('count-badge');
  badge.textContent = settlements.length;

  if (!settlements.length) {
    list.innerHTML = '<div class="empty-state">No settlements found.<br>Click Add to begin drawing.</div>';
    return;
  }

  const role = currentUser.role;
  const canEdit = role !== 'Researcher';
  const canApprove = role === 'Planner' || role === 'Authority';

  list.innerHTML = settlements.map(s => {
    const status = s.status || 'Pending';
    const risk = s.risk_level || 'Low';
    const pop = s.population_estimate ? s.population_estimate.toLocaleString() : '';
    const area = s.area ? `${s.area} km\u00B2` : '';

    const approvalBtns = (canApprove && status === 'Pending')
      ? `<div class="card-actions">
           <button class="btn btn-approve btn-sm" onclick="event.stopPropagation();updateStatus(${s.id},'Approved')">Approve</button>
           <button class="btn btn-reject btn-sm" onclick="event.stopPropagation();updateStatus(${s.id},'Rejected')">Reject</button>
         </div>`
      : '';

    const actionBtns = canEdit
      ? `<div class="card-btns">
           <button class="card-icon-btn" onclick="event.stopPropagation();editSettlement(${s.id})" title="Edit">&#9998;</button>
           <button class="card-icon-btn delete" onclick="event.stopPropagation();deleteSettlement(${s.id})" title="Delete">&#10005;</button>
         </div>`
      : '';

    return `<div class="settlement-card" onclick="flyToSettlement(${s.id})">
      ${actionBtns}
      <div class="card-name">${escHtml(s.name)}</div>
      <div class="card-meta">
        <span class="risk-badge risk-${risk}">${risk}</span>
        <span class="status-badge status-${status}">${status}</span>
        ${pop ? `<span class="pop-tag">${pop} residents</span>` : ''}
        ${area ? `<span class="area-tag">${area}</span>` : ''}
      </div>
      ${approvalBtns}
      <div class="card-date">${formatDate(s.created_at)}</div>
    </div>`;
  }).join('');
}

// ── EDIT ──
let editableLayer = null;

function editSettlement(id) {
  const s = settlements.find(s => s.id === id);
  if (!s) return;

  // Find the polygon on the map and make it editable
  const allLayers = typeof layerGroups !== 'undefined' && layerGroups.settlements
    ? layerGroups.settlements : drawnItems;

  // Remove any previous editable layer
  cancelBoundaryEdit();

  allLayers.eachLayer(layer => {
    if (layer._settlementId === id && layer.editing) {
      map.flyToBounds(layer.getBounds(), { padding: [60, 60], duration: 0.5 });
      layer.editing.enable();
      layer.setStyle({ color: '#f59e0b', weight: 3, dashArray: '8 4' });
      editableLayer = layer;
    }
  });

  // Show edit banner
  const banner = document.getElementById('edit-boundary-banner');
  if (banner) {
    banner.classList.add('show');
  }

  editingSettlementId = id;
  openSettlementModal(s);
}

function saveBoundaryEdit() {
  if (editableLayer) {
    const newCoords = editableLayer.getLatLngs()[0].map(ll => [ll.lat, ll.lng]);
    currentPolygon = editableLayer;
    // Store coords so saveSettlement picks them up
    editableLayer._editedCoords = newCoords;
  }
}

function cancelBoundaryEdit() {
  if (editableLayer && editableLayer.editing) {
    editableLayer.editing.disable();
    editableLayer = null;
  }
  const banner = document.getElementById('edit-boundary-banner');
  if (banner) banner.classList.remove('show');
}

// ── FLY TO ──
function flyToSettlement(id) {
  const allLayers = typeof layerGroups !== 'undefined' && layerGroups.settlements
    ? layerGroups.settlements : drawnItems;
  allLayers.eachLayer(layer => {
    if (layer._settlementId === id) {
      map.flyToBounds(layer.getBounds(), { padding: [60, 60], duration: 0.8 });
      layer.openPopup();
    }
  });
}

// ── DELETE ──
async function deleteSettlement(id) {
  if (!confirm('Delete this settlement?')) return;
  try {
    const res = await fetch(`/settlements/${id}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Settlement deleted');
      await loadSettlements();
    } else {
      const d = await res.json();
      showToast(d.error || 'Delete failed', true);
    }
  } catch(err) { showToast('Delete failed', true); }
}

// ── APPROVAL ──
async function updateStatus(id, status) {
  try {
    const res = await fetch(`/settlements/${id}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status })
    });
    if (res.ok) {
      showToast(`Settlement ${status.toLowerCase()}`);
      await loadSettlements();
    } else {
      const d = await res.json();
      showToast(d.error || 'Update failed', true);
    }
  } catch(e) { showToast('Network error', true); }
}

// ── SEARCH & FILTER ──
let searchTimeout = null;
function onSearchInput() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => loadSettlements(), 300);
}

function onFilterChange() {
  loadSettlements();
}
