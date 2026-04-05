/**
 * Leadway Householder Pricing Engine
 * Multi-page flow: Select -> Quote Builder -> Results
 * Uses official Leadway rate tables (Building + Content sections)
 */

let clientType = 'individual';

// Corporate rate bands for display
const CORPORATE_BUILDING_RATES = { basic: 0.125, bronze: 0.125, silver: 0.15, standard: 0.15, gold: 0.175, platinum: 0.185 };
const CORPORATE_CONTENT_RATES = { basic: 0.30, bronze: 0.30, silver: 0.35, standard: 0.35, gold: 0.45, platinum: 0.50 };

// ============= PAGE NAVIGATION =============

function showPage(pageId) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active-page'));
    document.getElementById(pageId).classList.add('active-page');
    const footer = document.getElementById('mainFooter');
    if (footer) footer.style.display = pageId === 'page-select' ? '' : 'none';
    window.scrollTo(0, 0);
    if (window.lucide) lucide.createIcons();
}

function selectProduct(type) {
    clientType = type;
    updateTypeToggle();
    updateInfoPanel();
    updateRateDisplay();
    showPage('page-quote');
}

function goBack() { showPage('page-select'); }
function goToQuote() { showPage('page-quote'); }

// ============= TYPE TOGGLE =============

function switchType(type) {
    clientType = type;
    updateTypeToggle();
    updateInfoPanel();
    updateRateDisplay();
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
        desc.textContent = 'Comprehensive cover for commercial buildings, office contents, and business assets. Underwritten rates with volume discounts.';
        feat3.textContent = 'Volume discounts for sums over N100M';
    } else {
        title.textContent = 'Protect What Matters';
        desc.textContent = 'Get comprehensive cover for your home and personal property — using Leadway\'s official pre-priced rates.';
        feat3.textContent = 'Discounts for security & fire equipment';
    }
}

function updateRateDisplay() {
    const coverType = (document.getElementById('coverType') || {}).value || 'standard';
    const rb = document.getElementById('rateBuilding');
    const rc = document.getElementById('rateContent');
    if (!rb || !rc) return;

    if (clientType === 'corporate') {
        rb.textContent = (CORPORATE_BUILDING_RATES[coverType] || 0.15) + '%';
        rc.textContent = (CORPORATE_CONTENT_RATES[coverType] || 0.35) + '%';
    } else {
        rb.textContent = '0.10%';
        rc.textContent = '0.20%';
    }
}

// ============= FORM HELPERS =============

function formatCurrency(input) {
    let value = input.value.replace(/[^0-9]/g, '');
    if (value) value = parseInt(value, 10).toLocaleString('en-NG');
    input.value = value;
}

function parseCurrency(str) {
    return parseFloat((str || '').replace(/[^0-9.-]/g, '')) || 0;
}

