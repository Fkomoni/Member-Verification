import React, { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  lookupEnrollee,
  getDiagnoses,
  searchMedications,
  getStates,
  createMedicationRequest,
  getRequestTracking,
  addressAutocomplete,
  getAddressDetails,
  searchPharmacies,
} from "../services/api";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./MedicationRequestPage.module.css";

const EMPTY_MED = {
  drug_name: "", generic_name: "", matched_drug_id: null,
  strength: "", dose: "", frequency: "", duration: "",
};

export default function MedicationRequestPage() {
  const { provider, logout } = useAuth();
  const navigate = useNavigate();

  // ── Enrollee ────────────────────────────────────
  const [enrolleeId, setEnrolleeId] = useState("");
  const [enrolleeData, setEnrolleeData] = useState(null);
  const [enrolleeLookupLoading, setEnrolleeLookupLoading] = useState(false);
  const [enrolleeLookupError, setEnrolleeLookupError] = useState("");

  // ── Member contact ──────────────────────────────
  const [memberPhone, setMemberPhone] = useState("");
  const [altPhone, setAltPhone] = useState("");
  const [memberEmail, setMemberEmail] = useState("");

  // ── Form ────────────────────────────────────────
  const [diagnosis, setDiagnosis] = useState("");
  const [diagnosisList, setDiagnosisList] = useState([]);
  const [diagnosisSearch, setDiagnosisSearch] = useState("");
  const [treatingDoctor, setTreatingDoctor] = useState("");
  const [providerNotes, setProviderNotes] = useState("");
  const [deliveryState, setDeliveryState] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [addressSearch, setAddressSearch] = useState("");
  const [addressSuggestions, setAddressSuggestions] = useState([]);
  const [addressValidation, setAddressValidation] = useState(null);
  const [pharmacies, setPharmacies] = useState([]);
  const [selectedPharmacy, setSelectedPharmacy] = useState(null);
  const [pharmacyLoading, setPharmacyLoading] = useState(false);
  const addressTimeout = useRef(null);
  const [urgency, setUrgency] = useState("routine");
  const [medications, setMedications] = useState([{ ...EMPTY_MED }]);

  // ── Location ────────────────────────────────────
  const [states, setStates] = useState([]);
  const [stateSearch, setStateSearch] = useState("");

  // ── Drug search ─────────────────────────────────
  const [activeSearch, setActiveSearch] = useState(null);
  const [drugResults, setDrugResults] = useState([]);
  const searchTimeout = useRef(null);

  // ── Submit ──────────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);
  const [tracking, setTracking] = useState(null);

  useEffect(() => {
    getStates().then(({ data }) => setStates(data.states)).catch(() => {});
    getDiagnoses().then(({ data }) => {
      console.log("Diagnoses loaded:", data);
      const list = data.diagnoses || data.result || data.data || data || [];
      setDiagnosisList(Array.isArray(list) ? list : []);
    }).catch((e) => console.error("Diagnosis load failed:", e));
  }, []);

  // ── Enrollee Lookup ─────────────────────────────
  const handleEnrolleeLookup = async () => {
    if (!enrolleeId.trim()) return;
    setEnrolleeLookupLoading(true);
    setEnrolleeLookupError("");
    setEnrolleeData(null);
    try {
      const { data } = await lookupEnrollee(enrolleeId.trim());
      if (data.found) {
        // Block inactive members
        if (data.is_active === false) {
          setEnrolleeLookupError(`Member status is "${data.status_description || data.status}". Only active members can request medications.`);
          return;
        }
        setEnrolleeData(data);
        // Auto-populate phone and email
        if (data.phone) setMemberPhone(data.phone);
        if (data.email) setMemberEmail(data.email);
      } else {
        setEnrolleeLookupError("Enrollee not found");
      }
    } catch (err) {
      setEnrolleeLookupError(err.response?.data?.detail || "Lookup failed");
    } finally {
      setEnrolleeLookupLoading(false);
    }
  };

  const clearEnrollee = () => { setEnrolleeData(null); setEnrolleeId(""); setEnrolleeLookupError(""); };

  // ── Drug search (local DB — synced from WellaHealth tariff) ──
  const handleDrugSearch = (index, value) => {
    const updated = [...medications];
    updated[index] = { ...updated[index], drug_name: value, matched_drug_id: null, generic_name: "", strength: "", dosage_form: "" };
    setMedications(updated);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (value.length < 3) { setDrugResults([]); setActiveSearch(null); return; }
    setActiveSearch(index);
    searchTimeout.current = setTimeout(() => {
      searchMedications(value)
        .then(({ data }) => {
          console.log("Drug search results:", data);
          setDrugResults(data.results || []);
        })
        .catch(() => setDrugResults([]));
    }, 300);
  };

  const selectDrug = (index, drug) => {
    const updated = [...medications];
    updated[index] = {
      ...updated[index],
      drug_name: drug.drug_name || drug.generic_name,
      generic_name: drug.generic_name || "",
      matched_drug_id: drug.drug_id || null,
      strength: drug.strength || "",
      dosage_form: drug.dosage_form || "",
    };
    setMedications(updated);
    setActiveSearch(null);
    setDrugResults([]);
  };

  // ── Address autocomplete (like Uber) ─────────────
  const handleAddressInput = (value) => {
    setAddressSearch(value);
    setDeliveryAddress("");
    setAddressValidation(null);
    setPharmacies([]);
    setSelectedPharmacy(null);
    if (addressTimeout.current) clearTimeout(addressTimeout.current);
    if (value.length < 3) { setAddressSuggestions([]); return; }
    addressTimeout.current = setTimeout(() => {
      addressAutocomplete(value)
        .then(({ data }) => setAddressSuggestions(data.predictions || []))
        .catch(() => setAddressSuggestions([]));
    }, 300);
  };

  const selectAddress = async (prediction) => {
    setAddressSearch(prediction.description);
    setDeliveryAddress(prediction.description);
    setAddressSuggestions([]);
    // Get full details from Google
    try {
      const { data } = await getAddressDetails(prediction.place_id);
      setAddressValidation(data);
      if (data.state && !deliveryState) setDeliveryState(data.state);
      // Auto-search pharmacies
      setPharmacyLoading(true);
      const state = data.state || deliveryState;
      const lga = data.lga || "";
      try {
        const { data: pharmData } = await searchPharmacies(state, lga, "");
        setPharmacies(pharmData.pharmacies || []);
        if (pharmData.pharmacies?.length === 1) setSelectedPharmacy(pharmData.pharmacies[0]);
      } catch { setPharmacies([]); }
      setPharmacyLoading(false);
    } catch { /* ignore */ }
  };

  const addMedLine = () => setMedications([...medications, { ...EMPTY_MED }]);
  const removeMedLine = (i) => { if (medications.length > 1) setMedications(medications.filter((_, idx) => idx !== i)); };
  const updateMed = (i, field, value) => { const u = [...medications]; u[i] = { ...u[i], [field]: value }; setMedications(u); };

  const getDiagName = (d) => {
    if (typeof d === "string") return d;
    return d.name || d.Name || d.description || d.Description ||
           d.DiagnosisName || d.diagnosisName || d.diagnosis ||
           d.DiagnosisDescription || d.Value || d.value ||
           d.Text || d.text || d.Label || d.label ||
           JSON.stringify(d);
  };

  const filteredDiagnoses = diagnosisSearch.length >= 2
    ? diagnosisList.filter(d => getDiagName(d).toLowerCase().includes(diagnosisSearch.toLowerCase())).slice(0, 15)
    : [];

  // ── Submit ──────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!enrolleeData) return setError("Please look up and confirm the enrollee first");
    if (!memberPhone.trim()) return setError("Member phone number is required");
    if (!diagnosis.trim()) return setError("Diagnosis is required");
    if (!deliveryState) return setError("Delivery state is required");
    if (!deliveryAddress.trim()) return setError("Delivery address is required");
    for (let i = 0; i < medications.length; i++) {
      const m = medications[i];
      if (!m.drug_name.trim()) return setError(`Medication ${i + 1}: drug name is required`);
      if (!m.dose) return setError(`Medication ${i + 1}: dose is required`);
      if (!m.frequency) return setError(`Medication ${i + 1}: frequency is required`);
      if (!m.duration) return setError(`Medication ${i + 1}: duration is required`);
    }

    setSubmitting(true);
    try {
      const pharmCode = selectedPharmacy?.pharmacyCode || selectedPharmacy?.PharmacyCode || selectedPharmacy?.code || "";
      const verifiedAddr = addressValidation?.formatted_address || deliveryAddress.trim();
      const resolvedLga = addressValidation?.lga || "";

      const { data } = await createMedicationRequest({
        enrollee_id: enrolleeId.trim(),
        enrollee_name: enrolleeData.name,
        enrollee_gender: enrolleeData.gender || null,
        diagnosis: diagnosis.trim(),
        treating_doctor: treatingDoctor.trim() || "Not specified",
        provider_notes: providerNotes || null,
        delivery_state: deliveryState,
        delivery_lga: resolvedLga || null,
        delivery_address: verifiedAddr,
        urgency,
        facility_name: provider?.provider_name || "Unknown Facility",
        facility_branch: null,
        member_phone: memberPhone.trim(),
        member_email: memberEmail.trim() || null,
        pharmacy_code: pharmCode || null,
        medications: medications.map(m => ({
          drug_name: m.drug_name.trim(),
          generic_name: m.generic_name || null,
          matched_drug_id: m.matched_drug_id || null,
          strength: m.strength.trim(),
          dosage_instruction: m.dose.trim(),
          duration: m.duration.trim(),
          quantity: "as prescribed",
          route: m.frequency || null,
        })),
      });
      setSuccess(data);
      // Fetch tracking info
      try {
        const { data: trk } = await getRequestTracking(data.request_id);
        setTracking(trk);
      } catch { /* ignore */ }
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit request.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setSuccess(null); setTracking(null); setEnrolleeId(""); setEnrolleeData(null);
    setMemberPhone(""); setAltPhone(""); setMemberEmail("");
    setDiagnosis(""); setDiagnosisSearch(""); setTreatingDoctor("");
    setProviderNotes(""); setDeliveryState(""); setStateSearch(""); setDeliveryAddress(""); setAddressSearch("");
    setAddressSuggestions([]); setAddressValidation(null); setPharmacies([]); setSelectedPharmacy(null);
    setUrgency("routine"); setMedications([{ ...EMPTY_MED }]); setError("");
  };

  const categoryBadge = (cat) => ({ acute: styles.badgeAcute, chronic: styles.badgeChronic, either: styles.badgeEither }[cat] || styles.badgeUnknown);
  const classificationLabel = (cls) => ({ acute: "Acute", chronic: "Chronic", mixed: "Mixed (Acute + Chronic)", review_required: "Review Required" }[cls] || cls);
  const classificationBadgeClass = (cls) => ({ acute: styles.badgeAcute, chronic: styles.badgeChronic, mixed: styles.badgeMixed, review_required: styles.badgeReview }[cls] || styles.badgeUnknown);
  const routeLabel = (dest) => ({ wellahealth: "WellaHealth API", whatsapp_lagos: "Leadway WhatsApp (Lagos)", whatsapp_outside_lagos: "Leadway WhatsApp (Outside Lagos)", manual_review: "Manual Review" }[dest] || dest);

  // ── Success ─────────────────────────────────────
  if (success) {
    const cls = success.classification;
    return (
      <div className={styles.page}>
        <Header provider={provider} logout={logout} />
        <NavBar active="new-request" />
        <main className={styles.main}>
          <div className={styles.successBanner}>
            <div className={styles.successTitle}>Request Submitted Successfully</div>
            <div className={styles.successRef}>Reference: <span className={styles.successRefCode}>{success.reference_number}</span></div>
          </div>
          {cls && (
            <div className={styles.classificationCard}>
              <h3 className={styles.classificationCardTitle}>Classification Result</h3>
              <div className={styles.classificationGrid}>
                <div className={styles.classificationMainResult}>
                  <span className={styles.classificationLabel}>Request Type</span>
                  <span className={`${styles.classificationBadgeLg} ${classificationBadgeClass(cls.classification)}`}>{classificationLabel(cls.classification)}</span>
                </div>
                <div className={styles.classificationCounts}>
                  {[["acute_count", "Acute"], ["chronic_count", "Chronic"], ["unknown_count", "Unknown"]].map(([k, l]) => (
                    <div key={k} className={styles.countItem}><span className={styles.countNumber}>{cls[k]}</span><span className={styles.countLabel}>{l}</span></div>
                  ))}
                  <div className={styles.countItem}><span className={styles.countNumber}>{cls.confidence != null ? `${Math.round(cls.confidence * 100)}%` : "—"}</span><span className={styles.countLabel}>Confidence</span></div>
                </div>
              </div>
              {cls.reasoning && <div className={styles.classificationReasoning}>{cls.reasoning}</div>}
            </div>
          )}
          {success.routing && (
            <div className={styles.routingCard}>
              <h3 className={styles.classificationCardTitle}>Routing Decision</h3>
              <div className={styles.routingDestination}>
                <span className={styles.routingLabel}>Destination</span>
                <span className={styles.routingBadge}>{routeLabel(success.routing.destination)}</span>
              </div>
              {success.routing.reasoning && <div className={styles.classificationReasoning}>{success.routing.reasoning}</div>}
            </div>
          )}

          {/* Tracking Info */}
          {tracking && (tracking.wellahealth || tracking.whatsapp) && (
            <div className={styles.classificationCard}>
              <h3 className={styles.classificationCardTitle}>Dispatch & Tracking</h3>
              {tracking.wellahealth && (
                <div>
                  <div className={styles.enrolleeDetails}>
                    <span className={styles.enrolleeDetail}><strong>Channel:</strong> WellaHealth</span>
                    <span className={styles.enrolleeDetail}><strong>Dispatched:</strong> {tracking.wellahealth.dispatched ? "Yes" : "Failed"}</span>
                    {tracking.wellahealth.pharmacy_code && <span className={styles.enrolleeDetail}><strong>Pharmacy:</strong> {tracking.wellahealth.pharmacy_code}</span>}
                    {tracking.wellahealth.tracking_code && <span className={styles.enrolleeDetail}><strong>Tracking Code:</strong> {tracking.wellahealth.tracking_code}</span>}
                    {tracking.wellahealth.dispatched_at && <span className={styles.enrolleeDetail}><strong>Time:</strong> {new Date(tracking.wellahealth.dispatched_at).toLocaleString()}</span>}
                  </div>
                  {tracking.wellahealth.tracking_link && (
                    <a href={tracking.wellahealth.tracking_link} target="_blank" rel="noreferrer" className={styles.trackingLink}>Track Order</a>
                  )}
                </div>
              )}
              {tracking.whatsapp && (
                <div>
                  <div className={styles.enrolleeDetails}>
                    <span className={styles.enrolleeDetail}><strong>Channel:</strong> WhatsApp</span>
                    <span className={styles.enrolleeDetail}><strong>Dispatched:</strong> {tracking.whatsapp.dispatched ? "Yes" : "Failed"}</span>
                    <span className={styles.enrolleeDetail}><strong>To:</strong> {tracking.whatsapp.destination_number}</span>
                    {tracking.whatsapp.dispatched_at && <span className={styles.enrolleeDetail}><strong>Time:</strong> {new Date(tracking.whatsapp.dispatched_at).toLocaleString()}</span>}
                    {tracking.whatsapp.error && <span className={styles.enrolleeDetail} style={{color: "#C61531"}}><strong>Error:</strong> {tracking.whatsapp.error}</span>}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className={styles.submitArea}>
            <button onClick={resetForm} className={styles.submitBtn}>New Request</button>
            <button onClick={() => navigate("/medication-requests")} className={styles.cancelBtn}>View All Requests</button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Header provider={provider} logout={logout} />
      <NavBar active="new-request" />
      <main className={styles.main}>
        <h1 className={styles.pageTitle}>New Medication Request</h1>
        <p className={styles.pageSubtitle}>Submit a prescription for an enrolled member.</p>
        {error && <div className={styles.errorBanner}>{error}</div>}

        <form onSubmit={handleSubmit}>
          {/* ── 1. Enrollee ─────────────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}><span className={styles.sectionTitleIcon}>1.</span> Enrollee Information</h2>
            {!enrolleeData ? (
              <div className={styles.field}>
                <label className={styles.label}>Enrollee ID <span className={styles.required}>*</span></label>
                <div className={styles.lookupRow}>
                  <input className={styles.input} value={enrolleeId} onChange={(e) => setEnrolleeId(e.target.value)}
                    placeholder="Enter Enrollee ID" onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleEnrolleeLookup())} />
                  <button type="button" className={styles.lookupBtn} onClick={handleEnrolleeLookup}
                    disabled={enrolleeLookupLoading || !enrolleeId.trim()}>
                    {enrolleeLookupLoading ? "Searching..." : "Look Up"}
                  </button>
                </div>
                {enrolleeLookupError && <div className={styles.fieldError}>{enrolleeLookupError}</div>}
              </div>
            ) : (
              <div className={styles.enrolleeConfirmed}>
                <div className={styles.enrolleeInfo}>
                  <div className={styles.enrolleeNameBig}>{enrolleeData.name}</div>
                  <div className={styles.enrolleeDetails}>
                    <span className={styles.enrolleeDetail}><strong>ID:</strong> {enrolleeId}</span>
                    {enrolleeData.gender && <span className={styles.enrolleeDetail}><strong>Gender:</strong> {enrolleeData.gender}</span>}
                    {enrolleeData.age && <span className={styles.enrolleeDetail}><strong>Age:</strong> {enrolleeData.age}</span>}
                    {enrolleeData.plan && <span className={styles.enrolleeDetail}><strong>Scheme:</strong> {enrolleeData.plan}</span>}
                    {enrolleeData.company && <span className={styles.enrolleeDetail}><strong>Company:</strong> {enrolleeData.company}</span>}
                    <span className={styles.enrolleeDetail}>
                      <strong>Status:</strong>{" "}
                      <span className={enrolleeData.is_active ? styles.statusActive : styles.statusInactive}>
                        {enrolleeData.status_description || enrolleeData.status || "Unknown"}
                      </span>
                    </span>
                  </div>
                </div>
                <button type="button" className={styles.changeBtn} onClick={clearEnrollee}>Change</button>
              </div>
            )}
            <div className={styles.formRowThree}>
              <div className={styles.field}>
                <label className={styles.label}>Member Phone <span className={styles.required}>*</span></label>
                <input className={styles.input} value={memberPhone} onChange={(e) => setMemberPhone(e.target.value)} placeholder="e.g. 08012345678" />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Alternative Phone</label>
                <input className={styles.input} value={altPhone} onChange={(e) => setAltPhone(e.target.value)} placeholder="Optional" />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Member Email</label>
                <input className={styles.input} type="email" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} placeholder="Optional" />
              </div>
            </div>
            <div className={styles.facilityAuto}>
              <span className={styles.label}>Facility</span>
              <span className={styles.facilityValue}>{provider?.provider_name || "—"}</span>
            </div>
          </div>

          {/* ── 2. Clinical ─────────────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}><span className={styles.sectionTitleIcon}>2.</span> Clinical Information</h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>Diagnosis <span className={styles.required}>*</span></label>
                <div className={styles.autocompleteWrap}>
                  <input className={styles.input} value={diagnosis || diagnosisSearch}
                    onChange={(e) => { setDiagnosisSearch(e.target.value); setDiagnosis(""); }}
                    placeholder="Type to search diagnoses..." />
                  {!diagnosis && filteredDiagnoses.length > 0 && (
                    <div className={styles.autocompleteDropdown}>
                      {filteredDiagnoses.map((d, i) => (
                        <div key={i} className={styles.autocompleteItem} onMouseDown={() => { setDiagnosis(getDiagName(d)); setDiagnosisSearch(""); }}>
                          <span className={styles.autocompleteName}>{getDiagName(d)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {diagnosis && <div className={styles.selectedTag}>{diagnosis} <span onClick={() => setDiagnosis("")} className={styles.tagRemove}>&times;</span></div>}
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Treating Doctor (optional)</label>
                <input className={styles.input} value={treatingDoctor} onChange={(e) => setTreatingDoctor(e.target.value)} placeholder="Dr. name" />
              </div>
            </div>
          </div>

          {/* ── 3. Medications ──────────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}><span className={styles.sectionTitleIcon}>3.</span> Medications</h2>
            {medications.map((med, idx) => (
              <div className={styles.medLine} key={idx}>
                <div className={styles.medLineHeader}>
                  <span className={styles.medLineNumber}>Medication {idx + 1}</span>
                  {medications.length > 1 && <button type="button" className={styles.removeMedBtn} onClick={() => removeMedLine(idx)}>&times;</button>}
                </div>
                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>Drug Name <span className={styles.required}>*</span></label>
                    <div className={styles.autocompleteWrap}>
                      <input className={styles.input} value={med.drug_name}
                        onChange={(e) => handleDrugSearch(idx, e.target.value)}
                        onFocus={() => med.drug_name.length >= 3 && setActiveSearch(idx)}
                        onBlur={() => setTimeout(() => setActiveSearch(null), 200)}
                        placeholder="Type to search medications..." />
                      {activeSearch === idx && drugResults.length > 0 && (
                        <div className={styles.autocompleteDropdown}>
                          {drugResults.map((drug, i) => (
                            <div key={i} className={styles.autocompleteItem} onMouseDown={() => selectDrug(idx, drug)}>
                              <div className={styles.autocompleteName}>{drug.drug_name || drug.generic_name}</div>
                              <div className={styles.autocompleteMeta}>
                                {drug.strength && <span className={styles.strengthTag}>{drug.strength}</span>}
                                {drug.dosage_form && <span>{drug.dosage_form}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Strength</label>
                    <input className={styles.input} value={med.strength}
                      onChange={(e) => updateMed(idx, "strength", e.target.value)}
                      placeholder="Auto-filled when you select a drug"
                      style={med.strength ? {background: "#f0f8f0", fontWeight: 600} : {}} />
                  </div>
                </div>
                <div className={styles.formRowThree}>
                  <div className={styles.field}>
                    <label className={styles.label}>Dose <span className={styles.required}>*</span></label>
                    <select className={styles.select} value={med.dose} onChange={(e) => updateMed(idx, "dose", e.target.value)}>
                      <option value="">Select dose</option>
                      <option value="1 tablet">1 Tablet</option>
                      <option value="2 tablets">2 Tablets</option>
                      <option value="1 capsule">1 Capsule</option>
                      <option value="2 capsules">2 Capsules</option>
                      <option value="5ml">5ml (1 teaspoon)</option>
                      <option value="10ml">10ml (2 teaspoons)</option>
                      <option value="1 sachet">1 Sachet</option>
                      <option value="1 application">1 Application</option>
                      <option value="1 puff">1 Puff</option>
                      <option value="2 puffs">2 Puffs</option>
                      <option value="1 drop">1 Drop</option>
                      <option value="2 drops">2 Drops</option>
                    </select>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Frequency <span className={styles.required}>*</span></label>
                    <select className={styles.select} value={med.frequency} onChange={(e) => updateMed(idx, "frequency", e.target.value)}>
                      <option value="">Select</option>
                      <option value="od">Once daily</option>
                      <option value="bd">Twice daily</option>
                      <option value="tds">3 times daily</option>
                      <option value="qds">4 times daily</option>
                      <option value="stat">Single dose</option>
                      <option value="prn">As needed</option>
                      <option value="nocte">At night</option>
                    </select>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Duration <span className={styles.required}>*</span></label>
                    <select className={styles.select} value={med.duration} onChange={(e) => updateMed(idx, "duration", e.target.value)}>
                      <option value="">Select</option>
                      <option value="3 days">3 Days</option>
                      <option value="5 days">5 Days</option>
                      <option value="7 days">7 Days (1 week)</option>
                      <option value="10 days">10 Days</option>
                      <option value="14 days">14 Days (2 weeks)</option>
                      <option value="21 days">21 Days (3 weeks)</option>
                      <option value="30 days">30 Days (1 month)</option>
                      <option value="60 days">60 Days (2 months)</option>
                      <option value="90 days">90 Days (3 months)</option>
                      <option value="ongoing">Ongoing / Continuous</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
            <button type="button" className={styles.addMedBtn} onClick={addMedLine}>+ Add Another Medication</button>
          </div>

          {/* ── 4. Delivery ─────────────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}><span className={styles.sectionTitleIcon}>4.</span> Delivery Location</h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>State <span className={styles.required}>*</span></label>
                <div className={styles.autocompleteWrap}>
                  <input className={styles.input} value={deliveryState || stateSearch}
                    onChange={(e) => { setStateSearch(e.target.value); setDeliveryState(""); }}
                    placeholder="Type state name..." />
                  {!deliveryState && stateSearch.length >= 1 && (
                    <div className={styles.autocompleteDropdown}>
                      {states
                        .filter(s => s.name.toLowerCase().includes(stateSearch.toLowerCase()))
                        .map((s) => (
                          <div key={s.name} className={styles.autocompleteItem}
                            onMouseDown={() => { setDeliveryState(s.name); setStateSearch(""); }}>
                            <span className={styles.autocompleteName}>{s.name}</span>
                          </div>
                        ))
                      }
                    </div>
                  )}
                </div>
              </div>
              <div />
            </div>
            <div className={styles.formRowFull}>
              <div className={styles.field}>
                <label className={styles.label}>Delivery Address <span className={styles.required}>*</span></label>
                <div className={styles.autocompleteWrap}>
                  <input className={styles.input} value={deliveryAddress || addressSearch}
                    onChange={(e) => handleAddressInput(e.target.value)}
                    placeholder="Start typing address..."
                  />
                  {addressSuggestions.length > 0 && (
                    <div className={styles.autocompleteDropdown}>
                      {addressSuggestions.map((p, i) => (
                        <div key={i} className={styles.autocompleteItem} onMouseDown={() => selectAddress(p)}>
                          <span className={styles.autocompleteName}>{p.description}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {addressValidation && addressValidation.formatted_address && (
                  <div className={styles.addressValid}>
                    <strong>Verified:</strong> {addressValidation.formatted_address}
                    {addressValidation.state && <> &middot; {addressValidation.state}</>}
                    {addressValidation.is_lagos !== null && <> &middot; {addressValidation.is_lagos ? "Lagos" : "Outside Lagos"}</>}
                  </div>
                )}
              </div>
            </div>

            {/* Pharmacy Selection */}
            {pharmacyLoading && <div className={styles.enrolleeMeta}>Searching pharmacies...</div>}
            {pharmacies.length > 0 && (
              <div className={styles.formRowFull}>
                <div className={styles.field}>
                  <label className={styles.label}>Nearest Pharmacy</label>
                  <div className={styles.pharmacyList}>
                    {pharmacies.slice(0, 5).map((p, i) => {
                      const code = p.pharmacyCode || p.PharmacyCode || p.code || "";
                      const name = p.pharmacyName || p.PharmacyName || p.name || `Pharmacy ${i + 1}`;
                      const addr = p.address || p.Address || "";
                      const isSelected = selectedPharmacy && (selectedPharmacy.pharmacyCode || selectedPharmacy.code) === code;
                      return (
                        <div key={i} className={`${styles.pharmacyItem} ${isSelected ? styles.pharmacySelected : ""}`}
                          onClick={() => setSelectedPharmacy(p)}>
                          <div className={styles.pharmacyName}>{name}</div>
                          {addr && <div className={styles.pharmacyAddr}>{addr}</div>}
                          <div className={styles.pharmacyCode}>Code: {code}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* ── 5. Additional ──────────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}><span className={styles.sectionTitleIcon}>5.</span> Additional Information</h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>Urgency</label>
                <select className={styles.select} value={urgency} onChange={(e) => setUrgency(e.target.value)}>
                  <option value="routine">Routine</option>
                  <option value="urgent">Urgent</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>
              <div />
            </div>
            <div className={styles.formRowFull}>
              <div className={styles.field}>
                <label className={styles.label}>Provider Notes</label>
                <textarea className={styles.textarea} value={providerNotes} onChange={(e) => setProviderNotes(e.target.value)} placeholder="Optional notes" rows={2} />
              </div>
            </div>
          </div>

          <div className={styles.submitArea}>
            <button type="button" className={styles.cancelBtn} onClick={() => navigate("/medication-requests")}>Cancel</button>
            <button type="submit" className={styles.submitBtn} disabled={submitting || !enrolleeData}>
              {submitting ? "Submitting..." : "Submit Request"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

function Header({ provider, logout }) {
  return (
    <header className={styles.header}>
      <div className={styles.headerLeft}>
        <Link to="/medication-request" className={styles.headerLogo}>
          <img src={logo} alt="Leadway Health" className={styles.headerLogoImg} />
        </Link>
        <span className={styles.headerDivider} />
        <span className={styles.headerPortal}>Rx Routing Hub</span>
      </div>
      <div className={styles.headerRight}>
        <span className={styles.providerName}>{provider?.provider_name}</span>
        <button onClick={logout} className={styles.logoutBtn}>Sign Out</button>
      </div>
    </header>
  );
}

function NavBar({ active }) {
  return (
    <nav className={styles.navBar}>
      <Link to="/medication-request" className={active === "new-request" ? styles.navLinkActive : styles.navLink}>New Rx Request</Link>
      <Link to="/medication-requests" className={active === "history" ? styles.navLinkActive : styles.navLink}>Request History</Link>
    </nav>
  );
}
