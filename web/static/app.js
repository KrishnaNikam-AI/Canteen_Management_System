/* ============================================================================
   app.js – Canteen Management System Global JavaScript
   ============================================================================ */

/* ── Theme ─────────────────────────────────────────────────────────────────── */
function initTheme() {
  const saved = localStorage.getItem('cms-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  updateThemeUI(saved);
}

function toggleTheme() {
  const cur = document.documentElement.getAttribute('data-theme');
  const next = cur === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('cms-theme', next);
  updateThemeUI(next);
}

function updateThemeUI(theme) {
  const icon  = document.getElementById('themeIcon');
  const label = document.getElementById('themeLabel');
  if (!icon) return;
  if (theme === 'dark') {
    icon.textContent  = '☀️';
    label.textContent = 'Light Mode';
  } else {
    icon.textContent  = '🌙';
    label.textContent = 'Dark Mode';
  }
}

/* ── Sidebar ───────────────────────────────────────────────────────────────── */
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const main    = document.querySelector('.main-content');
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('mobile-open');
  } else {
    sidebar.classList.toggle('collapsed');
    main.classList.toggle('expanded');
  }
}

/* ── Toast Notifications ───────────────────────────────────────────────────── */
function showToast(message, type = 'success', duration = 3500) {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(12px)';
    toast.style.transition = '0.3s';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Modal ─────────────────────────────────────────────────────────────────── */
function openModal(title, bodyHTML, footerHTML = '') {
  document.getElementById('modalTitle').textContent  = title;
  document.getElementById('modalBody').innerHTML     = bodyHTML;
  document.getElementById('modalFooter').innerHTML   = footerHTML;
  document.getElementById('modalOverlay').classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

/* ── API Helper ────────────────────────────────────────────────────────────── */
async function api(method, url, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const json = await res.json();
  if (!json.success) throw new Error(json.error || 'Unknown error');
  return json.data;
}

/* ── Badge Helper ──────────────────────────────────────────────────────────── */
function badge(value, map = {}) {
  const cls = map[value] || 'badge-' + (value || 'unknown').toLowerCase().replace(/\s+/g, '-');
  return `<span class="badge ${cls}">${value || '—'}</span>`;
}

function statusBadge(status) {
  const map = {
    'Pending':   'badge-pending',
    'Preparing': 'badge-preparing',
    'Ready':     'badge-ready',
    'Completed': 'badge-completed',
    'Cancelled': 'badge-cancelled',
    'Paid':      'badge-paid',
    'Unpaid':    'badge-unpaid',
    'Refunded':  'badge-refunded',
  };
  return badge(status, map);
}

/* ── DB Status Check ───────────────────────────────────────────────────────── */
async function checkDbStatus() {
  try {
    await api('GET', '/api/dashboard/stats');
    const dot  = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    if (dot)  dot.className  = 'status-dot online';
    if (text) text.textContent = 'DB Connected';
  } catch {
    const dot  = document.querySelector('.status-dot');
    const text = document.querySelector('.status-text');
    if (dot)  dot.className  = 'status-dot offline';
    if (text) text.textContent = 'DB Offline';
  }
}

/* ── Table Builder ─────────────────────────────────────────────────────────── */
function buildTable(cols, rows, actionFn = null) {
  if (!rows || rows.length === 0) {
    return `<div class="empty-state">
      <div class="empty-icon">📭</div>
      <p>No records found.</p>
    </div>`;
  }
  let html = `<div class="table-scroll"><table class="data-table"><thead><tr>`;
  cols.forEach(c => html += `<th>${c.label}</th>`);
  if (actionFn) html += `<th>Actions</th>`;
  html += `</tr></thead><tbody>`;
  rows.forEach(r => {
    html += `<tr>`;
    cols.forEach(c => {
      const raw = r[c.key] ?? '—';
      html += `<td>${c.render ? c.render(raw, r) : raw}</td>`;
    });
    if (actionFn) html += `<td>${actionFn(r)}</td>`;
    html += `</tr>`;
  });
  html += `</tbody></table></div>`;
  return html;
}

/* ── Init ──────────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  checkDbStatus();
});
