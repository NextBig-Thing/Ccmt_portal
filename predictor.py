"""
CCMT Admission Predictor — Core Engine
Loads 2024 & 2025 CCMT Master_Data, computes weighted admission probability.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ─── GATE Paper → Program keyword mapping ────────────────────────────────────
GATE_PAPER_PROGRAMS = {
    "CS - Computer Science & Information Technology": [
        "computer science", "information technology", "information security",
        "cyber security", "data science", "data analytics", "data engineering",
        "artificial intelligence", "machine learning", "software engineering",
        "software technology", "network", "internet of things", "iot",
        "quantum computing", "ic design", "vlsi", "embedded",
        "wireless", "autonomous systems", "information and cyber",
        "computing", "human computer", "bioinformatics",
    ],
    "DA - Data Science & Artificial Intelligence": [
        "data science", "artificial intelligence", "machine learning",
        "data analytics", "data engineering", "business analytics",
        "autonomous systems", "deep learning",
    ],
    "EC - Electronics & Communication Engineering": [
        "electronics", "communication", "vlsi", "embedded", "signal processing",
        "radar", "microwave", "rf", "photonics", "wireless", "ic design",
    ],
    "EE - Electrical Engineering": [
        "electrical", "power", "power electronics", "control", "drives",
        "energy systems", "smart grid", "electric vehicle",
    ],
    "ME - Mechanical Engineering": [
        "mechanical", "thermal", "manufacturing", "production", "design engineering",
        "cad", "robotics", "automation", "industrial", "aerospace",
        "automobile", "material", "nanotechnology", "modeling and simulation",
    ],
    "CE - Civil Engineering": [
        "civil", "structural", "transportation", "geotechnical", "environmental",
        "water resources", "construction", "urban",
    ],
    "CH - Chemical Engineering": [
        "chemical", "petroleum", "polymer", "process", "green technology",
    ],
    "IN - Instrumentation Engineering": [
        "instrumentation", "control", "measurement",
    ],
    "BT - Biotechnology": [
        "biotechnology", "biomedical", "bioinformatics", "biochemical",
    ],
    "XE - Engineering Sciences": [
        "engineering sciences", "fluid mechanics", "materials science",
    ],
    "PI - Production and Industrial Engineering": [
        "production", "industrial", "manufacturing", "quality",
    ],
    "MN - Mining Engineering": [
        "mining", "mineral",
    ],
    "MA - Mathematics": [
        "mathematics", "applied mathematics",
    ],
    "PH - Physics": [
        "physics", "photonics", "optics",
    ],
    "CY - Chemistry": [
        "chemistry", "chemical sciences",
    ],
    "TF - Textile Engineering and Fibre Science": [
        "textile", "fibre",
    ],
    "AR - Architecture and Planning": [
        "architecture", "planning", "urban",
    ],
    "GE - Geomatics Engineering": [
        "geomatics", "geo-informatics",
    ],
    "ES - Environmental Science & Engineering": [
        "environmental", "ecology",
    ],
    "AG - Agricultural Engineering": [
        "agricultural", "agriculture",
    ],
    "NM - Naval Architecture and Marine Engineering": [
        "naval", "marine",
    ],
    "TT - Textile Technology": [
        "textile technology",
    ],
    "GG - Geology and Geophysics": [
        "geology", "geophysics",
    ],
    "EY - Ecology and Evolution": [
        "ecology", "evolution",
    ],
    "PE - Petroleum Engineering": [
        "petroleum",
    ],
    "AE - Aerospace Engineering": [
        "aerospace", "aeronautical",
    ],
}

CHANCE_LABELS = {
    (40, 10000): ("🟢 Extremely Safe", "#00c853"),
    (20,    40): ("🟢 Very Safe",      "#43a047"),
    ( 5,    20): ("🟡 Safe",           "#f9a825"),
    (-5,     5): ("🟠 Moderate",       "#fb8c00"),
    (-10000, -5): ("🔴 Dream",         "#e53935"),
}


# We need a real cache — resolve at module import time when streamlit is available
try:
    import streamlit as st
    st_cache = st.cache_data
except ImportError:
    st_cache = lambda f: f  # noqa: E731

@st_cache
def load_data() -> pd.DataFrame:
    """Load and merge 2024 + 2025 Master_Data sheets."""
    dfs = []
    for year, fname in [(2024, "CCMT_2024_All_Data.xlsx"), (2025, "CCMT_2025_All_Data.xlsx")]:
        path = DATA_DIR / fname
        if path.exists():
            df = pd.read_excel(path, sheet_name="Master_Data")
            df["Year"] = year
            dfs.append(df)
    if not dfs:
        raise FileNotFoundError("No CCMT data files found in data/ folder.")
    combined = pd.concat(dfs, ignore_index=True)
    combined["Closing_Score"] = pd.to_numeric(combined["Closing_Score"], errors="coerce")
    combined["Opening_Score"] = pd.to_numeric(combined["Opening_Score"], errors="coerce")
    combined["Program_lower"] = combined["Program"].str.lower().fillna("")
    return combined


def _st_cache_wrapper(fn):
    """Lazy import of streamlit.cache_data to avoid import-time dependency."""
    try:
        import streamlit as st
        return st.cache_data(fn)
    except ImportError:
        return fn


# We need a real cache — resolve at module import time when streamlit is available
try:
    import streamlit as st
    st_cache = st.cache_data
except ImportError:
    st_cache = lambda f: f  # noqa: E731


def get_gate_papers() -> list[str]:
    return list(GATE_PAPER_PROGRAMS.keys())


def get_programs_for_paper(paper: str, df: pd.DataFrame) -> list[str]:
    """Return distinct program names that match the chosen GATE paper."""
    keywords = GATE_PAPER_PROGRAMS.get(paper, [])
    if not keywords:
        return sorted(df["Program"].dropna().unique().tolist())
    mask = df["Program_lower"].apply(
        lambda p: any(kw in p for kw in keywords)
    )
    matched = df.loc[mask, "Program"].dropna().unique().tolist()
    return sorted(matched) if matched else sorted(df["Program"].dropna().unique().tolist())


def get_categories(df: pd.DataFrame) -> list[str]:
    priority = ["OPEN", "OBC-NCL", "EWS", "SC", "ST",
                "OPEN-PwD", "OBC-NCL-PwD", "EWS-PwD", "SC-PwD"]
    existing = df["Category"].dropna().unique().tolist()
    ordered = [c for c in priority if c in existing]
    ordered += [c for c in existing if c not in ordered]
    return ordered


def get_rounds(df: pd.DataFrame) -> list[str]:
    order = ["Round 1", "Round 2", "Round 3",
             "Special Round 1", "Special Round 2", "National Spot Round"]
    existing = df["Round"].dropna().unique().tolist()
    ordered = [r for r in order if r in existing]
    ordered += [r for r in existing if r not in ordered]
    return ordered


def _round_weight(round_name: str) -> float:
    weights = {
        "Round 3": 1.0,
        "Special Round 2": 0.95,
        "Special Round 1": 0.90,
        "National Spot Round": 0.85,
        "Round 2": 0.80,
        "Round 1": 0.70,
    }
    return weights.get(round_name, 0.75)


def get_chance_label(diff: float):
    for (lo, hi), (label, color) in CHANCE_LABELS.items():
        if lo <= diff < hi:
            return label, color
    return ("🔴 Dream", "#e53935")


def compute_probability(diff: float) -> float:
    """Map score difference to 0–100 probability."""
    # Sigmoid-like mapping: diff=0 → ~50%, diff=40 → ~95%, diff=-20 → ~10%
    prob = 100 / (1 + np.exp(-0.1 * diff))
    return round(float(np.clip(prob, 1, 99)), 1)


def predict(
    gate_score: float,
    gate_paper: str,
    category: str,
    round_name: str,
    selected_programs: list[str],
    df: pd.DataFrame,
    top_n: int = 25,
) -> pd.DataFrame:
    """
    Returns top_n college recommendations sorted by Admission Probability.
    """
    # ── Filter by category & round ─────────────────────────────────────────
    filtered = df[
        (df["Category"] == category) &
        (df["Round"] == round_name)
    ].copy()

    # ── Filter by selected programs ─────────────────────────────────────────
    if selected_programs:
        filtered = filtered[filtered["Program"].isin(selected_programs)]

    if filtered.empty:
        # Fallback: relax round filter
        filtered = df[df["Category"] == category].copy()
        if selected_programs:
            filtered = filtered[filtered["Program"].isin(selected_programs)]

    if filtered.empty:
        return pd.DataFrame()

    # ── Pivot: one row per Institute+Program, columns = year closing scores ─
    pivot = filtered.pivot_table(
        index=["Institute", "Program"],
        columns="Year",
        values="Closing_Score",
        aggfunc="min",   # use best (lowest) closing score per combo
    ).reset_index()
    pivot.columns.name = None

    has_2024 = 2024 in pivot.columns
    has_2025 = 2025 in pivot.columns

    if has_2024:
        pivot.rename(columns={2024: "Close_2024"}, inplace=True)
    else:
        pivot["Close_2024"] = np.nan

    if has_2025:
        pivot.rename(columns={2025: "Close_2025"}, inplace=True)
    else:
        pivot["Close_2025"] = np.nan

    # ── Weighted closing score (2025 = 60%, 2024 = 40%) ─────────────────────
    w25, w24 = 0.60, 0.40

    def weighted_close(row):
        v25, v24 = row.get("Close_2025"), row.get("Close_2024")
        v25 = float(v25) if pd.notna(v25) else None
        v24 = float(v24) if pd.notna(v24) else None
        if v25 is not None and v24 is not None:
            return w25 * v25 + w24 * v24
        return v25 if v25 is not None else (v24 if v24 is not None else np.nan)

    pivot["Weighted_Close"] = pivot.apply(weighted_close, axis=1)
    pivot.dropna(subset=["Weighted_Close"], inplace=True)

    if pivot.empty:
        return pd.DataFrame()

    # ── Round weight multiplier ───────────────────────────────────────────────
    rw = _round_weight(round_name)

    # ── Score difference and probability ─────────────────────────────────────
    pivot["Score_Diff"] = gate_score - pivot["Weighted_Close"]
    pivot["Score_Diff"] = pivot["Score_Diff"] * rw  # dampen by round
    pivot["Probability"] = pivot["Score_Diff"].apply(compute_probability)

    # ── Trend bonus: if 2025 cutoff < 2024, trend is falling → safer ─────────
    def trend_bonus(row):
        v25 = row.get("Close_2025")
        v24 = row.get("Close_2024")
        if pd.notna(v25) and pd.notna(v24):
            diff = float(v24) - float(v25)  # positive if cutoff dropped (easier)
            return min(diff * 0.05, 5.0)   # cap bonus at +5%
        return 0.0

    pivot["Trend_Bonus"] = pivot.apply(trend_bonus, axis=1)
    pivot["Probability"] = (pivot["Probability"] + pivot["Trend_Bonus"]).clip(1, 99).round(1)

    # ── Admission chance label ────────────────────────────────────────────────
    pivot[["Chance", "Color"]] = pivot["Score_Diff"].apply(
        lambda d: pd.Series(get_chance_label(d))
    )

    # ── Sort & return top_n ───────────────────────────────────────────────────
    result = pivot.sort_values("Probability", ascending=False).head(top_n).reset_index(drop=True)
    result.index = result.index + 1  # 1-based rank

    # Round display values
    for col in ["Close_2025", "Close_2024", "Weighted_Close", "Probability"]:
        if col in result.columns:
            result[col] = result[col].apply(lambda x: round(float(x), 1) if pd.notna(x) else np.nan)

    return result
