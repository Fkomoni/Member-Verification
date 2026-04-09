import React, { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
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

  // ── Form state ──────────────────────────────────
  const [enrolleeId, setEnrolleeId] = useState("");
  const [enrolleeName, setEnrolleeName] = useState("");
  const [enrolleeGender, setEnrolleeGender] = useState("");
  const [diagnosis, setDiagnosis] = useState("");
  const [treatingDoctor, setTreatingDoctor] = useState("");
  const [doctorPhone, setDoctorPhone] = useState("");
  const [providerNotes, setProviderNotes] = useState("");
  const [deliveryState, setDeliveryState] = useState("");
  const [deliveryLga, setDeliveryLga] = useState("");
  const [deliveryCity, setDeliveryCity] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryLandmark, setDeliveryLandmark] = useState("");
  const [urgency, setUrgency] = useState("routine");
  const [facilityName, setFacilityName] = useState("");
  const [facilityBranch, setFacilityBranch] = useState("");
  const [medications, setMedications] = useState([{ ...EMPTY_MED }]);

  // ── Location data ───────────────────────────────
  const [states, setStates] = useState([]);
  const [lgas, setLgas] = useState([]);

  // ── Drug search ─────────────────────────────────
  const [activeSearch, setActiveSearch] = useState(null); // index of med line being searched
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const searchTimeout = useRef(null);

  // ── Submit state ────────────────────────────────
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(null);

  // Load states on mount
  useEffect(() => {
    getStates()
      .then(({ data }) => setStates(data.states))
      .catch(() => {});
  }, []);

  // Load LGAs when state changes
  useEffect(() => {
    if (!deliveryState) {
      setLgas([]);
      return;
    }
    getLgas(deliveryState)
      .then(({ data }) => setLgas(data.lgas))
      .catch(() => setLgas([]));
    setDeliveryLga("");
  }, [deliveryState]);

  // ── Drug search with debounce ───────────────────
  const handleDrugSearch = useCallback((index, value) => {
    const updated = [...medications];
    updated[index] = { ...updated[index], drug_name: value, matched_drug_id: null, generic_name: "" };
    setMedications(updated);

    if (searchTimeout.current) clearTimeout(searchTimeout.current);

    if (value.length < 2) {
      setSearchResults([]);
      setActiveSearch(null);
      return;
    }

    setActiveSearch(index);
    setSearchLoading(true);
    searchTimeout.current = setTimeout(async () => {
      try {
        const { data } = await searchDrugs(value);
        setSearchResults(data.results || []);
      } catch {
        setSearchResults([]);
      } finally {
        setSearchLoading(false);
      }
    }, 300);
  }, [medications]);

  const selectDrug = (index, drug) => {
    const updated = [...medications];
    updated[index] = {
      ...updated[index],
      drug_name: drug.generic_name,
      generic_name: drug.generic_name,
      matched_drug_id: drug.drug_id,
    };
    setMedications(updated);
    setActiveSearch(null);
    setSearchResults([]);
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

  // ── Submit ──────────────────────────────────────
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Basic validation
    if (!enrolleeId.trim()) return setError("Enrollee ID is required");
    if (!enrolleeName.trim()) return setError("Enrollee name is required");
    if (!diagnosis.trim()) return setError("Diagnosis is required");
    if (!treatingDoctor.trim()) return setError("Treating doctor is required");
    if (!deliveryState) return setError("Delivery state is required");
    if (!deliveryLga) return setError("Delivery LGA is required");
    if (!facilityName.trim()) return setError("Facility name is required");

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
        enrollee_name: enrolleeName.trim(),
        enrollee_gender: enrolleeGender || null,
        diagnosis: diagnosis.trim(),
        treating_doctor: treatingDoctor.trim(),
        doctor_phone: doctorPhone || null,
        provider_notes: providerNotes || null,
        delivery_state: deliveryState,
        delivery_lga: deliveryLga,
        delivery_city: deliveryCity || null,
        delivery_address: deliveryAddress || null,
        delivery_landmark: deliveryLandmark || null,
        urgency,
        facility_name: facilityName.trim(),
        facility_branch: facilityBranch || null,
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
      setError(err.response?.data?.detail || "Failed to submit request. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setSuccess(null);
    setEnrolleeId("");
    setEnrolleeName("");
    setEnrolleeGender("");
    setDiagnosis("");
    setTreatingDoctor("");
    setDoctorPhone("");
    setProviderNotes("");
    setDeliveryState("");
    setDeliveryLga("");
    setDeliveryCity("");
    setDeliveryAddress("");
    setDeliveryLandmark("");
    setUrgency("routine");
    setFacilityName("");
    setFacilityBranch("");
    setMedications([{ ...EMPTY_MED }]);
    setError("");
  };

  const categoryBadge = (cat) => {
    const map = {
      acute: styles.badgeAcute,
      chronic: styles.badgeChronic,
      either: styles.badgeEither,
    };
    return map[cat] || styles.badgeUnknown;
  };

  const classificationLabel = (cls) => {
    const labels = {
      acute: "Acute",
      chronic: "Chronic",
      mixed: "Mixed (Acute + Chronic)",
      review_required: "Review Required",
    };
    return labels[cls] || cls;
  };

  const classificationBadgeClass = (cls) => {
    const map = {
      acute: styles.badgeAcute,
      chronic: styles.badgeChronic,
      mixed: styles.badgeMixed,
      review_required: styles.badgeReview,
    };
    return map[cls] || styles.badgeUnknown;
  };

  const routeLabel = (dest) => {
    const labels = {
      wellahealth: "WellaHealth API",
      whatsapp_lagos: "Leadway WhatsApp (Lagos)",
      whatsapp_outside_lagos: "Leadway WhatsApp (Outside Lagos)",
      manual_review: "Manual Review Queue",
    };
    return labels[dest] || dest;
  };

  const routeIcon = (dest) => {
    if (dest === "wellahealth") return "arrow-right";
    if (dest?.startsWith("whatsapp")) return "whatsapp";
    return "flag";
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
              {cls.reasoning && (
                <div className={styles.classificationReasoning}>{cls.reasoning}</div>
              )}
              {cls.review_required && (
                <div className={styles.reviewFlag}>
                  One or more medications need manual review before routing.
                </div>
              )}
            </div>
          )}

          {/* Routing Decision */}
          {success.routing && (
            <div className={styles.routingCard}>
              <h3 className={styles.classificationCardTitle}>Routing Decision</h3>
              <div className={styles.routingDestination}>
                <span className={styles.routingLabel}>Destination</span>
                <span className={styles.routingBadge}>
                  {routeLabel(success.routing.destination)}
                </span>
              </div>
              {success.routing.reasoning && (
                <div className={styles.classificationReasoning}>
                  {success.routing.reasoning}
                </div>
              )}
              <div className={styles.routingStatusRow}>
                <span className={styles.routingStatusLabel}>Status:</span>
                <span className={styles.routingStatusValue}>{success.status}</span>
              </div>
            </div>
          )}

          {/* Per-item classification */}
          {success.items && success.items.length > 0 && (
            <div className={styles.classificationCard}>
              <h3 className={styles.classificationCardTitle}>Medication Breakdown</h3>
              <div className={styles.itemsList}>
                {success.items.map((item, idx) => (
                  <div key={item.item_id} className={styles.classifiedItem}>
                    <div className={styles.classifiedItemName}>
                      <span className={styles.classifiedItemIdx}>{idx + 1}.</span>
                      {item.drug_name}
                      {item.generic_name && item.generic_name !== item.drug_name && (
                        <span className={styles.classifiedItemGeneric}> ({item.generic_name})</span>
                      )}
                    </div>
                    <div className={styles.classifiedItemMeta}>
                      <span className={`${styles.categoryBadge} ${categoryBadge(item.item_category)}`}>
                        {item.item_category || "unclassified"}
                      </span>
                      {item.classification_confidence != null && (
                        <span className={styles.confidenceText}>
                          {Math.round(item.classification_confidence * 100)}% confidence
                        </span>
                      )}
                      {item.requires_review && (
                        <span className={styles.reviewBadge}>needs review</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className={styles.submitArea}>
            <button onClick={resetForm} className={styles.submitBtn}>
              New Request
            </button>
            <button
              onClick={() => navigate("/dashboard")}
              className={styles.cancelBtn}
            >
              Back to Dashboard
            </button>
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
        <p className={styles.pageSubtitle}>
          Submit a prescription for an enrolled member. All fields marked with * are required.
        </p>

        {error && <div className={styles.errorBanner}>{error}</div>}

        <form onSubmit={handleSubmit}>
          {/* ── Section 1: Enrollee Information ─── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>1.</span> Enrollee Information
            </h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>
                  Enrollee ID (CIF) <span className={styles.required}>*</span>
                </label>
                <input
                  className={styles.input}
                  value={enrolleeId}
                  onChange={(e) => setEnrolleeId(e.target.value)}
                  placeholder="e.g. CIF12345"
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>
                  Enrollee Full Name <span className={styles.required}>*</span>
                </label>
                <input
                  className={styles.input}
                  value={enrolleeName}
                  onChange={(e) => setEnrolleeName(e.target.value)}
                  placeholder="Full name of the member"
                />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>Gender</label>
                <select
                  className={styles.select}
                  value={enrolleeGender}
                  onChange={(e) => setEnrolleeGender(e.target.value)}
                >
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label}>
                  Facility Name <span className={styles.required}>*</span>
                </label>
                <input
                  className={styles.input}
                  value={facilityName}
                  onChange={(e) => setFacilityName(e.target.value)}
                  placeholder="Hospital / Clinic name"
                />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>Facility Branch</label>
                <input
                  className={styles.input}
                  value={facilityBranch}
                  onChange={(e) => setFacilityBranch(e.target.value)}
                  placeholder="Optional"
                />
              </div>
              <div />
            </div>
          </div>

          {/* ── Section 2: Clinical Information ─── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>2.</span> Clinical Information
            </h2>
            <div className={styles.formRowFull}>
              <div className={styles.field}>
                <label className={styles.label}>
                  Diagnosis / Clinical Indication <span className={styles.required}>*</span>
                </label>
                <textarea
                  className={styles.textarea}
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="e.g. Hypertension Stage 2, Upper respiratory tract infection"
                  rows={2}
                />
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>
                  Treating Doctor <span className={styles.required}>*</span>
                </label>
                <input
                  className={styles.input}
                  value={treatingDoctor}
                  onChange={(e) => setTreatingDoctor(e.target.value)}
                  placeholder="Dr. name"
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Doctor Phone</label>
                <input
                  className={styles.input}
                  value={doctorPhone}
                  onChange={(e) => setDoctorPhone(e.target.value)}
                  placeholder="Optional"
                />
              </div>
            </div>
          </div>

          {/* ── Section 3: Medications ──────────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>3.</span> Medications
            </h2>

            {medications.map((med, idx) => (
              <div className={styles.medLine} key={idx}>
                <div className={styles.medLineHeader}>
                  <span className={styles.medLineNumber}>Medication {idx + 1}</span>
                  {medications.length > 1 && (
                    <button
                      type="button"
                      className={styles.removeMedBtn}
                      onClick={() => removeMedLine(idx)}
                      title="Remove"
                    >
                      &times;
                    </button>
                  )}
                </div>

                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      Drug Name <span className={styles.required}>*</span>
                    </label>
                    <div className={styles.autocompleteWrap}>
                      <input
                        className={styles.input}
                        value={med.drug_name}
                        onChange={(e) => handleDrugSearch(idx, e.target.value)}
                        onFocus={() => med.drug_name.length >= 2 && setActiveSearch(idx)}
                        onBlur={() => setTimeout(() => setActiveSearch(null), 200)}
                        placeholder="Type to search..."
                      />
                      {activeSearch === idx && searchResults.length > 0 && (
                        <div className={styles.autocompleteDropdown}>
                          {searchResults.map((drug) => (
                            <div
                              key={drug.drug_id}
                              className={styles.autocompleteItem}
                              onMouseDown={() => selectDrug(idx, drug)}
                            >
                              <span className={styles.autocompleteName}>
                                {drug.generic_name}
                              </span>
                              <span className={`${styles.categoryBadge} ${categoryBadge(drug.category)}`}>
                                {drug.category}
                              </span>
                              {drug.common_brand_names && (
                                <div className={styles.autocompleteMeta}>
                                  {drug.common_brand_names}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Strength</label>
                    <input
                      className={styles.input}
                      value={med.strength}
                      onChange={(e) => updateMed(idx, "strength", e.target.value)}
                      placeholder="e.g. 500mg, 10mg"
                    />
                  </div>
                </div>

                <div className={styles.formRowThree}>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      Dosage <span className={styles.required}>*</span>
                    </label>
                    <input
                      className={styles.input}
                      value={med.dosage_instruction}
                      onChange={(e) => updateMed(idx, "dosage_instruction", e.target.value)}
                      placeholder="e.g. 1 tab BD"
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      Duration <span className={styles.required}>*</span>
                    </label>
                    <input
                      className={styles.input}
                      value={med.duration}
                      onChange={(e) => updateMed(idx, "duration", e.target.value)}
                      placeholder="e.g. 5 days"
                    />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      Quantity <span className={styles.required}>*</span>
                    </label>
                    <input
                      className={styles.input}
                      value={med.quantity}
                      onChange={(e) => updateMed(idx, "quantity", e.target.value)}
                      placeholder="e.g. 10 tabs"
                    />
                  </div>
                </div>

                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>Route</label>
                    <select
                      className={styles.select}
                      value={med.route}
                      onChange={(e) => updateMed(idx, "route", e.target.value)}
                    >
                      <option value="oral">Oral</option>
                      <option value="iv">IV</option>
                      <option value="im">IM</option>
                      <option value="topical">Topical</option>
                      <option value="inhaled">Inhaled</option>
                      <option value="sublingual">Sublingual</option>
                      <option value="rectal">Rectal</option>
                      <option value="ophthalmic">Ophthalmic</option>
                      <option value="otic">Otic</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div />
                </div>
              </div>
            ))}

            <button type="button" className={styles.addMedBtn} onClick={addMedLine}>
              + Add Another Medication
            </button>
          </div>

          {/* ── Section 4: Delivery Location ────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>4.</span> Delivery Location
            </h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>
                  State <span className={styles.required}>*</span>
                </label>
                <select
                  className={styles.select}
                  value={deliveryState}
                  onChange={(e) => setDeliveryState(e.target.value)}
                >
                  <option value="">Select State</option>
                  {states.map((s) => (
                    <option key={s.name} value={s.name}>
                      {s.name} {s.is_lagos ? "(Lagos)" : ""}
                    </option>
                  ))}
                </select>
              </div>
              <div className={styles.field}>
                <label className={styles.label}>
                  LGA <span className={styles.required}>*</span>
                </label>
                <select
                  className={styles.select}
                  value={deliveryLga}
                  onChange={(e) => setDeliveryLga(e.target.value)}
                  disabled={!deliveryState}
                >
                  <option value="">
                    {lgas.length ? "Select LGA" : "Select a state first"}
                  </option>
                  {lgas.map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>City</label>
                <input
                  className={styles.input}
                  value={deliveryCity}
                  onChange={(e) => setDeliveryCity(e.target.value)}
                  placeholder="Optional"
                />
              </div>
              <div className={styles.field}>
                <label className={styles.label}>Landmark</label>
                <input
                  className={styles.input}
                  value={deliveryLandmark}
                  onChange={(e) => setDeliveryLandmark(e.target.value)}
                  placeholder="Optional"
                />
              </div>
            </div>
            <div className={styles.formRowFull}>
              <div className={styles.field}>
                <label className={styles.label}>Delivery Address</label>
                <textarea
                  className={styles.textarea}
                  value={deliveryAddress}
                  onChange={(e) => setDeliveryAddress(e.target.value)}
                  placeholder="Full delivery address (optional)"
                  rows={2}
                />
              </div>
            </div>
          </div>

          {/* ── Section 5: Additional Info ──────── */}
          <div className={styles.section}>
            <h2 className={styles.sectionTitle}>
              <span className={styles.sectionTitleIcon}>5.</span> Additional Information
            </h2>
            <div className={styles.formRow}>
              <div className={styles.field}>
                <label className={styles.label}>Urgency</label>
                <select
                  className={styles.select}
                  value={urgency}
                  onChange={(e) => setUrgency(e.target.value)}
                >
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
                <textarea
                  className={styles.textarea}
                  value={providerNotes}
                  onChange={(e) => setProviderNotes(e.target.value)}
                  placeholder="Additional notes for the fulfilment team (optional)"
                  rows={2}
                />
              </div>
            </div>
          </div>

          {/* ── Submit ─────────────────────────── */}
          <div className={styles.submitArea}>
            <button
              type="button"
              className={styles.cancelBtn}
              onClick={() => navigate("/dashboard")}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Request"}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}

// ── Shared Header Component ───────────────────────
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

// ── Navigation Bar ────────────────────────────────
function NavBar({ active }) {
  return (
    <nav className={styles.navBar}>
      <Link
        to="/dashboard"
        className={active === "verification" ? styles.navLinkActive : styles.navLink}
      >
        Verification
      </Link>
      <Link
        to="/medication-request"
        className={active === "new-request" ? styles.navLinkActive : styles.navLink}
      >
        New Rx Request
      </Link>
      <Link
        to="/medication-requests"
        className={active === "history" ? styles.navLinkActive : styles.navLink}
      >
        Request History
      </Link>
    </nav>
  );
}
