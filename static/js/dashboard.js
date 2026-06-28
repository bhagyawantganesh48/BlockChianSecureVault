/**
 * Dashboard Chart.js visualizations
 */

document.addEventListener('DOMContentLoaded', () => {
    if (!window.dashboardData || typeof Chart === 'undefined') return;

    const chartDefaults = {
        responsive: true,
        plugins: {
            legend: {
                labels: { color: '#94a3b8' },
            },
        },
    };

    const categoryCanvas = document.getElementById('categoryChart');
    if (categoryCanvas) {
        const categories = window.dashboardData.categories || {};
        const labels = Object.keys(categories);
        const values = Object.values(categories);

        new Chart(categoryCanvas, {
            type: 'doughnut',
            data: {
                labels: labels.length ? labels : ['No Data'],
                datasets: [{
                    data: values.length ? values : [1],
                    backgroundColor: [
                        '#06b6d4', '#8b5cf6', '#10b981', '#f59e0b',
                        '#ef4444', '#ec4899', '#6366f1', '#14b8a6',
                    ],
                    borderWidth: 0,
                }],
            },
            options: {
                ...chartDefaults,
                plugins: {
                    ...chartDefaults.plugins,
                    legend: { position: 'bottom', labels: { color: '#94a3b8', padding: 16 } },
                },
            },
        });
    }

    const strengthCanvas = document.getElementById('strengthChart');
    if (strengthCanvas) {
        const strength = window.dashboardData.strength || {};
        new Chart(strengthCanvas, {
            type: 'bar',
            data: {
                labels: ['Strong', 'Medium', 'Weak'],
                datasets: [{
                    label: 'Passwords',
                    data: [
                        strength.Strong || 0,
                        strength.Medium || 0,
                        strength.Weak || 0,
                    ],
                    backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
                    borderRadius: 8,
                    borderSkipped: false,
                }],
            },
            options: {
                ...chartDefaults,
                scales: {
                    x: {
                        ticks: { color: '#94a3b8' },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#94a3b8', stepSize: 1 },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                    },
                },
                plugins: {
                    legend: { display: false },
                },
            },
        });
    }
});
