import React, { useEffect, useState } from "react";
import { getServiceTypes } from "../services/api";
import styles from "./shared.module.css";

export default function VisitTypeSelector({ member, onSelect }) {
  const [serviceTypes, setServiceTypes] = useState([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchTypes = async () => {
      if (!member.cif_number || !member.scheme_id) {
        setError("Missing CIF number or Scheme ID for this enrollee.");
        setLoading(false);
        return;
      }
      try {
        const { data } = await getServiceTypes(member.cif_number, member.scheme_id);
        if (data.success) {
          setServiceTypes(data.service_types || []);
        } else {
          setError(data.reason || "Failed to load visit types");
        }
      } catch (err) {
        setError(err.response?.data?.detail || "Failed to load visit types");
      } finally {
        setLoading(false);
      }
    };
    fetchTypes();
  }, [member.cif_number, member.scheme_id]);

  const handleContinue = () => {
    if (!selected) return;
    const selectedType = serviceTypes.find(
      (st) =>
        (st.ID || st.Id || st.id || st.SERVICE_TYPE_ID || st.ServiceTypeId) ===
        selected
    );
    onSelect(selectedType || { id: selected, name: selected });
  };

  if (loading) {
    return (
      <div className={styles.card}>
        <p className={styles.cardSubtitle}>Loading visit types...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.card}>
        <div className={styles.error}>{error}</div>
      </div>
    );
  }

  // Derive display name & ID from various possible field names
  const getTypeName = (st) =>
    st.DESCRIPTION ||
    st.Description ||
    st.description ||
    st.SERVICE_TYPE ||
    st.ServiceType ||
    st.NAME ||
    st.Name ||
    st.name ||
    st.VALUE ||
    st.Value ||
    "Unknown";

  const getTypeId = (st) =>
    String(
      st.ID ?? st.Id ?? st.id ?? st.SERVICE_TYPE_ID ?? st.ServiceTypeId ?? st.CODE ?? st.Code ?? st.code ?? getTypeName(st)
    );

  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>Select Visit Type</h2>
      <p className={styles.cardSubtitle}>
        Choose the type of service for this visit.
      </p>

      {serviceTypes.length === 0 ? (
        <p className={styles.cardSubtitle}>
          No service types available for this enrollee's plan.
        </p>
      ) : (
        <>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", marginBottom: "1rem" }}>
            {serviceTypes.map((st) => {
              const typeId = getTypeId(st);
              const typeName = getTypeName(st);
              return (
                <label
                  key={typeId}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.6rem",
                    padding: "0.65rem 0.85rem",
                    borderRadius: "8px",
                    border: selected === typeId ? "2px solid #C61531" : "1.5px solid #ddd",
                    background: selected === typeId ? "#FFF0F0" : "#fff",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                >
                  <input
                    type="radio"
                    name="visitType"
                    value={typeId}
                    checked={selected === typeId}
                    onChange={() => setSelected(typeId)}
                    style={{ accentColor: "#C61531" }}
                  />
                  <span style={{ fontWeight: 600, fontSize: "0.92rem", color: "#263626" }}>
                    {typeName}
                  </span>
                </label>
              );
            })}
          </div>

          <button
            onClick={handleContinue}
            disabled={!selected}
            className={styles.primaryBtn}
          >
            Continue
          </button>
        </>
      )}
    </div>
  );
}
