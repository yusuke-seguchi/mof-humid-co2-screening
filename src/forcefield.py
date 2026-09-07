"""RASPA 用力場ディレクトリの生成。

骨格原子: UFF (Rappé et al., JACS 1992) の LJ パラメータ。電荷は CIF の
PACMAN DDEC6 電荷を使う前提（pseudo_atoms.def の charge は 0）。
吸着質: TraPPE (CO2, N2)。分子定義は RASPA 同梱 ExampleDefinitions を使い、
サイト名（C_co2 / O_co2 / N_n2 / N_com）だけ本力場で定義し直す。

換算: eps[K] = D[kcal/mol] * 503.2224, sigma[Å] = x[Å] / 2^(1/6)
（RASPA同梱値 Fe_ 6.54185/2.5943 等と一致することを確認済み）
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config

KCAL_TO_K = 503.2224
R6 = 2 ** (1 / 6)

# UFF: element -> (D [kcal/mol], x [Å]), Rappé 1992 Table 1
UFF = {
    "H": (0.044, 2.886), "B": (0.180, 4.083), "C": (0.105, 3.851),
    "N": (0.069, 3.660), "O": (0.060, 3.500), "F": (0.050, 3.364),
    "Na": (0.030, 2.983), "Mg": (0.111, 3.021), "Al": (0.505, 4.499),
    "Si": (0.402, 4.295), "P": (0.305, 4.147), "S": (0.274, 4.035),
    "Cl": (0.227, 3.947), "K": (0.035, 3.812), "Ca": (0.238, 3.399),
    "Sc": (0.019, 3.295), "Ti": (0.017, 3.175), "V": (0.016, 3.144),
    "Cr": (0.015, 3.023), "Mn": (0.013, 2.961), "Fe": (0.013, 2.912),
    "Co": (0.014, 2.872), "Ni": (0.015, 2.834), "Cu": (0.005, 3.495),
    "Zn": (0.124, 2.763), "Ga": (0.415, 4.383), "Ge": (0.379, 4.280),
    "As": (0.309, 4.230), "Se": (0.291, 4.205), "Br": (0.251, 4.189),
    "Y": (0.072, 3.345), "Zr": (0.069, 3.124), "Nb": (0.059, 3.165),
    "Mo": (0.056, 3.052), "In": (0.599, 4.463), "Sn": (0.567, 4.392),
    "Sb": (0.449, 4.420), "Te": (0.398, 4.470), "I": (0.339, 4.500),
    "La": (0.017, 3.522), "Ce": (0.013, 3.556), "Pr": (0.010, 3.606),
    "Nd": (0.010, 3.575), "Sm": (0.008, 3.532), "Eu": (0.008, 3.514),
    "Gd": (0.009, 3.368), "Tb": (0.007, 3.451), "Dy": (0.007, 3.428),
    "Ho": (0.007, 3.416), "Er": (0.007, 3.402), "Tm": (0.006, 3.349),
    "Yb": (0.228, 3.243), "Lu": (0.041, 3.293), "Hf": (0.072, 3.141),
    "W": (0.067, 3.069),
}

MASS = {
    "H": 1.00794, "B": 10.811, "C": 12.0107, "N": 14.0067, "O": 15.9994,
    "F": 18.9984, "Na": 22.9898, "Mg": 24.305, "Al": 26.9815, "Si": 28.0855,
    "P": 30.9738, "S": 32.065, "Cl": 35.453, "K": 39.0983, "Ca": 40.078,
    "Sc": 44.9559, "Ti": 47.867, "V": 50.9415, "Cr": 51.9961, "Mn": 54.938,
    "Fe": 55.845, "Co": 58.9332, "Ni": 58.6934, "Cu": 63.546, "Zn": 65.38,
    "Ga": 69.723, "Ge": 72.64, "As": 74.9216, "Se": 78.96, "Br": 79.904,
    "Y": 88.9059, "Zr": 91.224, "Nb": 92.9064, "Mo": 95.96, "In": 114.818,
    "Sn": 118.71, "Sb": 121.76, "Te": 127.6, "I": 126.904, "La": 138.905,
    "Ce": 140.116, "Pr": 140.908, "Nd": 144.242, "Sm": 150.36, "Eu": 151.964,
    "Gd": 157.25, "Tb": 158.925, "Dy": 162.5, "Ho": 164.930, "Er": 167.259,
    "Tm": 168.934, "Yb": 173.054, "Lu": 174.967, "Hf": 178.49, "W": 183.84,
}

# TraPPE 吸着質サイト: name -> (eps[K], sigma[Å], charge, mass, print_as)
ADSORBATE_SITES = {
    "C_co2": (27.0, 2.80, 0.700, 12.0107, "C"),
    "O_co2": (79.0, 3.05, -0.350, 15.9994, "O"),
    "N_n2": (36.0, 3.31, -0.482, 14.0067, "N"),
    "N_com": (0.0, 0.0, 0.964, 0.0, "-"),
    "He": (10.9, 2.64, 0.0, 4.0026, "He"),
    "O_h2o": (0.0, 0.0, 0.0, 15.9994, "O"),  # TIP5P-Ew等を使う場合は要更新
}


def write_forcefield(dest: Path | None = None) -> Path:
    dest = dest or (config.PROJECT_ROOT / "simulations" / "forcefield" / "UFFPool")
    dest.mkdir(parents=True, exist_ok=True)

    # --- pseudo_atoms.def ---
    rows = []
    for el, (_, _) in UFF.items():
        rows.append(
            f"{el:<10} yes  {el:<4} {el:<4} 0  {MASS[el]:<10} 0.0  0.0  1.0  1.0  0  0  relative  0"
        )
    for name, (_, _, q, m, pr) in ADSORBATE_SITES.items():
        show = "no" if pr == "-" else "yes"
        rows.append(
            f"{name:<10} {show:<4} {pr:<4} {pr:<4} 0  {m:<10} {q:<8} 0.0  1.0  1.0  0  0  relative  0"
        )
    (dest / "pseudo_atoms.def").write_text(
        "#number of pseudo atoms\n"
        f"{len(rows)}\n"
        "#type print as chem oxidation mass charge polarization B-factor radii "
        "connectivity anisotropic anisotropic-type tinker-type\n"
        + "\n".join(rows) + "\n"
    )

    # --- force_field_mixing_rules.def ---
    lines = []
    for el, (d, x) in UFF.items():
        lines.append(f"{el:<10} lennard-jones  {d * KCAL_TO_K:10.5f} {x / R6:9.5f}")
    for name, (eps, sig, _, _, _) in ADSORBATE_SITES.items():
        if eps > 0:
            lines.append(f"{name:<10} lennard-jones  {eps:10.5f} {sig:9.5f}")
        else:
            lines.append(f"{name:<10} none")
    (dest / "force_field_mixing_rules.def").write_text(
        "# rule: shifted or truncated\nshifted\n"
        "# tail corrections\nno\n"
        "# number of defined interactions\n"
        f"{len(lines)}\n"
        "# type interaction\n" + "\n".join(lines) + "\n"
        "# mixing rule\nLorentz-Berthelot\n"
    )

    # --- force_field.def（個別上書きなし） ---
    (dest / "force_field.def").write_text(
        "# rules to overwrite\n0\n# number of defined interactions\n0\n"
        "# mixing rules to overwrite\n0\n"
    )
    return dest


if __name__ == "__main__":
    print("forcefield written to", write_forcefield())
