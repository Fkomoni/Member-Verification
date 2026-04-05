/**
 * Leadway Householder Pricing Engine
 * Multi-page flow: Select -> Quote Builder -> Results
 */

let clientType = 'individual';

// ============= PAGE NAVIGATION =============

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active-page'));
    document.getElementById(pageId).classList.add('active-page');

    // Show footer only on select page
    const footer = document.getElementById('mainFooter');
    if (footer) footer.style.display = pageId === 'page-select' ? '' : 'none';

    // Scroll to top
    window.scrollTo(0, 0);

    // Re-init icons
    if (window.lucide) lucide.createIcons();
}

function selectProduct(type) {
    clientType = type;
    updateTypeToggle();
    updateInfoPanel();
    showPage('page-quote');
}

function goBack() {
    showPage('page-select');
}

function goToQuote() {
    showPage('page-quote');
}

// ============= TYPE TOGGLE =============

function switchType(type) {
    clientType = type;
    updateTypeToggle();
    updateInfoPanel();
}

function updateTypeToggle() {
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === clientType);
    });
}

function updateInfoPanel() {
    const title = document.getElementById('infoTitle');
    const desc = document.getElementById('infoDesc');
    const feat3 = document.getElementById('infoFeature3');

    if (clientType === 'corporate') {
        title.textContent = 'Cover Your Business Property';
        desc.textContent = 'Comprehensive cover for commercial buildings, office contents, and business assets. Volume discounts for large sums insured.';
        feat3.textContent = 'Volume discounts for sums over N100M';
    } else {
        title.textContent = 'Protect What Matters';
        desc.textContent = 'Get comprehensive cover for your home and personal property against the most common risks — with pricing powered by real claims data.';
        feat3.textContent = 'Discounts for security & fire equipment';
    }
}

// ============= FORM HELPERS =============

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

function toggleChip(checkbox) {
    checkbox.closest('.peril-chip').classList.toggle('selected', checkbox.checked);
}

function getSelectedPerils() {
    const perils = [];
    document.querySelectorAll('.peril-chip input:checked').forEach(cb => perils.push(cb.value));
    return perils;
}

// ============= GENERATE QUOTE =============

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
    if (!sumInsured || sumInsured <= 0) { alert('Please enter a valid Sum Insured amount.'); return; }
    if (!location) { alert('Please select a location.'); return; }
    if (perils.length === 0) { alert('Please select at least one peril to cover.'); return; }

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
                location,
                cover_type: coverType,
                perils,
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
        displayResults(data, perils, sumInsured, location, coverType, duration);

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Get Your Householder Quote';
    }
}

// ============= DISPLAY RESULTS =============

function displayResults(data, selectedPerils, sumInsured, location, coverType, duration) {
    // Left panel
    document.getElementById('grossPremiumBig').textContent = formatNGN(data.gross_premium);
    document.getElementById('rateDisplay').textContent = 'Rate: ' + data.rate_per_mille.toFixed(2) + ' per mille';
    document.getElementById('resultsTitle').textContent =
        (clientType === 'corporate' ? 'Corporate' : 'Individual') + ' Quote';

    // Peril mini cards
    const perilMinis = {
        fire: { card: 'miniFireCard', amount: 'miniFireAmt', value: data.fire_premium },
        theft: { card: 'miniTheftCard', amount: 'miniTheftAmt', value: data.theft_premium },
        flood: { card: 'miniFloodCard', amount: 'miniFloodAmt', value: data.flood_premium },
    };
    for (const [peril, info] of Object.entries(perilMinis)) {
        const card = document.getElementById(info.card);
        const amt = document.getElementById(info.amount);
        if (selectedPerils.includes(peril)) {
            card.classList.remove('inactive');
            amt.textContent = formatNGN(info.value);
        } else {
            card.classList.add('inactive');
            amt.textContent = 'Not covered';
        }
    }

    // Right panel
    document.getElementById('clientBadge').textContent = clientType.toUpperCase();
    document.getElementById('coverBadge').textContent = coverType.toUpperCase();

    // Summary
    document.getElementById('sumDisplay').textContent = formatNGN(sumInsured);
    const locMap = { lagos: 'Lagos', abuja: 'Abuja', port_harcourt: 'Port Harcourt', ibadan: 'Ibadan', kaduna: 'Kaduna', other: 'Other' };
    document.getElementById('locDisplay').textContent = locMap[location] || location;
    document.getElementById('perilsDisplay').textContent = selectedPerils.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(', ');
    document.getElementById('durationDisplay').textContent = duration + ' months';

    // Breakdown
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
        const displayAmt = amount < 0 ? '-' + formatNGN(Math.abs(amount)) : '+' + formatNGN(amount);
        html += `<tr><td>${label}</td><td class="${cls}">${displayAmt}</td></tr>`;
    }
    document.getElementById('breakdownBody').innerHTML = html;

    // Net
    document.getElementById('grossNet').textContent = formatNGN(data.gross_premium);
    document.getElementById('commNet').textContent = '-' + formatNGN(data.commission);
    document.getElementById('netNet').textContent = formatNGN(data.net_premium);

    // Show results page
    showPage('page-results');
}

// ============= INIT =============
document.addEventListener('DOMContentLoaded', () => {
    showPage('page-select');
});
