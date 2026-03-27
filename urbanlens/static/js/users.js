// ════════════════════════════════════════
// USER MANAGEMENT
// ════════════════════════════════════════
async function loadUsers() {
  try {
    const res  = await fetch('/users');
    const data = await res.json();
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = data.map(u => `
      <tr>
        <td class="u-name">${escHtml(u.name)}</td>
        <td class="u-email">${escHtml(u.email)}</td>
        <td><span class="role-tag role-${u.role}">${u.role}</span></td>
        <td class="u-date">${formatDate(u.created_at)}</td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id},'${escHtml(u.name)}')">Delete</button>
        </td>
      </tr>
    `).join('');
  } catch(e) { showToast('Failed to load users', true); }
}

function openUserModal() {
  ['u-name','u-email','u-password'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('u-role').value = 'Planner';
  document.getElementById('user-modal-overlay').classList.add('open');
  setTimeout(() => document.getElementById('u-name').focus(), 200);
}

function closeUserModal() {
  document.getElementById('user-modal-overlay').classList.remove('open');
}

document.getElementById('user-modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('user-modal-overlay')) closeUserModal();
});

async function saveUser() {
  const name     = document.getElementById('u-name').value.trim();
  const email    = document.getElementById('u-email').value.trim();
  const password = document.getElementById('u-password').value.trim();
  const role     = document.getElementById('u-role').value;

  if (!name)     { highlightError('u-name');     return; }
  if (!email)    { highlightError('u-email');    return; }
  if (!password || password.length < 6) {
    highlightError('u-password');
    showToast('Password must be at least 6 characters', true);
    return;
  }

  try {
    const res = await fetch('/users', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role })
    });
    const d = await res.json();
    if (res.ok) {
      closeUserModal();
      showToast(`User ${name} created`);
      loadUsers();
    } else {
      showToast(d.error || 'Failed to create user', true);
    }
  } catch(e) { showToast('Network error', true); }
}

async function deleteUser(id, name) {
  if (!confirm(`Delete user "${name}"? This cannot be undone.`)) return;
  try {
    const res = await fetch(`/users/${id}`, { method: 'DELETE' });
    const d   = await res.json();
    if (res.ok) { showToast('User deleted'); loadUsers(); }
    else showToast(d.error || 'Delete failed', true);
  } catch(e) { showToast('Network error', true); }
}
