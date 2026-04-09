"""
Nigerian States and LGAs — structured location data for routing decisions.

The key function is `is_lagos_location()` which determines if a delivery
address should be routed to Leadway WhatsApp Number A (Lagos) or B (Outside Lagos).

All 36 states + FCT are included. LGAs are provided for Lagos state (critical
for routing) and the other 5 most common enrollee states. The rest can be
expanded as needed.
"""

# ── All 36 States + FCT ─────────────────────────────────────────

NIGERIAN_STATES: list[str] = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa",
    "Benue", "Borno", "Cross River", "Delta", "Ebonyi", "Edo",
    "Ekiti", "Enugu", "FCT", "Gombe", "Imo", "Jigawa",
    "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara",
    "Lagos", "Nasarawa", "Niger", "Ogun", "Ondo", "Osun",
    "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
]

# ── LGAs by State (Lagos fully enumerated; others key states) ───

LGAS_BY_STATE: dict[str, list[str]] = {
    "Lagos": [
        "Agege", "Ajeromi-Ifelodun", "Alimosho", "Amuwo-Odofin", "Apapa",
        "Badagry", "Epe", "Eti-Osa", "Ibeju-Lekki", "Ifako-Ijaiye",
        "Ikeja", "Ikorodu", "Kosofe", "Lagos Island", "Lagos Mainland",
        "Mushin", "Ojo", "Oshodi-Isolo", "Shomolu", "Surulere",
    ],
    "FCT": [
        "Abaji", "Abuja Municipal", "Bwari", "Gwagwalada", "Kuje", "Kwali",
    ],
    "Rivers": [
        "Abua/Odual", "Ahoada East", "Ahoada West", "Akuku-Toru", "Andoni",
        "Asari-Toru", "Bonny", "Degema", "Eleme", "Emohua",
        "Etche", "Gokana", "Ikwerre", "Khana", "Obio/Akpor",
        "Ogba/Egbema/Ndoni", "Ogu/Bolo", "Okrika", "Omuma", "Opobo/Nkoro",
        "Oyigbo", "Port Harcourt", "Tai",
    ],
    "Ogun": [
        "Abeokuta North", "Abeokuta South", "Ado-Odo/Ota", "Egbado North",
        "Egbado South", "Ewekoro", "Ifo", "Ijebu East", "Ijebu North",
        "Ijebu North East", "Ijebu Ode", "Ikenne", "Imeko Afon",
        "Ipokia", "Obafemi Owode", "Odeda", "Odogbolu", "Ogun Waterside",
        "Remo North", "Sagamu",
    ],
    "Oyo": [
        "Afijio", "Akinyele", "Atiba", "Atisbo", "Egbeda",
        "Ibadan North", "Ibadan North-East", "Ibadan North-West",
        "Ibadan South-East", "Ibadan South-West", "Ibarapa Central",
        "Ibarapa East", "Ibarapa North", "Ido", "Irepo",
        "Iseyin", "Itesiwaju", "Iwajowa", "Kajola", "Lagelu",
        "Ogbomosho North", "Ogbomosho South", "Ogo Oluwa", "Oluyole",
        "Ona Ara", "Orelope", "Ori Ire", "Oyo East", "Oyo West",
        "Saki East", "Saki West", "Surulere",
    ],
    "Kano": [
        "Ajingi", "Albasu", "Bagwai", "Bebeji", "Bichi",
        "Bunkure", "Dala", "Dambatta", "Dawakin Kudu", "Dawakin Tofa",
        "Doguwa", "Fagge", "Gabasawa", "Garko", "Garun Mallam",
        "Gaya", "Gezawa", "Gwale", "Gwarzo", "Kabo",
        "Kano Municipal", "Karaye", "Kibiya", "Kiru", "Kumbotso",
        "Kunchi", "Kura", "Madobi", "Makoda", "Minjibir",
        "Nasarawa", "Rano", "Rimin Gado", "Rogo", "Shanono",
        "Sumaila", "Takai", "Tarauni", "Tofa", "Tsanyawa",
        "Tudun Wada", "Ungogo", "Warawa", "Wudil",
    ],
}

# ── Lagos Aliases (for normalization) ────────────────────────────

_LAGOS_ALIASES = {
    "lagos", "lagos state", "lgs", "lag",
    "ikeja", "lekki", "vi", "victoria island",
    "ikoyi", "surulere", "yaba", "oshodi",
    "apapa", "festac", "ajah", "ikorodu",
    "epe", "badagry", "agege", "mushin",
    "alimosho", "isolo", "maryland", "ojota",
    "berger", "ogba", "magodo", "gbagada",
    "bariga", "somolu", "shomolu",
}


def normalize_state(raw: str) -> str | None:
    """
    Normalize a raw state string to a canonical Nigerian state name.
    Returns None if no match found.
    """
    cleaned = raw.strip().title()
    if cleaned == "Fct" or cleaned.upper() == "FCT":
        return "FCT"
    for state in NIGERIAN_STATES:
        if state.lower() == cleaned.lower():
            return state
    return None


def is_lagos_location(state: str | None, city: str | None = None) -> bool | None:
    """
    Determine if a location is in Lagos.

    Returns:
        True  — confirmed Lagos
        False — confirmed outside Lagos
        None  — cannot determine (missing/ambiguous data → send to review)
    """
    if not state and not city:
        return None

    # Check state first
    if state:
        normalized = normalize_state(state)
        if normalized == "Lagos":
            return True
        if normalized and normalized != "Lagos":
            return False

    # Fallback: check city/area name against Lagos aliases
    if city and city.strip().lower() in _LAGOS_ALIASES:
        return True

    # Could not determine
    return None


def get_states() -> list[dict[str, object]]:
    """Return all states with is_lagos flag."""
    return [
        {"name": s, "is_lagos": s == "Lagos"}
        for s in NIGERIAN_STATES
    ]


def get_lgas(state: str) -> list[str]:
    """Return LGAs for a given state. Empty list if state not in our data."""
    normalized = normalize_state(state)
    if not normalized:
        return []
    return LGAS_BY_STATE.get(normalized, [])
