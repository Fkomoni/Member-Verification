/**
 * Leadway Householder Pricing Engine — Frontend Logic
 */

let clientType = 'individual';

const SEGMENT_DESCRIPTIONS = {
    individual: 'Individual policies for homeowners and tenants. Covers personal property and household contents.',
    corporate: 'Corporate policies for businesses and commercial properties. Lower base rates with volume discounts for large sums insured.'
};

function setClientType(type) {
    clientType = type;
    document.querySelectorAll('.segment-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === type);
    });
    document.getElementById('segmentDesc').textContent = SEGMENT_DESCRIPTIONS[type];

    // Hide results
    document.getElementById('resultsPanel').classList.remove('visible');
    document.getElementById('resultsPlaceholder').style.display = '';

    // Re-initialize icons after DOM changes
    if (window.lucide) lucide.createIcons();
}

function togglePeril(checkbox) {
    const option = checkbox.closest('.peril-option');
    option.classList.toggle('selected', checkbox.checked);
}

function formatCurrency(input) {
    let value = input.value.replace(/[^0-9]/g, '');
    if (value) {
        value = parseInt(value, 10).toLocaleString('en-NG');
    }
    input.value = value;
}

function parseCurrency(str) {
    return parseFloat(str.replace(/[^0-9.-]/g, '')) || 0;
}

function formatNGN(amount) {
    return '\u20A6' + amount.toLocaleString('en-NG', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function getSelectedPerils() {
    const perils = [];
    document.querySelectorAll('.peril-option input[type="checkbox"]:checked').forEach(cb => {
        perils.push(cb.value);
    });
    return perils;
}

function resetForm() {
    document.getElementById('sumInsured').value = '';
    document.getElementById('location').value = '';
    document.getElementById('coverType').value = 'standard';
    document.getElementById('duration').value = '12';
    document.getElementById('buildingAge').value = '0';
    document.getElementById('claimsHistory').value = '0';
    document.getElementById('hasSecurity').checked = false;
    document.getElementById('hasFireExtinguisher').checked = false;

    // Reset perils — only fire checked
    document.querySelectorAll('.peril-option input[type="checkbox"]').forEach(cb => {
        const isFire = cb.value === 'fire';
        cb.checked = isFire;
        cb.closest('.peril-option').classList.toggle('selected', isFire);
    });

    document.getElementById('resultsPanel').classList.remove('visible');
    document.getElementById('resultsPlaceholder').style.display = '';
}

async function getQuote() {
    const sumInsured = parseCurrency(document.getElementById('sumInsured').value);
    const location = document.getElementById('location').value;
    const coverType = document.getElementById('coverType').value;
    const duration = parseInt(document.getElementById('duration').value);
    const buildingAge = parseInt(document.getElementById('buildingAge').value) || 0;
    const claimsHistory = parseInt(document.getElementById('claimsHistory').value);
    const hasSecurity = document.getElementById('hasSecurity').checked;
    const hasFireExtinguisher = document.getElementById('hasFireExtinguisher').checked;
    const perils = getSelectedPerils();

    // Validation
    if (!sumInsured || sumInsured <= 0) {
        alert('Please enter a valid Sum Insured amount.');
        return;
    }
    if (!location) {
        alert('Please select a location.');
        return;
    }
    if (perils.length === 0) {
        alert('Please select at least one peril to cover.');
        return;
    }

    const btn = document.getElementById('quoteBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Calculating...';

    try {
        const response = await fetch('/api/quote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_type: clientType,
                sum_insured: sumInsured,
                location: location,
                cover_type: coverType,
                perils: perils,
                building_age_years: buildingAge,
                has_security: hasSecurity,
                has_fire_extinguisher: hasFireExtinguisher,
                claims_history_count: claimsHistory,
                policy_duration_months: duration,
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to generate quote');
        }

        const data = await response.json();
        displayResults(data, perils, sumInsured);

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Generate Quote <i data-lucide="arrow-right" style="width:18px;height:18px;"></i>';
        if (window.lucide) lucide.createIcons();
    }
}

function displayResults(data, selectedPerils, sumInsured) {
    // Hide placeholder, show results
    document.getElementById('resultsPlaceholder').style.display = 'none';
    const panel = document.getElementById('resultsPanel');

    // Client badge
    document.getElementById('clientBadge').textContent = data.client_type.toUpperCase();

    // Rate
    document.getElementById('rateBadge').textContent =
        `Rate: ${data.rate_per_mille.toFixed(2)} per mille`;

    // Gross premium
    document.getElementById('grossPremium').textContent = formatNGN(data.gross_premium);

    // Sub text
    document.getElementById('premiumSub').textContent =
        `Sum Insured: ${formatNGN(sumInsured)}`;

    // Peril cards
    const perilMap = {
        fire: { card: 'fireCard', amount: 'fireAmount', value: data.fire_premium },
        theft: { card: 'theftCard', amount: 'theftAmount', value: data.theft_premium },
        flood: { card: 'floodCard', amount: 'floodAmount', value: data.flood_premium },
    };

    for (const [peril, info] of Object.entries(perilMap)) {
        const card = document.getElementById(info.card);
        const amountEl = document.getElementById(info.amount);
        if (selectedPerils.includes(peril)) {
            card.classList.remove('inactive');
            amountEl.textContent = formatNGN(info.value);
        } else {
            card.classList.add('inactive');
            amountEl.textContent = 'N/A';
        }
    }

    // Breakdown table
    const rows = [
        ['Base Premium', data.base_premium, ''],
        ['Location Adjustment', data.location_adjustment, data.location_adjustment > 0 ? 'loading' : data.location_adjustment < 0 ? 'discount' : ''],
        ['Cover Type Adjustment', data.cover_type_adjustment, data.cover_type_adjustment > 0 ? 'loading' : data.cover_type_adjustment < 0 ? 'discount' : ''],
        ['Claims History Loading', data.claims_loading, data.claims_loading > 0 ? 'loading' : ''],
        ['Security Discount', -data.security_discount, data.security_discount > 0 ? 'discount' : ''],
        ['Fire Equipment Discount', -data.fire_equipment_discount, data.fire_equipment_discount > 0 ? 'discount' : ''],
        ['Duration Adjustment', data.duration_adjustment, data.duration_adjustment !== 0 ? 'loading' : ''],
    ];

    let html = '';
    for (const [label, amount, cls] of rows) {
        if (amount === 0) continue;
        const sign = amount > 0 ? '+' : '';
        html += `<tr>
            <td>${label}</td>
            <td class="${cls}">${sign}${formatNGN(Math.abs(amount))}${amount < 0 ? ' (-)' : ''}</td>
        </tr>`;
    }

    html += `<tr class="total-row">
        <td>Gross Premium</td>
        <td>${formatNGN(data.gross_premium)}</td>
    </tr>`;

    document.getElementById('breakdownBody').innerHTML = html;

    // Net premium card
    document.getElementById('commissionAmount').textContent = '-' + formatNGN(data.commission);
    document.getElementById('netPremium').textContent = formatNGN(data.net_premium);

    // Show panel
    panel.classList.add('visible');

    // Re-init icons
    if (window.lucide) lucide.createIcons();

    // Scroll to results on mobile
    if (window.innerWidth <= 1024) {
        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Smooth scroll for anchor links
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
