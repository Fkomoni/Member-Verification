import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  lookupEnrollee,
  getDiagnoses,
  searchDrugTariff,
  searchDrugs,
  getStates,
  getLgas,
  createMedicationRequest,
} from "../services/api";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./MedicationRequestPage.module.css";

const EMPTY_MED = {
  drug_name: "",
  generic_name: "",
  matched_drug_id: null,
  strength: "",
  dosage_instruction: "",
  duration: "",
  quantity: "",
  route: "oral",
};

export default function MedicationRequestPage() {
  const { provider, logout } = useAuth();
  const navigate = useNavigate();

  // ── Enrollee state ──────────────────────────────
  const [enrolleeId, setEnrolleeId] = useState("");
  const [enrolleeData, setEnrolleeData] = useState(null); // from Prognosis lookup
  const [enrolleeLookupLoading, setEnrolleeLookupLoading] = useState(false);
  const [enrolleeLookupError, setEnrolleeLookupError] = useState("");

  // ── Form state ──────────────────────────────────
  const [diagnosis, setDiagnosis] = useState("");
  const [diagnosisList, setDiagnosisList] = useState([]);
  const [diagnosisSearch, setDiagnosisSearch] = useState("");
  const [treatingDoctor, setTreatingDoctor] = useState("");
  const [providerNotes, setProviderNotes] = useState("");
  const [deliveryState, setDeliveryState] = useState("");
  const [deliveryLga, setDeliveryLga] = useState("");
  const [deliveryCity, setDeliveryCity] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryLandmark, setDeliveryLandmark] = useState("");
  const [urgency, setUrgency] = useState("routine");
  const [medications, setMedications] = useState([{ ...EMPTY_MED }]);

  // ── Location data ───────────────────────────────
  const [states, setStates] = useState([]);
  const [lgas, setLgas] = useState([]);

  // ── Drug search (WellaHealth tariff) ────────────
  const [activeSearch, setActiveSearch] = useState(null);
  const [drugResults, setDrugResults] = useState([]);
  const searchTimeout = useRef(null);

  // ── Submit state ────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  // Load states + diagnoses on mount
  useEffect(() => {
    getStates().then(({ data }) => setStates(data.states)).catch(() => {});
    getDiagnoses().then(({ data }) => setDiagnosisList(data.diagnoses || [])).catch(() => {});
  }, []);

  // Load LGAs when state changes
  useEffect(() => {
    if (!deliveryState) { setLgas([]); return; }
    getLgas(deliveryState).then(({ data }) => setLgas(data.lgas)).catch(() => setLgas([]));
    setDeliveryLga("");
  }, [deliveryState]);

  // ── Enrollee Lookup ─────────────────────────────
  const handleEnrolleeLookup = async () => {
    if (!enrolleeId.trim()) return;
    setEnrolleeLookupLoading(true);
    setEnrolleeLookupError("");
    setEnrolleeData(null);
    try {
      const { data } = await lookupEnrollee(enrolleeId.trim());
      if (data.found) {
        setEnrolleeData(data);
      } else {
        setEnrolleeLookupError("Enrollee not found");
      }
    } catch (err) {
      setEnrolleeLookupError(err.response?.data?.detail || "Lookup failed");
    } finally {
      setEnrolleeLookupLoading(false);
    }
  };

  const confirmEnrollee = () => {
    // Enrollee is already set via enrolleeData — no action needed
    // This just serves as visual confirmation
  };

  const clearEnrollee = () => {
    setEnrolleeData(null);
    setEnrolleeId("");
    setEnrolleeLookupError("");
  };

  // ── Drug search (WellaHealth tariff + local drug master) ──
  const handleDrugSearch = useCallback((index, value) => {
    const updated = [...medications];
    updated[index] = { ...updated[index], drug_name: value, matched_drug_id: null, generic_name: "" };
    setMedications(updated);

    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (value.length < 2) { setDrugResults([]); setActiveSearch(null); return; }

    setActiveSearch(index);
    searchTimeout.current = setTimeout(async () => {
      try {
        // Search WellaHealth tariff first, then local drug master
        const [tariffRes, localRes] = await Promise.allSettled([
          searchDrugTariff(value),
          searchDrugs(value),
        ]);

        const results = [];
        // WellaHealth tariff drugs
        if (tariffRes.status === "fulfilled" && tariffRes.value.data.drugs) {
          tariffRes.value.data.drugs.slice(0, 10).forEach(d => {
            results.push({
              drug_id: d.id || null,
              name: d.name,
              price: d.price,
              source: "wellahealth",
            });
          });
        }
        // Local drug master (for classification info)
        if (localRes.status === "fulfilled" && localRes.value.data.results) {
          localRes.value.data.results.slice(0, 5).forEach(d => {
            // Avoid duplicates
            if (!results.some(r => r.name.toLowerCase() === d.generic_name.toLowerCase())) {
              results.push({
                drug_id: d.drug_id,
                name: d.generic_name,
                category: d.category,
                source: "drug_master",
              });
            }
          });
        }
        setDrugResults(results);
      } catch {
        setDrugResults([]);
      }
    }, 300);
  }, [medications]);

  const selectDrug = (index, drug) => {
    const updated = [...medications];
    updated[index] = {
      ...updated[index],
      drug_name: drug.name,
      generic_name: drug.name,
      matched_drug_id: drug.drug_id || null,
    };
    setMedications(updated);
    setActiveSearch(null);
    setDrugResults([]);
  };

  // ── Medication line management ──────────────────
  const addMedLine = () => setMedications([...medications, { ...EMPTY_MED }]);
  const removeMedLine = (index) => {
    if (medications.length <= 1) return;
    setMedications(medications.filter((_, i) => i !== index));
  };
  const updateMed = (index, field, value) => {
    const updated = [...medications];
    updated[index] = { ...updated[index], [field]: value };
    setMedications(updated);
  };

  // ── Diagnosis filter ────────────────────────────
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
    if (!diagnosis.trim()) return setError("Diagnosis is required");
    if (!deliveryState) return setError("Delivery state is required");
    if (!deliveryLga) return setError("Delivery LGA is required");

    for (let i = 0; i < medications.length; i++) {
      const m = medications[i];
      if (!m.drug_name.trim()) return setError(`Medication ${i + 1}: drug name is required`);
      if (!m.dosage_instruction.trim()) return setError(`Medication ${i + 1}: dosage is required`);
      if (!m.duration.trim()) return setError(`Medication ${i + 1}: duration is required`);
      if (!m.quantity.trim()) return setError(`Medication ${i + 1}: quantity is required`);
    }

    setSubmitting(true);
    try {
      const payload = {
        enrollee_id: enrolleeId.trim(),
        enrollee_name: enrolleeData.name,
        enrollee_gender: enrolleeData.gender || null,
        diagnosis: diagnosis.trim(),
        treating_doctor: treatingDoctor.trim() || "Not specified",
        provider_notes: providerNotes || null,
        delivery_state: deliveryState,
        delivery_lga: deliveryLga,
        delivery_city: deliveryCity || null,
        delivery_address: deliveryAddress || null,
        delivery_landmark: deliveryLandmark || null,
        urgency,
        facility_name: provider?.provider_name || "Unknown Facility",
        facility_branch: null,
        medications: medications.map((m) => ({
          drug_name: m.drug_name.trim(),
          generic_name: m.generic_name || null,
          matched_drug_id: m.matched_drug_id || null,
          strength: m.strength || null,
          dosage_instruction: m.dosage_instruction.trim(),
          duration: m.duration.trim(),
          quantity: m.quantity.trim(),
          route: m.route || null,
        })),
      };

      const { data } = await createMedicationRequest(payload);
      setSuccess(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit request.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setSuccess(null);
    setEnrolleeId("");
    setEnrolleeData(null);
    setDiagnosis("");
    setDiagnosisSearch("");
    setTreatingDoctor("");
    setProviderNotes("");
    setDeliveryState("");
    setDeliveryLga("");
    setDeliveryCity("");
    setDeliveryAddress("");
    setDeliveryLandmark("");
    setUrgency("routine");
    setMedications([{ ...EMPTY_MED }]);
    setError("");
  };

  const categoryBadge = (cat) => {
    const map = { acute: styles.badgeAcute, chronic: styles.badgeChronic, either: styles.badgeEither };
    return map[cat] || styles.badgeUnknown;
  };

  const classificationLabel = (cls) => {
    const labels = { acute: "Acute", chronic: "Chronic", mixed: "Mixed (Acute + Chronic)", review_required: "Review Required" };
    return labels[cls] || cls;
  };

  const classificationBadgeClass = (cls) => {
    const map = { acute: styles.badgeAcute, chronic: styles.badgeChronic, mixed: styles.badgeMixed, review_required: styles.badgeReview };
    return map[cls] || styles.badgeUnknown;
  };

  const routeLabel = (dest) => {
    const labels = { wellahealth: "WellaHealth API", whatsapp_lagos: "Leadway WhatsApp (Lagos)", whatsapp_outside_lagos: "Leadway WhatsApp (Outside Lagos)", manual_review: "Manual Review Queue" };
    return labels[dest] || dest;
  };

  // ── Success state ───────────────────────────────
  if (success) {
    const cls = success.classification;
    return (
      <div className={styles.page}>
        <Header provider={provider} logout={logout} />
        <NavBar active="new-request" />
        <main className={styles.main}>
          <div className={styles.successBanner}>
            <div className={styles.successTitle}>Request Submitted Successfully</div>
            <div className={styles.successRef}>
              Reference: <span className={styles.successRefCode}>{success.reference_number}</span>
            </div>
          </div>

          {cls && (
            <div className={styles.classificationCard}>
              <h3 className={styles.classificationCardTitle}>Classification Result</h3>
              <div className={styles.classificationGrid}>
                <div className={styles.classificationMainResult}>
                  <span className={styles.classificationLabel}>Request Type</span>
                  <span className={`${styles.classificationBadgeLg} ${classificationBadgeClass(cls.classification)}`}>
                    {classificationLabel(cls.classification)}
                  </span>
                </div>
                <div className={styles.classificationCounts}>
                  <div className={styles.countItem}>
                    <span className={styles.countNumber}>{cls.acute_count}</span>
                    <span className={styles.countLabel}>Acute</span>
                  </div>
                  <div className={styles.countItem}>
                    <span className={styles.countNumber}>{cls.chronic_count}</span>
                    <span className={styles.countLabel}>Chronic</span>
                  </div>
                  <div className={styles.countItem}>
                    <span className={styles.countNumber}>{cls.unknown_count}</span>
                    <span className={styles.countLabel}>Unknown</span>
                  </div>
                  <div className={styles.countItem}>
                    <span className={styles.countNumber}>{cls.confidence != null ? `${Math.round(cls.confidence * 100)}%` : "—"}</span>
                    <span className={styles.countLabel}>Confidence</span>
                  </div>
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
              <div className={styles.routingStatusRow}>
                <span className={styles.routingStatusLabel}>Status:</span>
                <span className={styles.routingStatusValue}>{success.status}</span>
              </div>
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
          {/* ── Section 1: Enrollee Lookup ──────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>1.</span> Enrollee Information
            </h2>

            {!enrolleeData ? (
              <>
                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>Enrollee ID (CIF) <span className={styles.required}>*</span></label>
                    <div className={styles.lookupRow}>
                      <input
                        className={styles.input}
                        value={enrolleeId}
                        onChange={(e) => setEnrolleeId(e.target.value)}
                        placeholder="Enter CIF number"
                        onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleEnrolleeLookup())}
                      />
                      <button
                        type="button"
                        className={styles.lookupBtn}
                        onClick={handleEnrolleeLookup}
                        disabled={enrolleeLookupLoading || !enrolleeId.trim()}
                      >
                        {enrolleeLookupLoading ? "Searching..." : "Look Up"}
                      </button>
                    </div>
                    {enrolleeLookupError && <div className={styles.fieldError}>{enrolleeLookupError}</div>}
                  </div>
                </div>
              </>
            ) : (
              <div className={styles.enrolleeConfirmed}>
                <div className={styles.enrolleeInfo}>
                  <div className={styles.enrolleeNameBig}>{enrolleeData.name}</div>
                  <div className={styles.enrolleeMeta}>
                    CIF: {enrolleeId}
                    {enrolleeData.gender && <> &middot; {enrolleeData.gender}</>}
                    {enrolleeData.plan && <> &middot; {enrolleeData.plan}</>}
                  </div>
                </div>
                <button type="button" className={styles.changeBtn} onClick={clearEnrollee}>Change</button>
              </div>
            )}

            <div className={styles.facilityAuto}>
              <span className={styles.label}>Facility</span>
              <span className={styles.facilityValue}>{provider?.provider_name || "—"}</span>
            </div>
          </div>

          {/* ── Section 2: Diagnosis ────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>2.</span> Clinical Information
            </h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>Diagnosis <span className={styles.required}>*</span></label>
                <div className={styles.autocompleteWrap}>
                  <input
                    className={styles.input}
                    value={diagnosis || diagnosisSearch}
                    onChange={(e) => {
                      setDiagnosisSearch(e.target.value);
                      setDiagnosis("");
                    }}
                    placeholder="Type to search diagnoses..."
                  />
                  {!diagnosis && filteredDiagnoses.length > 0 && (
                    <div className={styles.autocompleteDropdown}>
                      {filteredDiagnoses.map((d, i) => {
                        const name = typeof d === "string" ? d : d.name || d.Name || d.description || d.Description || JSON.stringify(d);
                        return (
                          <div key={i} className={styles.autocompleteItem} onMouseDown={() => { setDiagnosis(name); setDiagnosisSearch(""); }}>
                            <span className={styles.autocompleteName}>{name}</span>
                          </div>
                        );
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

          {/* ── Section 3: Medications (WellaHealth tariff) */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>3.</span> Medications
            </h2>

            {medications.map((med, idx) => (
              <div className={styles.medLine} key={idx}>
                <div className={styles.medLineHeader}>
                  <span className={styles.medLineNumber}>Medication {idx + 1}</span>
                  {medications.length > 1 && (
                    <button type="button" className={styles.removeMedBtn} onClick={() => removeMedLine(idx)}>&times;</button>
                  )}
                </div>

                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>Drug Name <span className={styles.required}>*</span></label>
                    <div className={styles.autocompleteWrap}>
                      <input
                        className={styles.input}
                        value={med.drug_name}
                        onChange={(e) => handleDrugSearch(idx, e.target.value)}
                        onFocus={() => med.drug_name.length >= 2 && setActiveSearch(idx)}
                        onBlur={() => setTimeout(() => setActiveSearch(null), 200)}
                        placeholder="Search WellaHealth drugs..."
                      />
                      {activeSearch === idx && drugResults.length > 0 && (
                        <div className={styles.autocompleteDropdown}>
                          {drugResults.map((drug, i) => (
                            <div key={i} className={styles.autocompleteItem} onMouseDown={() => selectDrug(idx, drug)}>
                              <span className={styles.autocompleteName}>{drug.name}</span>
                              {drug.price && <span className={styles.autocompleteMeta}>₦{Number(drug.price).toLocaleString()}</span>}
                              {drug.category && (
                                <span className={`${styles.categoryBadge} ${categoryBadge(drug.category)}`}>{drug.category}</span>
                              )}
                              <span className={styles.sourceTag}>{drug.source === "wellahealth" ? "WH" : "Local"}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Strength</label>
                    <input className={styles.input} value={med.strength} onChange={(e) => updateMed(idx, "strength", e.target.value)} placeholder="e.g. 500mg" />
                  </div>
                </div>

                <div className={styles.formRowThree}>
                  <div className={styles.field}>
                    <label className={styles.label}>Dosage <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.dosage_instruction} onChange={(e) => updateMed(idx, "dosage_instruction", e.target.value)} placeholder="e.g. 1 tab BD" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Duration <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.duration} onChange={(e) => updateMed(idx, "duration", e.target.value)} placeholder="e.g. 5 days" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Quantity <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.quantity} onChange={(e) => updateMed(idx, "quantity", e.target.value)} placeholder="e.g. 10 tabs" />
                  </div>
                </div>
              </div>
            ))}

            <button type="button" className={styles.addMedBtn} onClick={addMedLine}>+ Add Another Medication</button>
          </div>

          {/* ── Section 4: Delivery Location ────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>4.</span> Delivery Location
            </h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>State <span className={styles.required}>*</span></label>
                <select className={styles.select} value={deliveryState} onChange={(e) => setDeliveryState(e.target.value)}>
                  <option value="">Select State</option>
                  {states.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label}>LGA <span className={styles.required}>*</span></label>
                <select className={styles.select} value={deliveryLga} onChange={(e) => setDeliveryLga(e.target.value)} disabled={!deliveryState}>
                  <option value="">{lgas.length ? "Select LGA" : "Select state first"}</option>
                  {lgas.map((l) => <option key={l} value={l}>{l}</option>)}
                </select>
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>City</label>
                <input className={styles.input} value={deliveryCity} onChange={(e) => setDeliveryCity(e.target.value)} placeholder="Optional" />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Landmark</label>
                <input className={styles.input} value={deliveryLandmark} onChange={(e) => setDeliveryLandmark(e.target.value)} placeholder="Optional" />
              </div>
            </div>
            <div className={styles.formRowFull}>
              <div className={styles.field}>
                <label className={styles.label}>Delivery Address</label>
                <textarea className={styles.textarea} value={deliveryAddress} onChange={(e) => setDeliveryAddress(e.target.value)} placeholder="Full delivery address (optional)" rows={2} />
              </div>
            </div>
          </div>

          {/* ── Section 5: Urgency ──────────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>5.</span> Additional Information
            </h2>
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
                <textarea className={styles.textarea} value={providerNotes} onChange={(e) => setProviderNotes(e.target.value)} placeholder="Optional notes for the fulfilment team" rows={2} />
              </div>
            </div>
          </div>

          {/* ── Submit ─────────────────────────── */}
          <div className={styles.submitArea}>
            <button type="button" className={styles.cancelBtn} onClick={() => navigate("/dashboard")}>Cancel</button>
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
        <Link to="/dashboard" className={styles.headerLogo}>
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
      <Link to="/dashboard" className={active === "verification" ? styles.navLinkActive : styles.navLink}>Verification</Link>
      <Link to="/medication-request" className={active === "new-request" ? styles.navLinkActive : styles.navLink}>New Rx Request</Link>
      <Link to="/medication-requests" className={active === "history" ? styles.navLinkActive : styles.navLink}>Request History</Link>
    </nav>
  );
}
