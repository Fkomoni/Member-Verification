"""
Approximate centre coordinates for Nigerian LGAs.

Used to find the nearest LGAs when a pharmacy search for a specific LGA
returns no results — allowing the system to try the geographically closest
LGAs before falling back to a full state search.

Coordinates are approximate centroids (lat, lng). Accuracy is sufficient
for proximity ranking (finding which LGA is 3km vs 15km away).
"""

import math


# ── LGA Centre Coordinates ────────────────────────────────────────
# Format: { "State": { "LGA Name": (lat, lng), ... } }

LGA_COORDS: dict[str, dict[str, tuple[float, float]]] = {

    # ── Lagos (20 LGAs) ─────────────────────────────────────────
    "Lagos": {
        "Agege":              (6.621,  3.322),
        "Ajeromi-Ifelodun":   (6.474,  3.356),
        "Alimosho":           (6.614,  3.255),
        "Amuwo-Odofin":       (6.464,  3.316),
        "Apapa":              (6.449,  3.361),
        "Badagry":            (6.415,  2.886),
        "Epe":                (6.583,  3.983),
        "Eti-Osa":            (6.469,  3.574),
        "Ibeju-Lekki":        (6.449,  3.771),
        "Ifako-Ijaiye":       (6.652,  3.296),
        "Ikeja":              (6.601,  3.347),
        "Ikorodu":            (6.619,  3.510),
        "Kosofe":             (6.558,  3.415),
        "Lagos Island":       (6.453,  3.397),
        "Lagos Mainland":     (6.496,  3.379),
        "Mushin":             (6.523,  3.353),
        "Ojo":                (6.472,  3.246),
        "Oshodi-Isolo":       (6.554,  3.343),
        "Shomolu":            (6.554,  3.383),
        "Surulere":           (6.498,  3.352),
    },

    # ── FCT / Abuja (6 LGAs) ────────────────────────────────────
    "FCT": {
        "Abaji":              (8.616,  7.194),
        "Abuja Municipal":    (9.057,  7.498),
        "Bwari":              (9.243,  7.382),
        "Gwagwalada":         (8.945,  7.080),
        "Kuje":               (8.876,  7.225),
        "Kwali":              (8.766,  7.076),
    },

    # ── Rivers (23 LGAs) ─────────────────────────────────────────
    "Rivers": {
        "Abua/Odual":         (4.993,  6.726),
        "Ahoada East":        (5.083,  6.627),
        "Ahoada West":        (4.995,  6.527),
        "Akuku-Toru":         (4.731,  6.873),
        "Andoni":             (4.485,  7.367),
        "Asari-Toru":         (4.733,  6.952),
        "Bonny":              (4.443,  7.152),
        "Degema":             (4.729,  6.764),
        "Eleme":              (4.759,  7.143),
        "Emohua":             (4.708,  6.862),
        "Etche":              (5.108,  7.057),
        "Gokana":             (4.776,  7.166),
        "Ikwerre":            (5.009,  6.975),
        "Khana":              (4.783,  7.340),
        "Obio/Akpor":         (4.863,  7.023),
        "Ogba/Egbema/Ndoni":  (5.267,  6.706),
        "Ogu/Bolo":           (4.694,  7.036),
        "Okrika":             (4.729,  7.075),
        "Omuma":              (5.219,  7.090),
        "Opobo/Nkoro":        (4.506,  7.494),
        "Oyigbo":             (4.885,  7.148),
        "Port Harcourt":      (4.815,  7.049),
        "Tai":                (4.745,  7.220),
    },

    # ── Ogun (20 LGAs) ─────────────────────────────────────────
    "Ogun": {
        "Abeokuta North":     (7.153,  3.346),
        "Abeokuta South":     (7.115,  3.356),
        "Ado-Odo/Ota":        (6.695,  3.151),
        "Egbado North":       (8.016,  2.849),
        "Egbado South":       (7.063,  2.978),
        "Ewekoro":            (6.997,  3.191),
        "Ifo":                (6.815,  3.195),
        "Ijebu East":         (6.930,  4.027),
        "Ijebu North":        (6.999,  3.862),
        "Ijebu North East":   (7.086,  4.040),
        "Ijebu Ode":          (6.820,  3.918),
        "Ikenne":             (6.882,  3.714),
        "Imeko Afon":         (7.557,  3.021),
        "Ipokia":             (6.614,  2.778),
        "Obafemi Owode":      (7.004,  3.417),
        "Odeda":              (7.206,  3.284),
        "Odogbolu":           (6.898,  3.844),
        "Ogun Waterside":     (6.642,  4.000),
        "Remo North":         (6.935,  3.714),
        "Sagamu":             (6.840,  3.646),
    },

    # ── Oyo (33 LGAs) ──────────────────────────────────────────
    "Oyo": {
        "Afijio":             (7.787,  3.834),
        "Akinyele":           (7.474,  3.887),
        "Atiba":              (7.927,  3.944),
        "Atisbo":             (8.473,  3.284),
        "Egbeda":             (7.360,  3.845),
        "Ibadan North":       (7.395,  3.900),
        "Ibadan North East":  (7.411,  3.937),
        "Ibadan North West":  (7.396,  3.855),
        "Ibadan South East":  (7.362,  3.916),
        "Ibadan South West":  (7.356,  3.880),
        "Ibarapa Central":    (7.324,  3.247),
        "Ibarapa East":       (7.444,  3.389),
        "Ibarapa North":      (7.660,  3.143),
        "Ido":                (7.426,  3.793),
        "Irepo":              (8.785,  3.638),
        "Iseyin":             (7.969,  3.601),
        "Itesiwaju":          (8.183,  3.384),
        "Iwajowa":            (8.279,  3.231),
        "Kajola":             (7.993,  3.215),
        "Lagelu":             (7.493,  4.007),
        "Ogbomosho North":    (8.135,  4.238),
        "Ogbomosho South":    (8.079,  4.259),
        "Ogo Oluwa":          (8.085,  4.411),
        "Olorunsogo":         (8.372,  3.569),
        "Oluyole":            (7.272,  3.857),
        "Ona Ara":            (7.296,  3.955),
        "Orelope":            (8.716,  3.516),
        "Ori Ire":            (8.059,  4.525),
        "Oyo East":           (7.817,  3.980),
        "Oyo West":           (7.817,  3.880),
        "Saki East":          (8.648,  3.394),
        "Saki West":          (8.672,  3.265),
        "Surulere":           (8.498,  4.557),
    },

    # ── Kano (44 LGAs — selected urban ones) ────────────────────
    "Kano": {
        "Dala":               (11.996, 8.533),
        "Fagge":              (12.000, 8.512),
        "Gwale":              (11.963, 8.510),
        "Kano Municipal":     (12.000, 8.592),
        "Kumbotso":           (12.048, 8.565),
        "Nassarawa":          (11.971, 8.560),
        "Tarauni":            (12.005, 8.557),
        "Ungogo":             (12.039, 8.489),
    },

    # ── Kaduna (23 LGAs — selected) ─────────────────────────────
    "Kaduna": {
        "Chikun":             (10.459, 7.440),
        "Igabi":              (10.717, 7.334),
        "Kaduna North":       (10.546, 7.437),
        "Kaduna South":       (10.501, 7.437),
    },

    # ── Edo (18 LGAs) ───────────────────────────────────────────
    "Edo": {
        "Akoko-Edo":          (7.262,  5.948),
        "Egor":               (6.308,  5.648),
        "Esan Central":       (6.755,  6.165),
        "Esan North East":    (6.825,  6.282),
        "Esan South East":    (6.639,  6.257),
        "Esan West":          (6.736,  6.059),
        "Etsako Central":     (7.074,  6.192),
        "Etsako East":        (7.193,  6.359),
        "Etsako West":        (7.149,  6.093),
        "Igueben":            (6.636,  6.195),
        "Ikpoba Okha":        (6.295,  5.655),
        "Orhionmwon":         (6.110,  5.706),
        "Oredo":              (6.340,  5.627),
        "Ovia North East":    (6.478,  5.327),
        "Ovia South West":    (6.245,  5.284),
        "Owan East":          (7.008,  5.994),
        "Owan West":          (7.082,  5.829),
        "Uhunmwonde":         (6.138,  5.778),
    },

    # ── Delta (25 LGAs — selected) ───────────────────────────────
    "Delta": {
        "Aniocha North":      (6.471,  6.596),
        "Aniocha South":      (6.272,  6.629),
        "Bomadi":             (5.573,  5.856),
        "Burutu":             (5.352,  5.508),
        "Ethiope East":       (5.634,  6.043),
        "Ethiope West":       (5.610,  5.900),
        "Ika North East":     (6.264,  6.385),
        "Ika South":          (6.077,  6.375),
        "Isoko North":        (5.457,  6.213),
        "Isoko South":        (5.363,  6.226),
        "Ndokwa East":        (5.766,  6.561),
        "Ndokwa West":        (5.695,  6.468),
        "Okpe":               (5.650,  5.795),
        "Oshimili North":     (6.189,  6.794),
        "Oshimili South":     (6.068,  6.790),
        "Patani":             (5.652,  6.214),
        "Sapele":             (5.899,  5.680),
        "Udu":                (5.638,  5.769),
        "Ughelli North":      (5.505,  5.990),
        "Ughelli South":      (5.399,  5.976),
        "Ukwuani":            (5.823,  6.433),
        "Uvwie":              (5.597,  5.765),
        "Warri Central":      (5.516,  5.747),
        "Warri North":        (5.633,  5.600),
        "Warri South":        (5.426,  5.704),
    },
}


# ── Haversine ────────────────────────────────────────────────────

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── Public API ───────────────────────────────────────────────────

def find_nearest_lgas(
    state: str,
    lat: float,
    lng: float,
    exclude_lga: str = "",
    limit: int = 3,
) -> list[str]:
    """
    Return LGA names in `state` sorted by distance from (lat, lng),
    excluding the LGA that already failed.

    Returns [] if we have no coordinate data for that state.
    """
    # Normalise state key — handle "FCT" / "Abuja" variations
    state_key = state.strip()
    if state_key not in LGA_COORDS:
        # Case-insensitive fallback
        for k in LGA_COORDS:
            if k.lower() == state_key.lower():
                state_key = k
                break
        else:
            return []

    lgas = LGA_COORDS[state_key]
    exclude_lower = exclude_lga.strip().lower()

    ranked: list[tuple[float, str]] = []
    for lga_name, (lga_lat, lga_lng) in lgas.items():
        if lga_name.lower() == exclude_lower:
            continue
        dist = _haversine_km(lat, lng, lga_lat, lga_lng)
        ranked.append((dist, lga_name))

    ranked.sort()
    return [name for _, name in ranked[:limit]]
