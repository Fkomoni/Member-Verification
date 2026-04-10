import React, { useState, useEffect, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  lookupEnrollee,
  searchMedications,
  getStates,
  createMedicationRequest,
  validateAddress,
  searchPharmacies,
} from "../services/api";
import logo from "../assets/logos/leadway-logo.png.jpeg";
import styles from "./MedicationRequestPage.module.css";

/** Haversine distance in km between two lat/lng pairs. */
const haversineKm = (lat1, lon1, lat2, lon2) => {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

/** Top 200 most common Nigerian diagnoses (hardcoded — no API required). */
const NIGERIAN_DIAGNOSES = [
  "Malaria",
  "Uncomplicated Malaria",
  "Severe Malaria",
  "Typhoid Fever",
  "Upper Respiratory Tract Infection (URTI)",
  "Lower Respiratory Tract Infection (LRTI)",
  "Pneumonia",
  "Bronchopneumonia",
  "Asthma",
  "Hypertension",
  "Diabetes Mellitus Type 2",
  "Diabetes Mellitus Type 1",
  "Urinary Tract Infection (UTI)",
  "Gastroenteritis",
  "Peptic Ulcer Disease",
  "Gastro-Oesophageal Reflux Disease (GERD)",
  "Anaemia",
  "Sickle Cell Disease",
  "Sickle Cell Crisis",
  "Tuberculosis (TB)",
  "Pulmonary Tuberculosis",
  "HIV/AIDS",
  "Hepatitis B",
  "Hepatitis C",
  "Malaria in Pregnancy",
  "Preeclampsia",
  "Eclampsia",
  "Sepsis",
  "Meningitis",
  "Bacterial Meningitis",
  "Viral Meningitis",
  "Epilepsy / Seizure Disorder",
  "Febrile Seizures",
  "Stroke (Cerebrovascular Accident)",
  "Ischaemic Stroke",
  "Haemorrhagic Stroke",
  "Heart Failure",
  "Congestive Heart Failure",
  "Myocardial Infarction",
  "Angina Pectoris",
  "Acute Coronary Syndrome",
  "Atrial Fibrillation",
  "Deep Vein Thrombosis (DVT)",
  "Pulmonary Embolism",
  "Kidney Disease / Chronic Kidney Disease (CKD)",
  "Acute Kidney Injury (AKI)",
  "Nephrotic Syndrome",
  "Nephritic Syndrome",
  "Liver Cirrhosis",
  "Acute Hepatitis",
  "Jaundice",
  "Neonatal Jaundice",
  "Cholecystitis",
  "Cholelithiasis (Gallstones)",
  "Pancreatitis",
  "Appendicitis",
  "Intestinal Obstruction",
  "Hernia",
  "Inguinal Hernia",
  "Fibroid (Uterine Leiomyoma)",
  "Ovarian Cyst",
  "Polycystic Ovary Syndrome (PCOS)",
  "Pelvic Inflammatory Disease (PID)",
  "Sexually Transmitted Infection (STI)",
  "Gonorrhoea",
  "Syphilis",
  "Chlamydia",
  "Vaginal Candidiasis",
  "Trichomoniasis",
  "Ectopic Pregnancy",
  "Threatened Abortion",
  "Incomplete Abortion",
  "Anaemia in Pregnancy",
  "Gestational Diabetes",
  "Postpartum Haemorrhage",
  "Caesarean Section",
  "Neonatal Sepsis",
  "Neonatal Pneumonia",
  "Low Birth Weight",
  "Protein-Energy Malnutrition",
  "Kwashiorkor",
  "Marasmus",
  "Vitamin A Deficiency",
  "Iron Deficiency Anaemia",
  "Folate Deficiency",
  "Skin Infection",
  "Cellulitis",
  "Wound Infection",
  "Abscess",
  "Scabies",
  "Tinea Capitis (Ringworm)",
  "Tinea Corporis",
  "Tinea Pedis (Athlete's Foot)",
  "Eczema / Atopic Dermatitis",
  "Psoriasis",
  "Urticaria (Hives)",
  "Allergic Reaction",
  "Conjunctivitis",
  "Allergic Conjunctivitis",
  "Trachoma",
  "Glaucoma",
  "Cataract",
  "Otitis Media",
  "Otitis Externa",
  "Tonsillitis",
  "Pharyngitis",
  "Sinusitis",
  "Rhinitis",
  "Allergic Rhinitis",
  "Dental Caries",
  "Periodontal Disease",
  "Oral Candidiasis (Thrush)",
  "Diarrhoea",
  "Acute Watery Diarrhoea",
  "Bloody Diarrhoea / Dysentery",
  "Cholera",
  "Salmonella Infection",
  "Shigellosis",
  "Amoebiasis",
  "Giardiasis",
  "Worm Infestation / Helminthiasis",
  "Ascariasis",
  "Hookworm Infection",
  "Schistosomiasis",
  "Filariasis / Lymphatic Filariasis",
  "Onchocerciasis (River Blindness)",
  "Guinea Worm Disease (Dracunculiasis)",
  "Lassa Fever",
  "Dengue Fever",
  "Yellow Fever",
  "Rabies",
  "Chickenpox (Varicella)",
  "Measles",
  "Mumps",
  "Rubella",
  "Meningococcal Disease",
  "Diphtheria",
  "Pertussis (Whooping Cough)",
  "Tetanus",
  "Neonatal Tetanus",
  "Poliomyelitis",
  "COVID-19",
  "Influenza",
  "Viral Fever",
  "Dengue Haemorrhagic Fever",
  "Monkeypox",
  "Osteoarthritis",
  "Rheumatoid Arthritis",
  "Gout",
  "Back Pain / Low Back Pain",
  "Neck Pain / Cervical Spondylosis",
  "Fracture",
  "Dislocation",
  "Sprain / Strain",
  "Soft Tissue Injury",
  "Burns",
  "Road Traffic Accident (RTA)",
  "Head Injury / Traumatic Brain Injury",
  "Anxiety Disorder",
  "Depression",
  "Schizophrenia",
  "Bipolar Disorder",
  "Substance Use Disorder",
  "Alcohol Use Disorder",
  "Dementia",
  "Attention Deficit Hyperactivity Disorder (ADHD)",
  "Autism Spectrum Disorder",
  "Intellectual Disability",
  "Thyroid Disease",
  "Hypothyroidism",
  "Hyperthyroidism",
  "Goitre",
  "Obesity",
  "Dyslipidaemia",
  "Metabolic Syndrome",
  "Prostate Enlargement (BPH)",
  "Prostate Cancer",
  "Cervical Cancer",
  "Breast Cancer",
  "Colorectal Cancer",
  "Liver Cancer (HCC)",
  "Kaposi's Sarcoma",
  "Leukaemia",
  "Lymphoma",
  "Multiple Myeloma",
  "Pre-diabetes / Impaired Glucose Tolerance",
  "Hypertensive Heart Disease",
  "Hypertensive Nephropathy",
  "Diabetic Nephropathy",
  "Diabetic Retinopathy",
  "Diabetic Neuropathy",
  "Peripheral Vascular Disease",
  "Varicose Veins",
  "Haemorrhoids (Piles)",
  "Anal Fissure",
  "Rectal Prolapse",
  "Inflammatory Bowel Disease (IBD)",
  "Crohn's Disease",
  "Ulcerative Colitis",
  "Irritable Bowel Syndrome (IBS)",
  "Constipation",
  "Acute Abdomen",
  "Peritonitis",
  "Intussusception",
  "Herpes Simplex",
  "Herpes Zoster (Shingles)",
  "Impetigo",
  "Vitiligo",
  "Alopecia",
  "Acne Vulgaris",
  "Pilonidal Cyst",
  "Hydrocele",
  "Varicocele",
  "Undescended Testis",
  "Urinary Retention",
  "Urolithiasis (Kidney Stones)",
  "Renal Colic",
  "Enuresis (Bedwetting)",
  "Childhood Fever",
  "Febrile Illness NOS",
  "Pain NOS",
];

const EMPTY_MED = {
  drug_name: "", generic_name: "", matched_drug_id: null,
  strength: "", dosage_form: "", dosage_instruction: "", duration: "",
  frequency: "", med_notes: "",
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
  const [showDiagnosisDropdown, setShowDiagnosisDropdown] = useState(false);
  const [treatingDoctor, setTreatingDoctor] = useState("");
  const [providerNotes, setProviderNotes] = useState("");
  const [deliveryState, setDeliveryState] = useState("");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [addressValidation, setAddressValidation] = useState(null);
  const [addressValidating, setAddressValidating] = useState(false);
  const [pharmacies, setPharmacies] = useState([]);
  const [selectedPharmacy, setSelectedPharmacy] = useState(null);
  const [pharmacyLoading, setPharmacyLoading] = useState(false);
  const [deliveryCoords, setDeliveryCoords] = useState(null); // {lat, lng} from address validation
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
  }, []);

  // ── Auto-search pharmacies when state is selected ────────────
  useEffect(() => {
    if (!deliveryState) return;
    setPharmacyLoading(true);
    setPharmacies([]);
    setSelectedPharmacy(null);
    setDeliveryCoords(null); // coords only valid after address verify
    // State-level search (no coords yet — address not verified)
    searchPharmacies(deliveryState, "", "", null, null)
      .then(({ data }) => {
        const list = data.pharmacies || [];
        setPharmacies(list);
        if (list.length === 1) setSelectedPharmacy(list[0]);
      })
      .catch(() => setPharmacies([]))
      .finally(() => setPharmacyLoading(false));
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
    if (value.length < 2) { setDrugResults([]); setActiveSearch(null); return; }
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

  // ── Address validation ───────────────────────────
  const handleValidateAddress = async () => {
    if (!deliveryAddress.trim()) return;
    setAddressValidating(true);
    setAddressValidation(null);
    try {
      const { data } = await validateAddress(deliveryAddress.trim(), deliveryState);
      setAddressValidation(data);
      if (data.validated) {
        // Store coordinates for proximity-based pharmacy sorting
        if (data.lat && data.lng) setDeliveryCoords({ lat: data.lat, lng: data.lng });

        const resolvedState = data.state || deliveryState;
        const resolvedLga = data.lga || "";

        if (data.state && data.state !== deliveryState) {
          // State changed — useEffect on deliveryState triggers a fresh pharmacy search
          setDeliveryState(data.state);
        } else {
          // Refine pharmacy search by LGA, passing coordinates so the backend
          // can try neighboring LGAs before falling back to state-level
          setPharmacyLoading(true);
          const coordsNow = data.lat && data.lng ? { lat: data.lat, lng: data.lng } : deliveryCoords;
          try {
            const { data: pharmData } = await searchPharmacies(
              resolvedState, resolvedLga, "",
              coordsNow?.lat ?? null, coordsNow?.lng ?? null,
            );
            const list = pharmData.pharmacies || [];
            setPharmacies(list);
            if (list.length === 1) setSelectedPharmacy(list[0]);
          } catch { /* keep existing pharmacy list */ }
          setPharmacyLoading(false);
        }
      }
    } catch { setAddressValidation({ validated: false, reason: "Validation failed" }); }
    setAddressValidating(false);
  };

  const addMedLine = () => setMedications([...medications, { ...EMPTY_MED }]);
  const removeMedLine = (i) => { if (medications.length > 1) setMedications(medications.filter((_, idx) => idx !== i)); };
  const updateMed = (i, field, value) => { const u = [...medications]; u[i] = { ...u[i], [field]: value }; setMedications(u); };

  const filteredDiagnoses = diagnosis.length >= 2
    ? NIGERIAN_DIAGNOSES.filter(d => d.toLowerCase().includes(diagnosis.toLowerCase())).slice(0, 15)
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
      if (!m.strength.trim()) return setError(`Medication ${i + 1}: strength/mg is required`);
      if (!m.dosage_instruction.trim()) return setError(`Medication ${i + 1}: dose is required`);
      if (!m.frequency) return setError(`Medication ${i + 1}: frequency is required`);
      if (!m.duration.trim()) return setError(`Medication ${i + 1}: duration is required`);
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
        delivery_lga: addressValidation?.lga || null,
        delivery_address: deliveryAddress.trim(),
        urgency,
        facility_name: provider?.provider_name || "Unknown Facility",
        facility_branch: null,
        member_phone: memberPhone.trim(),
        member_email: memberEmail.trim() || null,
        // WellaHealth pharmacy code from the selected pharmacy card
        pharmacy_code: selectedPharmacy
          ? (selectedPharmacy.pharmacyCode || selectedPharmacy.PharmacyCode || selectedPharmacy.code || "")
          : "",
        medications: medications.map(m => ({
          drug_name: m.drug_name.trim(),
          generic_name: m.generic_name || null,
          matched_drug_id: m.matched_drug_id || null,
          strength: m.strength.trim() || null,
          dosage_instruction: m.dosage_instruction.trim(),
          duration: m.duration.trim(),
          // route field stores the dosing frequency (OD/BD/TDS/QDS/STAT/PRN)
          // WellaHealth dispatch reads item.route as the "frequency" field
          route: m.frequency || null,
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
    setDiagnosis(""); setTreatingDoctor("");
    setProviderNotes(""); setDeliveryState(""); setDeliveryAddress("");
    setAddressValidation(null); setDeliveryCoords(null); setPharmacies([]); setSelectedPharmacy(null);
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
              {success.pharmacy_code && (
                <div className={styles.routingDestination} style={{marginTop:"8px"}}>
                  <span className={styles.routingLabel}>Pharmacy Code</span>
                  <span className={styles.routingBadge} style={{fontFamily:"monospace"}}>{success.pharmacy_code}</span>
                </div>
              )}
              {success.routing.reasoning && <div className={styles.classificationReasoning}>{success.routing.reasoning}</div>}
            </div>
          )}
          {/* WellaHealth dispatch result */}
          {success.routing?.destination === "wellahealth" && (
            <div className={styles.routingCard} style={{borderLeft: success.wellahealth_dispatched === true ? "4px solid #16a34a" : success.wellahealth_dispatched === false ? "4px solid #dc2626" : "4px solid #d1d5db"}}>
              <h3 className={styles.classificationCardTitle}>WellaHealth Dispatch</h3>
              {success.wellahealth_dispatched === true && (
                <>
                  <div className={styles.routingDestination}>
                    <span className={styles.routingLabel}>Status</span>
                    <span className={styles.routingBadge} style={{background:"#dcfce7",color:"#16a34a"}}>Sent successfully</span>
                  </div>
                  {success.wellahealth_tracking_code && (
                    <div className={styles.routingDestination} style={{marginTop:"8px"}}>
                      <span className={styles.routingLabel}>Tracking Code</span>
                      <span className={styles.routingBadge} style={{fontFamily:"monospace"}}>{success.wellahealth_tracking_code}</span>
                    </div>
                  )}
                </>
              )}
              {success.wellahealth_dispatched === false && (
                <div className={styles.routingDestination}>
                  <span className={styles.routingLabel}>Status</span>
                  <span className={styles.routingBadge} style={{background:"#fee2e2",color:"#dc2626"}}>
                    Dispatch failed — {success.wellahealth_error || "check Render logs"}
                  </span>
                </div>
              )}
              {success.wellahealth_dispatched == null && (
                <div className={styles.classificationReasoning}>Dispatching to WellaHealth... check logs for result.</div>
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
                  <input className={styles.input} value={diagnosis}
                    onChange={(e) => { setDiagnosis(e.target.value); setShowDiagnosisDropdown(true); }}
                    onFocus={() => diagnosis.length >= 2 && setShowDiagnosisDropdown(true)}
                    onBlur={() => setTimeout(() => setShowDiagnosisDropdown(false), 200)}
                    placeholder="Type diagnosis (e.g. Malaria, Typhoid...)" />
                  {showDiagnosisDropdown && filteredDiagnoses.length > 0 && (
                    <div className={styles.autocompleteDropdown}>
                      {filteredDiagnoses.map((d, i) => (
                        <div key={i} className={styles.autocompleteItem} onMouseDown={() => { setDiagnosis(d); setShowDiagnosisDropdown(false); }}>
                          <span className={styles.autocompleteName}>{d}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
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
                              {drug.brand_hint && !drug.brand_name && <span className={styles.autocompleteMeta} style={{color:"#6b7280"}}>also: {drug.brand_hint.split(",").slice(0,2).join(", ")}</span>}
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
                {/* WellaHealth format: name → strength | dose → frequency | duration | notes */}
                <div className={styles.formRow}>
                  <div className={styles.field}>
                    <label className={styles.label}>Strength / mg <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.strength}
                      onChange={(e) => updateMed(idx, "strength", e.target.value)}
                      placeholder="e.g. 500mg" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Dose <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.dosage_instruction}
                      onChange={(e) => updateMed(idx, "dosage_instruction", e.target.value)}
                      placeholder="e.g. 1 tab" />
                  </div>
                </div>
                <div className={styles.formRowThree}>
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
                  <div className={styles.field}>
                    <label className={styles.label}>Duration <span className={styles.required}>*</span></label>
                    <input className={styles.input} value={med.duration}
                      onChange={(e) => updateMed(idx, "duration", e.target.value)}
                      placeholder="e.g. 5 days" />
                  </div>
                  <div className={styles.field}>
                    <label className={styles.label}>Notes</label>
                    <input className={styles.input} value={med.med_notes}
                      onChange={(e) => updateMed(idx, "med_notes", e.target.value)}
                      placeholder="Optional" />
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

            {/* Pharmacy Selection — sorted by distance when address is verified */}
            {pharmacyLoading && <div className={styles.enrolleeMeta}>Searching nearby pharmacies...</div>}
            {!pharmacyLoading && deliveryState && pharmacies.length === 0 && (
              <div className={styles.enrolleeMeta} style={{color:"#b45309",marginTop:"8px"}}>
                No WellaHealth pharmacies found for {deliveryState}. Verify your address to search by LGA, or the request will be routed and pharmacy assigned during fulfilment.
              </div>
            )}
            {pharmacies.length > 0 && (() => {
              // Sort by distance if we have coordinates and pharmacies have lat/lng
              const sortedPharmacies = deliveryCoords
                ? [...pharmacies].sort((a, b) => {
                    const aLat = a.latitude || a.lat || a.Latitude;
                    const aLng = a.longitude || a.lng || a.Longitude;
                    const bLat = b.latitude || b.lat || b.Latitude;
                    const bLng = b.longitude || b.lng || b.Longitude;
                    if (!aLat || !bLat) return 0;
                    return haversineKm(deliveryCoords.lat, deliveryCoords.lng, aLat, aLng) -
                           haversineKm(deliveryCoords.lat, deliveryCoords.lng, bLat, bLng);
                  })
                : pharmacies;
              return (
                <div className={styles.formRowFull}>
                  <div className={styles.field}>
                    <label className={styles.label}>
                      Nearby Pharmacies ({pharmacies.length})
                      {deliveryCoords && " — sorted by distance"}
                    </label>
                    <div className={styles.pharmacyList}>
                      {sortedPharmacies.slice(0, 8).map((p, i) => {
                        const code = p.pharmacyCode || p.PharmacyCode || p.code || "";
                        const name = p.pharmacyName || p.PharmacyName || p.name || `Pharmacy ${i + 1}`;
                        const addr = p.address || p.Address || p.location || "";
                        const lgaName = p.lga || p.lgaName || p.LGA || "";
                        const pLat = p.latitude || p.lat || p.Latitude;
                        const pLng = p.longitude || p.lng || p.Longitude;
                        const dist = deliveryCoords && pLat && pLng
                          ? haversineKm(deliveryCoords.lat, deliveryCoords.lng, pLat, pLng)
                          : null;
                        const isSelected = selectedPharmacy &&
                          (selectedPharmacy.pharmacyCode || selectedPharmacy.code) === code;
                        const isNearest = i === 0 && deliveryCoords && pLat;
                        return (
                          <div key={i}
                            className={`${styles.pharmacyItem} ${isSelected ? styles.pharmacySelected : ""}`}
                            onClick={() => setSelectedPharmacy(p)}>
                            <div className={styles.pharmacyName}>
                              {name}
                              {isNearest && (
                                <span style={{fontSize:"0.7rem",background:"#059669",color:"#fff",
                                  padding:"1px 6px",borderRadius:"4px",marginLeft:"6px",fontWeight:600}}>
                                  Nearest
                                </span>
                              )}
                            </div>
                            {lgaName && <div className={styles.pharmacyAddr} style={{fontWeight:500}}>{lgaName}</div>}
                            {addr && <div className={styles.pharmacyAddr}>{addr}</div>}
                            <div className={styles.pharmacyCode}>
                              Code: {code}
                              {dist !== null && (
                                <span style={{marginLeft:"8px",color:"#6b7280",fontSize:"0.75rem"}}>
                                  ~{dist < 1 ? `${(dist * 1000).toFixed(0)}m` : `${dist.toFixed(1)}km`} away
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })()}
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
