import React from "react";

/**
 * Leadway Health HMO logo — references /leadway-logo.png in the public folder.
 * Drop your logo image as: frontend/public/leadway-logo.png
 */
export default function LeadwayLogo({ size = 40, className = "" }) {
  return (
    <img
      src="/leadway-logo.png"
      alt="Leadway Health HMO"
      width={size * 3.5}
      height={size}
      className={className}
      style={{ objectFit: "contain" }}
    />
  );
}
