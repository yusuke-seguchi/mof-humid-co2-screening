from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def _normalize(value: float | int | None, low: float, high: float) -> float:
    if value is None or pd.isna(value):
        return 0.0
    if high <= low:
        return 0.0
    return float(np.clip((value - low) / (high - low), 0.0, 1.0))


def score_candidate(row: dict[str, Any]) -> float:
    """Return a single screening score between 0 and 1.

    The score combines adsorption-relevant structural descriptors with synthesis and
    stability considerations. Higher is more promising for MOF screening.
    """
    surface_area = float(row.get("surface_area_m2g", 0.0) or 0.0)
    pore_volume = float(row.get("pore_volume_cm3g", 0.0) or 0.0)
    cavity = float(row.get("largest_cavity_angstrom", 0.0) or 0.0)
    metal_density = float(row.get("metal_density", 0.0) or 0.0)
    stability = float(row.get("stability_score", 0.0) or 0.0)
    synthesizability = float(row.get("synthesizability_score", 0.0) or 0.0)
    is_activated = bool(row.get("is_activated", False))

    area_score = _normalize(surface_area, 500.0, 3000.0)
    volume_score = _normalize(pore_volume, 0.3, 2.0)
    cavity_score = _normalize(cavity, 5.0, 20.0)
    density_score = 1.0 - _normalize(metal_density, 0.0, 1.0)
    stability_score = np.clip(stability, 0.0, 1.0)
    synth_score = np.clip(synthesizability, 0.0, 1.0)

    base = 0.30 * area_score + 0.20 * volume_score + 0.15 * cavity_score
    practical = 0.20 * density_score + 0.10 * stability_score + 0.05 * synth_score
    activity_bonus = 0.10 if is_activated else 0.0

    return float(np.clip(base + practical + activity_bonus, 0.0, 1.0))


def filter_candidates(df: pd.DataFrame, min_score: float = 0.6) -> pd.DataFrame:
    """Filter a MOF table and keep candidates that look promising.

    Candidates are scored with `score_candidate` and filtered using a minimum score,
    stability, synethsizability, and activity requirements.
    """
    working = df.copy()
    working["screening_score"] = working.apply(score_candidate, axis=1)

    filtered = working[
        (working["screening_score"] >= min_score)
        & (working.get("stability_score", 0.0).fillna(0.0) >= 0.5)
        & (working.get("synthesizability_score", 0.0).fillna(0.0) >= 0.5)
        & (working.get("is_activated", False).fillna(False) == True)
    ].copy()

    return filtered.sort_values("screening_score", ascending=False).reset_index(drop=True)
