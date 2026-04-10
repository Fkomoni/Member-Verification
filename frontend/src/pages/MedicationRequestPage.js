import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  lookupEnrollee,
  getDiagnoses,
  searchMedications,
  getStates,
  createMedicationRequest,
  validateAddress,
  searchPharmacies,
} from "../services/api";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./MedicationRequestPage.module.css";

const EMPTY_MED = {
  drug_name: "", generic_name: "", matched_drug_id: null,
  strength: "", dosage_form: "", dosage_instruction: "", duration: "",
  quantity: "", frequency: "", med_notes: "",
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
  const [addressValidation, setAddressValidation] = useState(null);
  const [addressValidating, setAddressValidating] = useState(false);
  const [pharmacies, setPharmacies] = useState([]);
  const [selectedPharmacy, setSelectedPharmacy] = useState(null);
  const [pharmacyLoading, setPharmacyLoading] = useState(false);
  const [urgency, setUrgency] = useState("routine");
  const [medications, setMedications] = useState([{ ...EMPTY_MED }]);

  // ── Location ────────────────────────────────────
  const [states, setStates] = useState([]);

  // ── Drug search ─────────────────────────────────
  const [activeSearch, setActiveSearch] = useState(null);
  const [drugResults, setDrugResults] = useState([]);
  const searchTimeout = useRef(null);

  // ── Submit ──────────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    getStates().then(({ data }) => setStates(data.states)).catch(() => {});
    getDiagnoses().then(({ data }) => setDiagnosisList(data.diagnoses || [])).catch(() => {});
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
  const handleDrugSearch = useCallback((index, value) => {
    const updated = [...medications];
    updated[index] = { ...updated[index], drug_name: value, matched_drug_id: null, generic_name: "", strength: "", dosage_form: "" };
    setMedications(updated);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (value.length < 2) { setDrugResults([]); setActiveSearch(null); return; }
    setActiveSearch(index);
    searchTimeout.current = setTimeout(async () => {
      try {
        const { data } = await searchMedications(value);
        setDrugResults(data.results || []);
      } catch { setDrugResults([]); }
    }, 250);
  }, [medications]);

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

  // ── Address validation ───────────────────────────
  const handleValidateAddress = async () => {
    if (!deliveryAddress.trim()) return;
    setAddressValidating(true);
    setAddressValidation(null);
    setPharmacies([]);
    setSelectedPharmacy(null);
    try {
      const { data } = await validateAddress(deliveryAddress.trim(), deliveryState);
      setAddressValidation(data);
      if (data.validated) {
        if (data.state && !deliveryState) setDeliveryState(data.state);
        // Auto-search pharmacies near verified address
        setPharmacyLoading(true);
        try {
          const state = data.state || deliveryState;
          const lga = data.lga || "";
          const { data: pharmData } = await searchPharmacies(state, lga, "");
          setPharmacies(pharmData.pharmacies || []);
          // Auto-select first pharmacy if only one
          if (pharmData.pharmacies?.length === 1) {
            setSelectedPharmacy(pharmData.pharmacies[0]);
          }
        } catch { setPharmacies([]); }
        setPharmacyLoading(false);
      }
    } catch { setAddressValidation({ validated: false, reason: "Validation failed" }); }
    setAddressValidating(false);
  };

  const addMedLine = () => setMedications([...medications, { ...EMPTY_MED }]);
  const removeMedLine = (i) => { if (medications.length > 1) setMedications(medications.filter((_, idx) => idx !== i)); };
  const updateMed = (i, field, value) => { const u = [...medications]; u[i] = { ...u[i], [field]: value }; setMedications(u); };

  const filteredDiagnoses = diagnosisSearch.length >= 2
    ? diagnosisList.filter(d => {
        const name = typeof d === "string" ? d : d.name || d.Name || d.description || "";
        return name.toLowerCase().includes(diagnosisSearch.toLowerCase());
      }).slice(0, 15)
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
      if (!m.dosage_instruction.trim()) return setError(`Medication ${i + 1}: dosage is required`);
      if (!m.duration.trim()) return setError(`Medication ${i + 1}: duration is required`);
      if (!m.quantity.trim()) return setError(`Medication ${i + 1}: quantity is required`);
    }

    setSubmitting(true);
    try {
      const { data } = await createMedicationRequest({
        enrollee_id: enrolleeId.trim(),
        enrollee_name: enrolleeData.name,
        enrollee_gender: enrolleeData.gender || null,
        diagnosis: diagnosis.trim(),
        treating_doctor: treatingDoctor.trim() || "Not specified",
        provider_notes: providerNotes || null,
        delivery_state: deliveryState,
        delivery_lga: deliveryState, // state used as LGA placeholder
        delivery_address: deliveryAddress.trim(),
        urgency,
        facility_name: provider?.provider_name || "Unknown Facility",
        facility_branch: null,
        member_phone: memberPhone.trim(),
        member_email: memberEmail.trim() || null,
        medications: medications.map(m => ({
          drug_name: m.drug_name.trim(), generic_name: m.generic_name || null,
          matched_drug_id: m.matched_drug_id || null, strength: m.strength || null,
          dosage_instruction: m.dosage_instruction.trim(), duration: m.duration.trim(),
          quantity: m.quantity.trim(), route: m.route || null,
        })),
      });
      setSuccess(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit request.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setSuccess(null); setEnrolleeId(""); setEnrolleeData(null);
    setMemberPhone(""); setAltPhone(""); setMemberEmail("");
    setDiagnosis(""); setDiagnosisSearch(""); setTreatingDoctor("");
    setProviderNotes(""); setDeliveryState(""); setDeliveryAddress("");
    setAddressValidation(null); setPharmacies([]); setSelectedPharmacy(null);
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
                      {filteredDiagnoses.map((d, i) => {
                        const name = typeof d === "string" ? d : d.name || d.Name || d.description || JSON.stringify(d);
                        return <div key={i} className={styles.autocompleteItem} onMouseDown={() => { setDiagnosis(name); setDiagnosisSearch(""); }}>
                          <span className={styles.autocompleteName}>{name}</span>
                        </div>;
                      })}
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
                <div className={styles.formRowFull}>
                  <div className={styles.field}>
                    <label className={styles.label}>Drug Name <span className={styles.required}>*</span></label>
                    <div className={styles.autocompleteWrap}>
                      <input className={styles.input} value={med.drug_name}
                        onChange={(e) => handleDrugSearch(idx, e.target.value)}
                        onFocus={() => med.drug_name.length >= 2 && setActiveSearch(idx)}
                        onBlur={() => setTimeout(() => setActiveSearch(null), 200)}
                        placeholder="Type to search medications..." />
                      {activeSearch === idx && drugResults.length > 0 && (
                        <div className={styles.autocompleteDropdown}>
                          {drugResults.map((drug, i) => (
                            <div key={i} className={styles.autocompleteItem} onMouseDown={() => selectDrug(idx, drug)}>
                              <span className={styles.autocompleteName}>{drug.drug_name || drug.generic_name}</span>
                              {drug.strength && <span className={styles.autocompleteMeta}>{drug.strength}</span>}
                              {drug.dosage_form && <span className={styles.autocompleteMeta}>{drug.dosage_form}</span>}
                              {drug.brand_name && <span className={styles.autocompleteMeta}>({drug.brand_name})</span>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    {med.generic_name && med.generic_name !== med.drug_name && (
                      <div className={styles.selectedDrugInfo}>Generic: {med.generic_name}{med.strength && ` | ${med.strength}`}{med.dosage_form && ` | ${med.dosage_form}`}</div>
                    )}
                  </div>
                </div>
                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>Dosage <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.dosage_instruction} onChange={(e) => updateMed(idx, "dosage_instruction", e.target.value)} placeholder="e.g. 1 tab twice daily" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Frequency <span className={styles.required}>*</span></label>
                    <select className={styles.select} value={med.frequency} onChange={(e) => updateMed(idx, "frequency", e.target.value)}>
                      <option value="">Select</option>
                      <option value="OD">Once daily (OD)</option>
                      <option value="BD">Twice daily (BD)</option>
                      <option value="TDS">Three times daily (TDS)</option>
                      <option value="QDS">Four times daily (QDS)</option>
                      <option value="STAT">Single dose (STAT)</option>
                      <option value="PRN">As needed (PRN)</option>
                      <option value="Nocte">At night (Nocte)</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                </div>
                <div className={styles.formRowThree}>
                  <div className={styles.field}>
                    <label className={styles.label}>Duration <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.duration} onChange={(e) => updateMed(idx, "duration", e.target.value)} placeholder="e.g. 5 days" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Quantity <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.quantity} onChange={(e) => updateMed(idx, "quantity", e.target.value)} placeholder="e.g. 10 tablets" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Notes</label>
                    <input className={styles.input} value={med.med_notes} onChange={(e) => updateMed(idx, "med_notes", e.target.value)} placeholder="Optional" />
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
                <select className={styles.select} value={deliveryState} onChange={(e) => setDeliveryState(e.target.value)}>
                  <option value="">Select State</option>
                  {states.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
                </select>
              </div>
              <div />
            </div>
            <div className={styles.formRowFull}>
              <div className={styles.field}>
                <label className={styles.label}>Delivery Address <span className={styles.required}>*</span></label>
                <div className={styles.lookupRow}>
                  <textarea className={styles.textarea} style={{flex: 1}} value={deliveryAddress} onChange={(e) => { setDeliveryAddress(e.target.value); setAddressValidation(null); }}
                    placeholder="Enter full delivery address" rows={2} />
                  <button type="button" className={styles.lookupBtn} onClick={handleValidateAddress}
                    disabled={addressValidating || !deliveryAddress.trim()} style={{alignSelf: "flex-start", marginTop: "2px"}}>
                    {addressValidating ? "Verifying..." : "Verify"}
                  </button>
                </div>
                {addressValidation && addressValidation.validated && (
                  <div className={styles.addressValid}>
                    <strong>Verified:</strong> {addressValidation.formatted_address}
                    {addressValidation.state && <> &middot; State: {addressValidation.state}</>}
                    {addressValidation.is_lagos !== null && <> &middot; {addressValidation.is_lagos ? "Lagos" : "Outside Lagos"}</>}
                  </div>
                )}
                {addressValidation && !addressValidation.validated && (
                  <div className={styles.fieldError}>Address could not be verified: {addressValidation.reason}</div>
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
