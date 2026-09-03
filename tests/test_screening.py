import pandas as pd

from mof_screening import score_candidate, filter_candidates


def test_score_candidate_rank_high_value_candidates():
    row = {
        "mof_id": "MOF-001",
        "surface_area_m2g": 2000,
        "pore_volume_cm3g": 1.2,
        "largest_cavity_angstrom": 12.0,
        "metal_density": 0.3,
        "stability_score": 0.8,
        "synthesizability_score": 0.9,
        "is_activated": True,
    }

    score = score_candidate(row)

    assert score > 0.7


def test_filter_candidates_keeps_promising_and_excludes_unstable():
    df = pd.DataFrame(
        [
            {
                "mof_id": "good",
                "surface_area_m2g": 2200,
                "pore_volume_cm3g": 1.4,
                "largest_cavity_angstrom": 13.0,
                "metal_density": 0.25,
                "stability_score": 0.9,
                "synthesizability_score": 0.8,
                "is_activated": True,
            },
            {
                "mof_id": "bad",
                "surface_area_m2g": 400,
                "pore_volume_cm3g": 0.2,
                "largest_cavity_angstrom": 5.0,
                "metal_density": 0.9,
                "stability_score": 0.2,
                "synthesizability_score": 0.4,
                "is_activated": False,
            },
        ]
    )

    filtered = filter_candidates(df)

    assert filtered["mof_id"].tolist() == ["good"]
