/**
 * Live password strength analyzer
 */

document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.strength-input');
    inputs.forEach((input) => {
        const meter = input.closest('.mb-3, .col-12')?.querySelector('#strengthMeter')
            || document.getElementById('strengthMeter');
        if (!meter) return;

        input.addEventListener('input', debounce(async () => {
            await updateStrengthMeter(input.value, meter);
        }, 200));

        if (input.value) updateStrengthMeter(input.value, meter);
    });
});

async function updateStrengthMeter(password, container) {
    if (!password) {
        container.innerHTML = '';
        return;
    }

    try {
        const response = await fetch('/api/strength', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password }),
        });
        const data = await response.json();
        renderMeter(container, data);
    } catch {
        container.innerHTML = '<span class="text-danger small">Unable to analyze</span>';
    }
}

function renderMeter(container, data) {
    const pct = Math.min((data.score / 5) * 100, 100);
    container.innerHTML = `
        <div class="d-flex justify-content-between align-items-center mb-1">
            <span class="strength-label ${data.strength}">${data.label}</span>
            <span class="strength-details">Entropy: ${data.entropy} bits</span>
        </div>
        <div class="progress mb-2">
            <div class="progress-bar bg-${data.color}" style="width: ${pct}%"></div>
        </div>
        <div class="strength-details d-flex flex-wrap gap-3">
            <span><i class="bi bi-${data.checks.length ? 'check2 text-success' : 'x text-danger'}"></i> 8+ chars</span>
            <span><i class="bi bi-${data.checks.uppercase ? 'check2 text-success' : 'x text-danger'}"></i> Upper</span>
            <span><i class="bi bi-${data.checks.lowercase ? 'check2 text-success' : 'x text-danger'}"></i> Lower</span>
            <span><i class="bi bi-${data.checks.digits ? 'check2 text-success' : 'x text-danger'}"></i> Digits</span>
            <span><i class="bi bi-${data.checks.special ? 'check2 text-success' : 'x text-danger'}"></i> Special</span>
        </div>
    `;
}

function debounce(fn, delay) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}