function formatNGN(amount) {
    return '\u20A6' + amount.toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function toggleChip(checkbox) {
    checkbox.closest('.peril-chip').classList.toggle('selected', checkbox.checked);
}

function toggleCoverage(checkbox) {
    checkbox.closest('.coverage-option').classList.toggle('selected', checkbox.checked);
}

// ============= GENERATE QUOTE =============

async function getQuote() {
    const buildingSI = parseCurrency(document.getElementById('buildingSI').value);
    const contentSI = parseCurrency(document.getElementById('contentSI').value);
    const location = document.getElementById('location').value;
    const coverType = document.getElementById('coverType').value;
    const duration = parseInt(document.getElementById('duration').value);
    const buildingAge = parseInt(document.getElementById('buildingAge').value) || 0;
    const claimsHistory = parseInt(document.getElementById('claimsHistory').value);
    const hasSecurity = document.getElementById('hasSecurity').checked;
    const hasFireExtinguisher = document.getElementById('hasFireExtinguisher').checked;

    // Coverages
    const incBuilding = document.getElementById('incBuilding').checked;
    const incContent = document.getElementById('incContent').checked;
    const incAccidental = document.getElementById('incAccidental').checked;
    const incAllRisks = document.getElementById('incAllRisks').checked;
    const incPA = document.getElementById('incPA').checked;
    const incAltAcc = document.getElementById('incAltAcc').checked;

    // Validation
    if (buildingSI <= 0 && contentSI <= 0) {
        alert('Please enter at least one Sum Insured (Building or Content).');
        return;
    }
    if (!location) { alert('Please select a location.'); return; }
    if (!incBuilding && !incContent && !incAccidental && !incAllRisks && !incPA && !incAltAcc) {
        alert('Please select at least one coverage.'); return;
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
                building_sum_insured: buildingSI,
                content_sum_insured: contentSI,
                location,
                cover_type: coverType,
                include_building: incBuilding,
                include_content: incContent,
                include_accidental_damage: incAccidental,
                include_all_risks: incAllRisks,
                include_personal_accident: incPA,
                include_alt_accommodation: incAltAcc,
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
        displayResults(data, buildingSI, contentSI, location, coverType, duration);

    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.textContent = 'Get Your Householder Quote';
    }
}

// ============= DISPLAY RESULTS =============

function displayResults(data, buildingSI, contentSI, location, coverType, duration) {
    // Left panel
    document.getElementById('grossPremiumBig').textContent = formatNGN(data.gross_premium);
    document.getElementById('rateDisplay').textContent = 'Rate: ' + data.rate_per_mille.toFixed(2) + ' per mille';
    document.getElementById('resultsTitle').textContent =
        (clientType === 'corporate' ? 'Corporate' : 'Individual') + ' Quote';

    // Section mini cards
    const sections = [
        { label: 'Building', amount: data.building_premium, icon: 'building', cls: 'fire-mini' },
        { label: 'Content', amount: data.content_premium, icon: 'sofa', cls: 'theft-mini' },
        { label: 'Accidental Damage', amount: data.accidental_damage_premium, icon: 'alert-triangle', cls: 'flood-mini' },
        { label: 'All Risks', amount: data.all_risks_premium, icon: 'shield-check', cls: 'fire-mini' },
        { label: 'Personal Accident', amount: data.personal_accident_premium, icon: 'heart-pulse', cls: 'theft-mini' },
        { label: 'Alt. Accommodation', amount: data.alt_accommodation_premium, icon: 'bed', cls: 'flood-mini' },
    ];

    const cardsHtml = sections
        .filter(s => s.amount > 0)
        .map(s => `
            <div class="peril-mini">
                <div class="peril-mini-icon ${s.cls}"><i data-lucide="${s.icon}" style="width:16px;height:16px;"></i></div>
                <div>
                    <span class="peril-mini-label">${s.label}</span>
                    <span class="peril-mini-amount">${formatNGN(s.amount)}</span>
                </div>
            </div>
        `).join('');
    document.getElementById('sectionCards').innerHTML = cardsHtml;

    // Right panel badges
    document.getElementById('clientBadge').textContent = clientType.toUpperCase();
    document.getElementById('coverBadge').textContent = coverType.toUpperCase();

    // Summary
    const totalSI = buildingSI + contentSI;
    document.getElementById('sumDisplay').textContent = formatNGN(totalSI);
    const locMap = { lagos: 'Lagos', abuja: 'Abuja', port_harcourt: 'Port Harcourt', ibadan: 'Ibadan', kaduna: 'Kaduna', other: 'Other' };
    document.getElementById('locDisplay').textContent = locMap[location] || location;
    document.getElementById('perilsDisplay').textContent = data.coverages.length + ' coverages';
    document.getElementById('durationDisplay').textContent = duration + ' months';

    // Breakdown table
    const rows = [
        ['Base Premium (all sections)', data.base_premium, ''],
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
        const displayAmt = amount < 0 ? '-' + formatNGN(Math.abs(amount)) : '+' + formatNGN(amount);
        html += `<tr><td>${label}</td><td class="${cls}">${displayAmt}</td></tr>`;
    }
    document.getElementById('breakdownBody').innerHTML = html;

    // Net
    document.getElementById('grossNet').textContent = formatNGN(data.gross_premium);
    document.getElementById('commNet').textContent = '-' + formatNGN(data.commission);
    document.getElementById('netNet').textContent = formatNGN(data.net_premium);

    showPage('page-results');
}

// ============= INIT =============
document.addEventListener('DOMContentLoaded', () => {
    showPage('page-select');
});
