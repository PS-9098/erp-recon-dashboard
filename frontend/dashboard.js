document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    document.getElementById('refresh-btn').addEventListener('click', loadDashboard);
});

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IE', {
        style: 'currency',
        currency: 'EUR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

async function loadDashboard() {
    setLoading(true);
    try {
        const [invoicesRes, discrepanciesRes, agingRes] = await Promise.all([
            fetch('/api/outstanding-invoices'),
            fetch('/api/discrepancies'),
            fetch('/api/aging-summary')
        ]);

        if (!invoicesRes.ok || !discrepanciesRes.ok || !agingRes.ok) {
            throw new Error('One or more API calls failed');
        }

        const invoices = await invoicesRes.json();
        const discrepancies = await discrepanciesRes.json();
        const aging = await agingRes.json();

        renderInvoices(invoices);
        renderDiscrepancies(discrepancies);
        renderAging(aging);
    } catch (error) {
        console.error('Dashboard load error:', error);
        document.getElementById('invoices-tbody').innerHTML = `<tr><td colspan="6" class="loading">Failed to load data</td></tr>`;
        document.getElementById('discrepancies-list').innerHTML = '<div class="loading">Failed to load discrepancies</div>';
        document.getElementById('aging-container').innerHTML = '<div class="loading">Failed to load aging summary</div>';
    } finally {
        setLoading(false);
    }
}

function setLoading(isLoading) {
    const btn = document.getElementById('refresh-btn');
    btn.disabled = isLoading;
    btn.textContent = isLoading ? 'Loading...' : 'Refresh Data';
}

function renderInvoices(invoices) {
    const tbody = document.getElementById('invoices-tbody');
    if (!invoices || invoices.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No outstanding invoices</td></tr>';
        return;
    }

    tbody.innerHTML = invoices.map(inv => `
        <tr>
            <td>${escapeHtml(inv.invoice_number)}</td>
            <td>${escapeHtml(inv.vendor_name)}</td>
            <td>${formatCurrency(inv.amount)}</td>
            <td>${inv.due_date}</td>
            <td>${inv.days_overdue}</td>
            <td><span class="status-badge status-${inv.status}">${capitalize(inv.status)}</span></td>
        </tr>
    `).join('');
}

function renderDiscrepancies(discrepancies) {
    const container = document.getElementById('discrepancies-list');
    if (!discrepancies || discrepancies.length === 0) {
        container.innerHTML = '<div class="loading">No discrepancies found</div>';
        return;
    }

    container.innerHTML = discrepancies.map(d => `
        <div class="discrepancy-item">
            <div>
                <strong>${escapeHtml(d.invoice_number)}</strong> – ${escapeHtml(d.vendor_name)}<br>
                <small>Invoice: ${formatCurrency(d.invoice_amount)}</small>
                ${d.gl_amount !== null ? `<small> | GL: ${formatCurrency(d.gl_amount)}</small>` : ''}
            </div>
            <span class="issue-tag">${escapeHtml(d.issue)}</span>
        </div>
    `).join('');
}

function renderAging(aging) {
    const container = document.getElementById('aging-container');
    const buckets = [
        { key: 'bucket_0_30', label: '0–30 days', count: aging.bucket_0_30 || 0 },
        { key: 'bucket_31_60', label: '31–60 days', count: aging.bucket_31_60 || 0 },
        { key: 'bucket_61_90', label: '61–90 days', count: aging.bucket_61_90 || 0 },
        { key: 'bucket_90_plus', label: '90+ days', count: aging.bucket_90_plus || 0 }
    ];

    const maxCount = Math.max(...buckets.map(b => b.count), 1);

    container.innerHTML = `
        <div class="aging-bars">
            ${buckets.map(b => `
                <div class="aging-row">
                    <div class="aging-label">${b.label}</div>
                    <div class="bar-wrapper">
                        <div class="bar ${b.key}" style="width: ${(b.count / maxCount) * 100}%">
                            ${b.count > 0 ? b.count : ''}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
        <small style="color: var(--text-light); margin-top: 0.5rem; display: block;">Total outstanding: ${buckets.reduce((sum, b) => sum + b.count, 0)}</small>
    `;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}