// ════════════════════════════════════════
// AUDIT LOG
// ════════════════════════════════════════
async function loadAuditLog() {
  try {
    const res  = await fetch('/audit-log');
    const data = await res.json();
    const tbody = document.getElementById('audit-tbody');
    tbody.innerHTML = data.map(a => `
      <tr>
        <td><span class="audit-action">${escHtml(a.action)}</span></td>
        <td class="audit-user">${escHtml(a.user_name) || '—'}<br><span style="font-size:9px;color:var(--muted)">${escHtml(a.user_role) || ''}</span></td>
        <td class="audit-detail">${a.target_type ? `${escHtml(a.target_type)} #${a.target_id}` : '—'}</td>
        <td class="audit-detail">${escHtml(a.detail) || '—'}</td>
        <td class="audit-time">${formatDate(a.created_at)}</td>
      </tr>
    `).join('');
  } catch(e) { showToast('Failed to load audit log', true); }
}
