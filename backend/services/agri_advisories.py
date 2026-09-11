"""Curated static agri advisories (Phase 4, D-05/D-06).

Prompt-adjacent data: the agent combines these short agronomy notes with
live ``get_current_weather`` / ``get_weather_forecast`` values quoted from
the tool JSON. Static text only — no secrets, no user data, no network
calls, and no tool registration. Every advisory returned by
:func:`get_advisory` carries the non-IMD qualifier (mirroring the
``tools/imd_client.py`` ``_build_advisory`` wording authority).
"""

from __future__ import annotations

import re

# Qualifier stamped on every advisory (D-02 disclosure wording authority).
_NON_IMD_QUALIFIER = "(non-IMD model data)"

# Canonical crops covered with specific guidance (D-06 open-ended scope:
# anything else falls back to the generic best-effort advisory).
_KNOWN_CROPS = ("paddy", "wheat", "cotton", "sugarcane", "maize", "soybean")

# Season cue -> canonical season. Monsoon reads as kharif; winter as rabi;
# zaid as summer. Any other wording yields no season match (crop default).
_SEASON_ALIASES = {
    "kharif": "kharif",
    "monsoon": "kharif",
    "rabi": "rabi",
    "winter": "rabi",
    "summer": "summer",
    "zaid": "summer",
}

# Crop -> season -> advisory. Each entry is 1-2 lines of plain agronomy.
# "default" covers the crop when no season cue matches.
_ADVISORIES = {
    "paddy": {
        "kharif": (
            "Paddy (kharif): transplant 20-25 day nursery seedlings after "
            "monsoon onset when puddled fields hold 2-5 cm standing water; "
            "pause transplanting during heavy downpour spells and drain "
            "excess water to protect young seedlings "
            "(non-IMD model data)."
        ),
        "default": (
            "Paddy: use levelled puddled fields with 20-25 day seedlings and "
            "shallow standing water; align nursery sowing with expected "
            "monsoon onset and avoid water stagnation at flowering "
            "(non-IMD model data)."
        ),
    },
    "wheat": {
        "rabi": (
            "Wheat (rabi): sow in October-November as night temperatures "
            "fall; give crown-root irrigation about 20-25 days after sowing "
            "and avoid waterlogging in heavy soils (non-IMD model data)."
        ),
        "default": (
            "Wheat: sow at the start of the cool season in well-drained "
            "soil; irrigate at crown-root and flowering stages and pause "
            "field work during unseasonal rain (non-IMD model data)."
        ),
    },
    "cotton": {
        "kharif": (
            "Cotton (kharif): sow with early monsoon showers in well-drained "
            "black soils; ensure field drainage before heavy rain spells and "
            "scout for sucking pests in prolonged humid weather "
            "(non-IMD model data)."
        ),
        "summer": (
            "Cotton (summer): sow only with assured irrigation in deep, "
            "well-drained soils; mulch to hold moisture and irrigate in "
            "evening hours during heat spells (non-IMD model data)."
        ),
        "default": (
            "Cotton: prefer well-drained soils with assured drainage; "
            "balance irrigation with rainfall and watch pests after humid "
            "spells (non-IMD model data)."
        ),
    },
    "sugarcane": {
        "kharif": (
            "Sugarcane (kharif/monsoon planting): plant setts in furrows with "
            "good drainage; earth up the crop before heavy rain and keep "
            "drains clear against waterlogging (non-IMD model data)."
        ),
        "summer": (
            "Sugarcane (summer): trash-mulch the rows and irrigate at "
            "7-10 day intervals in heat; protect young plantings from hot "
            "dry winds with light frequent watering (non-IMD model data)."
        ),
        "default": (
            "Sugarcane: plant healthy setts in well-drained furrows, keep "
            "drains open through the rains, and irrigate through dry spells "
            "to sustain cane growth (non-IMD model data)."
        ),
    },
    "maize": {
        "kharif": (
            "Maize (kharif): sow on ridges with monsoon onset for drainage; "
            "thin to one seedling per hill and top-dress nitrogen when a "
            "dry window follows establishment (non-IMD model data)."
        ),
        "rabi": (
            "Maize (rabi): sow in October-November with assured irrigation; "
            "keep soil moist at tasselling and silking, the stages most "
            "sensitive to moisture stress (non-IMD model data)."
        ),
        "default": (
            "Maize: sow on well-drained ridges, keep the knee-high to "
            "flowering window weed-free, and irrigate through dry spells "
            "(non-IMD model data)."
        ),
    },
    "soybean": {
        "kharif": (
            "Soybean (kharif): sow with monsoon onset in well-drained fields "
            "treated with rhizobium; drain excess water within a day of "
            "heavy rain since seedlings tolerate no waterlogging "
            "(non-IMD model data)."
        ),
        "default": (
            "Soybean: sow early in the rains in well-drained soil, keep "
            "drainage channels open, and harvest promptly when pods mature "
            "before late rain damages grain (non-IMD model data)."
        ),
    },
}

# Best-effort fallback for unknown crops (D-06: never refuse for a missing
# crop; answer from the curated base plus live tool values).
_GENERIC_FALLBACK = (
    "General farm advisory: no crop-specific note is available, so work "
    "best-effort from current conditions — schedule sowing, spraying, and "
    "harvest in dry windows, open field drains before forecast rain, and "
    "irrigate only if no rain is expected in the next few days "
    "(non-IMD model data)."
)


def _normalize(text: object) -> str:
    """Lowercase, trim, and collapse whitespace for cue matching."""
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _detect_crop(text: str) -> str | None:
    """Return the first known crop named in the text, else None."""
    for crop in _KNOWN_CROPS:
        if crop in text:
            return crop
    return None


def _detect_season(text: str) -> str | None:
    """Return the canonical season for the first cue found, else None."""
    for cue, season in _SEASON_ALIASES.items():
        if cue in text:
            return season
    return None


def get_advisory(crop: str = "", season: str = "") -> str:
    """Return a curated advisory for a crop plus an optional season cue.

    Matching is case- and whitespace-insensitive over the combined
    ``crop``/``season`` text, so ``get_advisory("Paddy sowing", "Kharif")``
    and ``get_advisory("paddy", "monsoon")`` both hit the paddy-kharif
    note. Unknown crops (or empty input) yield the generic best-effort
    fallback. The returned string always carries the non-IMD qualifier.
    """
    combined = f"{_normalize(crop)} {_normalize(season)}".strip()
    found_crop = _detect_crop(combined)
    if found_crop is not None:
        variants = _ADVISORIES[found_crop]
        found_season = _detect_season(combined)
        text = variants.get(found_season, variants["default"]) if found_season else variants["default"]
    else:
        text = _GENERIC_FALLBACK
    if "non-imd" not in text.lower():
        text = f"{text} {_NON_IMD_QUALIFIER}"
    return text


# Alias kept for prompt-path import flexibility; same function, same text.
lookup_advisory = get_advisory
