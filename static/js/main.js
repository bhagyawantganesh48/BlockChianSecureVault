/**
 * Main application JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    initSidebarToggle();
    initPasswordToggle();
    initRevealPassword();
    initCopyButtons();
    initFormLoading();
});

function initSidebarToggle() {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    if (toggle && sidebar) {
        toggle.addEventListener('click', () => sidebar.classList.toggle('show'));
    }
}

function initPasswordToggle() {
    document.querySelectorAll('.toggle-password').forEach((btn) => {
        btn.addEventListener('click', () => {
            const target = document.querySelector(btn.dataset.target);
            if (!target) return;
            const isPassword = target.type === 'password';
            target.type = isPassword ? 'text' : 'password';
            btn.querySelector('i').className = isPassword ? 'bi bi-eye-slash' : 'bi bi-eye';
        });
    });
}

function initRevealPassword() {
    const revealed = {};

    document.querySelectorAll('.reveal-btn').forEach((btn) => {
        btn.addEventListener('click', async () => {
            const entryId = btn.dataset.entryId;
            const mask = document.querySelector(`.password-mask[data-entry-id="${entryId}"]`);
            const copyBtn = document.querySelector(`.copy-btn[data-entry-id="${entryId}"]`);
            if (!mask) return;

            if (revealed[entryId]) {
                mask.textContent = '••••••••';
                btn.querySelector('i').className = 'bi bi-eye';
                if (copyBtn) copyBtn.classList.add('d-none');
                delete revealed[entryId];
                return;
            }

            showLoading(true);
            try {
                const response = await fetch(`/password/reveal/${entryId}`);
                const data = await response.json();
                if (data.success) {
                    mask.textContent = data.password;
                    btn.querySelector('i').className = 'bi bi-eye-slash';
                    revealed[entryId] = data.password;
                    if (copyBtn) {
                        copyBtn.classList.remove('d-none');
                        copyBtn.onclick = () => copyToClipboard(data.password);
                    }
                } else {
                    showToast('Failed to reveal password', 'danger');
                }
            } catch {
                showToast('Network error', 'danger');
            } finally {
                showLoading(false);
            }
        });
    });
}

function initCopyButtons() {
    document.querySelectorAll('.copy-text-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            const target = document.querySelector(btn.dataset.target);
            if (target) copyToClipboard(target.textContent.trim());
        });
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Copy failed', 'danger');
    });
}

function showToast(message, type = 'info') {
    const existing = document.querySelector('.copy-toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `copy-toast alert alert-${type} glass-alert`;
    toast.innerHTML = `<i class="bi bi-clipboard-check me-2"></i>${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.classList.toggle('d-none', !show);
}

function initFormLoading() {
    document.querySelectorAll('form').forEach((form) => {
        form.addEventListener('submit', () => showLoading(true));
    });
}
