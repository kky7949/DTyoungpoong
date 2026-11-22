"""Column order and units transcribed from the supplied data dictionary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (
    "Ni_함량_pct", "Co_함량_pct", "Li_함량_pct", "Mn_함량_pct",
    "Cu_불순물_pct", "Fe_불순물_pct", "Al_불순물_pct", "원료투입량_kg",
    "황산투입량_L", "침출온도_C", "침출시간_hr",
)
CHEM = BASE[:7]
PROCESS = BASE[7:]
TARGETS = {"Ni": "Ni_회수율_pct", "Co": "Co_회수율_pct"}
LIMITS = {
    "Ni_함량_pct": (8, 30), "Co_함량_pct": (2, 15), "Li_함량_pct": (2, 6),
    "Mn_함량_pct": (5, 16), "Cu_불순물_pct": (0.3, 6), "Fe_불순물_pct": (0.2, 6),
    "Al_불순물_pct": (0.5, 7), "원료투입량_kg": (80, 200),
    "황산투입량_L": (400, 1500), "침출온도_C": (40, 95), "침출시간_hr": (1, 8),
}
METADATA = ("배치ID", "분석일자", "원료등급")
RAW_COLUMNS = METADATA + BASE + tuple(TARGETS.values())
RAW_SHEET = "원료분석_원본데이터"
DICTIONARY_SHEET = "데이터사전"
DEFAULT_RAW_PATH = ROOT / "data" / "raw" / "youngpoong_raw.xlsx"
UNITS = dict(zip(BASE, ["wt%"] * 7 + ["kg", "L", "deg C", "hr"]))
UNITS.update({target: "%" for target in TARGETS.values()})
PLOT_LABELS = dict(zip(BASE, [
    "Ni content (wt%)", "Co content (wt%)", "Li content (wt%)", "Mn content (wt%)",
    "Cu impurity (wt%)", "Fe impurity (wt%)", "Al impurity (wt%)", "Feed (kg)",
    "Sulfuric acid (L)", "Temperature (deg C)", "Time (hr)",
]))
PLOT_LABELS.update({"Ni_회수율_pct": "Ni recovery (%)", "Co_회수율_pct": "Co recovery (%)"})
