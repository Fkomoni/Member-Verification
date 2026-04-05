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

const BUILDING_IMAGES = {
    individual: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=400&h=180&fit=crop&q=90',
    corporate: 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=180&fit=crop&q=90',
};

function selectCoverType(val) {
    document.getElementById('coverType').value = val;
    document.querySelectorAll('.ct-card').forEach(c => {
        c.classList.toggle('active', c.dataset.val === val);
    });
    updateRateDisplay();
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

    // Swap building coverage image based on client type
    const bldgImg = document.getElementById('buildingCovImg');
    if (bldgImg) bldgImg.src = BUILDING_IMAGES[clientType] || BUILDING_IMAGES.individual;
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
    checkbox.closest('.cov-card').classList.toggle('selected', checkbox.checked);
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
    // Store for payment/policy generation
    lastQuoteData = data;
    lastQuoteParams = {
        client_type: clientType,
        building_sum_insured: buildingSI,
        content_sum_insured: contentSI,
        location: location,
        cover_type: document.getElementById('coverType').value,
        include_building: document.getElementById('incBuilding').checked,
        include_content: document.getElementById('incContent').checked,
        include_accidental_damage: document.getElementById('incAccidental').checked,
        include_all_risks: document.getElementById('incAllRisks').checked,
        include_personal_accident: document.getElementById('incPA').checked,
        include_alt_accommodation: document.getElementById('incAltAcc').checked,
        building_age_years: parseInt(document.getElementById('buildingAge').value) || 0,
        has_security: document.getElementById('hasSecurity').checked,
        has_fire_extinguisher: document.getElementById('hasFireExtinguisher').checked,
        claims_history_count: parseInt(document.getElementById('claimsHistory').value),
        policy_duration_months: duration,
    };

    // Reset payment state
    document.getElementById('paymentSection').style.display = '';
    document.getElementById('paymentSuccess').style.display = 'none';
    document.getElementById('payAmount').textContent = formatNGN(data.gross_premium);

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

// ============= PAYMENT & POLICY =============

let lastQuoteData = null;
let lastQuoteParams = null;
let paymentReference = null;

function initiatePayment() {
    const name = document.getElementById('payName').value.trim();
    const email = document.getElementById('payEmail').value.trim();
    const phone = document.getElementById('payPhone').value.trim();

    if (!name) { alert('Please enter your full name.'); return; }
    if (!email || !email.includes('@')) { alert('Please enter a valid email address.'); return; }
    if (!phone) { alert('Please enter your phone number.'); return; }

    const amount = lastQuoteData.gross_premium;

    // Fetch Paystack public key then initiate
    fetch('/api/paystack-key')
        .then(r => r.json())
        .then(data => {
            const handler = PaystackPop.setup({
                key: data.public_key,
                email: email,
                amount: Math.round(amount * 100), // Paystack expects kobo
                currency: 'NGN',
                ref: 'LW-HH-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6),
                metadata: {
                    custom_fields: [
                        { display_name: "Customer Name", variable_name: "customer_name", value: name },
                        { display_name: "Phone", variable_name: "phone", value: phone },
                        { display_name: "Product", variable_name: "product", value: "Householder Insurance" },
                    ]
                },
                callback: function(response) {
                    // Payment successful
                    paymentReference = response.reference;
                    onPaymentSuccess(name, email, phone);
                },
                onClose: function() {
                    // User closed payment window
                }
            });
            handler.openIframe();
        })
        .catch(err => {
            alert('Could not initialize payment: ' + err.message);
        });
}

function onPaymentSuccess(name, email, phone) {
    // Hide payment form, show success
    document.getElementById('paymentSection').style.display = 'none';
    document.getElementById('paymentSuccess').style.display = 'block';
    if (window.lucide) lucide.createIcons();
}

async function downloadPolicy() {
    const btn = document.getElementById('downloadPolicyBtn');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Generating...';

    const name = document.getElementById('payName').value.trim();
    const email = document.getElementById('payEmail').value.trim();
    const phone = document.getElementById('payPhone').value.trim();
    const address = document.getElementById('payAddress').value.trim();

    try {
        const response = await fetch('/api/generate-policy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_name: name,
                customer_email: email,
                customer_phone: phone,
                address: address,
                payment_reference: paymentReference || 'N/A',
                ...lastQuoteParams,
            })
        });

        if (!response.ok) throw new Error('Failed to generate policy');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Leadway-Householder-Policy-${name.replace(/\s+/g, '-')}.pdf`;
        a.click();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        alert('Error generating policy: ' + error.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="download" style="width:16px;height:16px;"></i> Download Your Policy Document';
        if (window.lucide) lucide.createIcons();
    }
}

// ============= POLICY SUMMARY =============

function showPolicySummary() {
    const html = `
        <div style="max-height:70vh;overflow-y:auto;">
            <h2 style="font-size:22px;font-weight:700;margin-bottom:4px;">Houseowners & Householders Insurance Policy</h2>
            <p style="color:#6C757D;font-size:13px;margin-bottom:24px;">Leadway Assurance Company Limited — Policy Summary</p>

            <div style="background:#FEF0EB;border-left:4px solid #FF6B22;padding:16px;border-radius:8px;margin-bottom:20px;">
                <strong style="color:#FF6B22;">5 Sections of Cover</strong>
                <p style="font-size:13px;color:#495057;margin-top:4px;">This policy covers buildings, contents, alternative accommodation, public liability, and personal accident.</p>
            </div>

            <h3 style="font-size:16px;margin-bottom:12px;color:#FF6B22;">Sections Covered</h3>
            <table style="width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px;">
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;font-weight:700;">Section I</td><td style="padding:10px 0;">Loss or Damage to the <strong>Buildings</strong></td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;font-weight:700;">Section II</td><td style="padding:10px 0;">Loss or Damage to the <strong>Contents</strong></td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;font-weight:700;">Section III</td><td style="padding:10px 0;"><strong>Alternative Accommodation</strong> & Loss of Rent</td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;font-weight:700;">Section IV</td><td style="padding:10px 0;"><strong>Liability to the Public</strong></td></tr>
                <tr><td style="padding:10px 0;font-weight:700;">Section V</td><td style="padding:10px 0;"><strong>Compensation for Death</strong> of the Insured</td></tr>
            </table>

            <h3 style="font-size:16px;margin-bottom:12px;color:#FF6B22;">Insured Perils</h3>
            <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:24px;">
                ${['Fire', 'Lightning', 'Explosion', 'Theft', 'Riot & Strike', 'Malicious Damage', 'Aircraft Impact', 'Burst Pipes', 'Impact Damage', 'Earthquake / Volcano', 'Hurricane / Cyclone', 'Flood', 'Storm'].map(p => `<span style="padding:6px 14px;background:#FEF0EB;border-radius:100px;font-size:12px;font-weight:600;color:#FF6B22;">${p}</span>`).join('')}
            </div>

            <h3 style="font-size:16px;margin-bottom:12px;color:#FF6B22;">Limits of Liability</h3>
            <table style="width:100%;border-collapse:collapse;margin-bottom:24px;font-size:13px;">
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;">Section I (Building)</td><td style="padding:10px 0;font-weight:600;">Sum Insured on each item</td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;">Section II (Content)</td><td style="padding:10px 0;font-weight:600;">3% per article (Jewellery exclusive)</td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;">Platinum items (Gold, Silver, Art)</td><td style="padding:10px 0;font-weight:600;">10% of Contents SI or N500,000</td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;">Section III (Alt. Accommodation)</td><td style="padding:10px 0;font-weight:600;">10% Building SI + 10% Contents SI</td></tr>
                <tr style="border-bottom:1px solid #E8EAED;"><td style="padding:10px 0;">Section IV (Public Liability)</td><td style="padding:10px 0;font-weight:600;">N250,000 per event</td></tr>
                <tr><td style="padding:10px 0;">Section V (Death Compensation)</td><td style="padding:10px 0;font-weight:600;">N25,000 or half Total Sum</td></tr>
            </table>

            <h3 style="font-size:16px;margin-bottom:12px;color:#FF6B22;">Key Conditions</h3>
            <ul style="font-size:13px;color:#495057;padding-left:20px;line-height:1.8;margin-bottom:24px;">
                <li>Theft cover only if accompanied by actual forcible and violent breaking in or out</li>
                <li>Flood includes natural/artificial water, storm surges, overflowing waterways</li>
                <li>No single jewelry item > 2.5% of contents SI (unless specifically insured)</li>
                <li>Policy frequency: Annual</li>
                <li>Currency: NGN</li>
            </ul>

            <div style="text-align:center;padding-top:16px;border-top:1px solid #E8EAED;">
                <a href="/static/Leadway-Householder-Policy.pdf" target="_blank" style="display:inline-flex;align-items:center;gap:8px;padding:12px 28px;background:#FF6B22;color:#fff;border-radius:8px;font-weight:600;font-size:14px;text-decoration:none;">
                    Download Full Policy (PDF)
                </a>
            </div>
        </div>
    `;

    const overlay = document.createElement('div');
    overlay.id = 'policySummaryOverlay';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px;';
    overlay.onclick = (ev) => { if (ev.target === overlay) overlay.remove(); };
    overlay.innerHTML = `<div style="background:#fff;border-radius:16px;max-width:720px;width:100%;padding:36px;position:relative;"><button onclick="document.getElementById('policySummaryOverlay').remove()" style="position:absolute;top:16px;right:16px;background:none;border:none;font-size:24px;cursor:pointer;color:#6C757D;">&times;</button>${html}</div>`;
    document.body.appendChild(overlay);
}

// ============= RATE CARD =============

async function showRateCard(e) {
    if (e) e.preventDefault();
    try {
        const res = await fetch('/api/rates');
        const data = await res.json();
        let html = '<h3 style="margin-bottom:16px;">Individual (Pre-Priced) Rates</h3><table class="breakdown-table">';
        const labels = {building:'Building (Fire & Special Perils)',content:'Content (Fire, Burglary & Special Perils)',accidental_damage:'Accidental Damage',all_risks:'All Risks Extension',personal_accident:'Personal Accident',alt_accommodation:'Alternative Accommodation'};
        for (const [k,v] of Object.entries(data.individual_rates)) {
            html += `<tr><td>${labels[k]||k}</td><td>${(v*100).toFixed(3)}%</td></tr>`;
        }
        html += '</table><h3 style="margin:24px 0 16px;">Corporate (Underwritten) Rates</h3><table class="breakdown-table"><tr><td><strong>Section</strong></td><td><strong>Band 1</strong></td><td><strong>Band 2</strong></td><td><strong>Band 3</strong></td><td><strong>Band 4</strong></td></tr>';
        for (const [section, bands] of Object.entries(data.corporate_rates)) {
            html += `<tr><td>${section.charAt(0).toUpperCase()+section.slice(1)}</td>`;
            for (const b of Object.values(bands)) html += `<td>${(b*100).toFixed(3)}%</td>`;
            html += '</tr>';
        }
        html += '</table>';
        // Show in a modal-like overlay
        const overlay = document.createElement('div');
        overlay.id = 'rateCardOverlay';
        overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:20px;';
        overlay.onclick = (ev) => { if (ev.target === overlay) overlay.remove(); };
        overlay.innerHTML = `<div style="background:#fff;border-radius:16px;max-width:700px;width:100%;max-height:80vh;overflow-y:auto;padding:36px;position:relative;"><button onclick="document.getElementById('rateCardOverlay').remove()" style="position:absolute;top:16px;right:16px;background:none;border:none;font-size:24px;cursor:pointer;color:#6C757D;">&times;</button><h2 style="font-size:24px;font-weight:700;margin-bottom:8px;">Leadway Householder Rate Card</h2><p style="color:#6C757D;font-size:13px;margin-bottom:24px;">Official rates from Leadway Assurance PRICING.xlsx</p>${html}</div>`;
        document.body.appendChild(overlay);
    } catch (err) {
        alert('Failed to load rate card: ' + err.message);
    }
}

// ============= INIT =============
document.addEventListener('DOMContentLoaded', () => {
    showPage('page-select');
});
