import React, { useState } from "react";
import MemberValidator from "../components/MemberValidator";
import AuthCodeValidator from "../components/AuthCodeValidator";
import ReimbursementForm from "../components/ReimbursementForm";
import s from "../components/memberportal.module.css";
import styles from "./MemberPortalPage.module.css";

const STEPS = [
  { label: "Verify Identity" },
  { label: "Authorization Code" },
  { label: "Submit Claim" },
];

export default function MemberPortalPage() {
  const [step, setStep] = useState(0);
  const [memberData, setMemberData] = useState(null);
  const [codeData, setCodeData] = useState(null);
  const [result, setResult] = useState(null);

  const handleMemberValidated = (data) => {
    setMemberData(data);
    setStep(1);
  };

  const handleCodeValidated = (data) => {
    setCodeData(data);
    setStep(2);
  };

  const handleSubmitted = (data) => {
    setResult(data);
    setStep(3);
  };

  const handleStartOver = () => {
    setStep(0);
    setMemberData(null);
    setCodeData(null);
    setResult(null);
  };

  const formatAmount = (amount) =>
    new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN" }).format(amount);

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLogo}>
          <svg viewBox="0 0 40 40" width="32" height="32">
            <circle cx="20" cy="20" r="18" fill="url(#mpGrad)" />
            <defs>
              <linearGradient id="mpGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#F15A24" />
                <stop offset="100%" stopColor="#FFCE07" />
              </linearGradient>
            </defs>
          </svg>
          <div>
            <span className={styles.headerBrand}>LEADWAY</span>
            <span className={styles.headerBrandHealth}> Health</span>
          </div>
          <span className={styles.headerDivider} />
          <span className={styles.headerPortal}>Reimbursement Portal</span>
        </div>
      </header>

      <main className={styles.main}>
        {/* Step indicator (only show for steps 0–2) */}
        {step < 3 && (
          <div className={s.steps}>
            {STEPS.map((st, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && (
                  <div
                    className={`${s.stepConnector} ${idx <= step ? s.stepConnectorActive : ""}`}
                  />
                )}
                <div
                  className={`${s.step} ${
                    idx === step ? s.stepActive : idx < step ? s.stepComplete : ""
                  }`}
                >
                  <div className={s.stepNumber}>
                    {idx < step ? (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <span className={s.stepLabel}>{st.label}</span>
                </div>
              </React.Fragment>
            ))}
          </div>
        )}

        {/* Step Content */}
        {step === 0 && (
          <MemberValidator onValidated={handleMemberValidated} />
        )}

        {step === 1 && (
          <AuthCodeValidator
            memberData={memberData}
            onValidated={handleCodeValidated}
            onBack={() => setStep(0)}
          />
        )}

        {step === 2 && (
          <ReimbursementForm
            memberData={memberData}
            codeData={codeData}
            onSubmitted={handleSubmitted}
            onBack={() => setStep(1)}
          />
        )}

        {step === 3 && result && (
          <div className={s.successCard}>
            <div className={s.successIconLarge}>
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#0A7C3E" strokeWidth="2.5">
                <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h2 className={s.successTitle}>Claim Submitted Successfully</h2>
            <p className={s.successMessage}>
              Your reimbursement claim has been submitted and is now being processed.
              Please save your claim reference number below for tracking.
            </p>
            <div className={s.claimRefDisplay}>
              <div className={s.claimRefLabel}>Claim Reference</div>
              <div className={s.claimRefValue}>{result.claim_ref}</div>
            </div>
            <p className={s.successMessage} style={{ fontSize: "0.82rem", color: "#888" }}>
              Our claims team will review your submission.
              You will be contacted if additional information is needed.
            </p>
            <button onClick={handleStartOver} className={s.primaryBtn} style={{ maxWidth: 320, margin: "0 auto" }}>
              Submit Another Claim
            </button>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        Leadway Health Services &mdash; For health, wealth &amp; more...
      </footer>
    </div>
  );
}
