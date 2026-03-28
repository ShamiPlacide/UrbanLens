// ════════════════════════════════════════
// GLOBAL STATE
// ════════════════════════════════════════
let currentUser = null;

// ════════════════════════════════════════
// AUTH
// ════════════════════════════════════════
async function doLogin() {
  const email    = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value.trim();
  try {
    const res  = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      document.getElementById('login-page').style.display = 'none';
      document.getElementById('dashboard').style.display = 'flex';
      setupRoleUI();
      initMap();
      loadSettlements();
      loadInfrastructure();
    } else {
      showLoginError();
    }
  } catch(e) { showToast('Connection error', true); }
}

function showLoginError() {
  const err = document.getElementById('login-error');
  err.style.display = 'block';
  setTimeout(() => err.style.display = 'none', 3000);
}

async function doLogout() {
  await fetch('/logout', { method: 'POST' });
  location.reload();
}

document.getElementById('login-password').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});
document.getElementById('login-email').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

// ════════════════════════════════════════
// ROLE-BASED UI SETUP
// ════════════════════════════════════════
function setupRoleUI() {
  const role = currentUser.role;

  document.getElementById('chip-name').textContent = currentUser.name;
  const roleTag = document.getElementById('chip-role');
  roleTag.textContent = role;
  roleTag.className = 'role-tag role-' + role;

  // Planner (Admin) gets Users + Audit Log tabs
  if (role === 'Planner') {
    document.getElementById('tab-users').style.display = 'flex';
    document.getElementById('tab-audit').style.display = 'flex';
  }

  // All roles get Analytics tab
  document.getElementById('tab-analytics').style.display = 'flex';

  // Researcher gets read-only banner and no Add button
  if (role === 'Researcher') {
    document.getElementById('readonly-banner').classList.add('show');
  } else {
    // Planner and Authority can both add settlements
    document.getElementById('add-btn').style.display = 'inline-flex';
    document.getElementById('add-infra-btn').style.display = 'inline-flex';
  }
}

// ════════════════════════════════════════
// TABS
// ════════════════════════════════════════
function switchTab(name) {
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel-view').forEach(p => p.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');

  if (name === 'users')     loadUsers();
  if (name === 'audit')     loadAuditLog();
  if (name === 'analytics') loadAnalytics();
  if (name === 'map' && typeof map !== 'undefined' && map) setTimeout(() => map.invalidateSize(), 50);
}

// ════════════════════════════════════════
// PROFILE
// ════════════════════════════════════════
function openProfileModal() {
  document.getElementById('profile-name').value = currentUser.name;
  document.getElementById('profile-email').textContent = currentUser.email;
  document.getElementById('profile-role').textContent = currentUser.role;
  document.getElementById('profile-role').className = 'profile-value role-tag role-' + currentUser.role;
  document.getElementById('profile-new-password').value = '';
  document.getElementById('profile-modal-overlay').classList.add('open');
}

function closeProfileModal() {
  document.getElementById('profile-modal-overlay').classList.remove('open');
}

async function saveProfile() {
  const name = document.getElementById('profile-name').value.trim();
  const newPassword = document.getElementById('profile-new-password').value.trim();

  if (!name) { highlightError('profile-name'); return; }

  try {
    // Update name
    const res = await fetch('/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (!res.ok) {
      const d = await res.json();
      showToast(d.error || 'Failed to update profile', true);
      return;
    }
    currentUser.name = name;
    document.getElementById('chip-name').textContent = name;

    // Update password if provided
    if (newPassword) {
      if (newPassword.length < 6) {
        showToast('Password must be at least 6 characters', true);
        return;
      }
      const pwRes = await fetch(`/users/${currentUser.id}/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: newPassword })
      });
      if (!pwRes.ok) {
        const d = await pwRes.json();
        showToast(d.error || 'Failed to update password', true);
        return;
      }
    }

    closeProfileModal();
    showToast('Profile updated');
  } catch(e) { showToast('Network error', true); }
}

document.getElementById('profile-modal-overlay').addEventListener('click', e => {
  if (e.target === document.getElementById('profile-modal-overlay')) closeProfileModal();
});

// ════════════════════════════════════════
// UTILITIES
// ════════════════════════════════════════
function showToast(msg, isError = false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast show' + (isError ? ' error' : '');
  setTimeout(() => t.className = 'toast', 3500);
}

function escHtml(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' });
  } catch(e) { return iso; }
}

function highlightError(id) {
  const el = document.getElementById(id);
  el.focus(); el.style.borderColor = '#ef4444';
  setTimeout(() => el.style.borderColor = '', 1500);
}
