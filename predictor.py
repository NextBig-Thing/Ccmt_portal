"""
CCMT Admission Predictor — Core Engine
Loads 2024 & 2025 CCMT Master_Data, computes weighted admission probability.
"""

import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# ─── GATE Paper → Program keyword mapping ────────────────────────────────────
# STRICTLY based on CCMT eligibility — each paper can only apply to its domain.
# CS paper holders CANNOT apply to VLSI, Embedded, Signal Processing (those need EC).
GATE_PAPER_PROGRAMS = {
    "CS - Computer Science & Information Technology": [
        "computer science", "information technology", "information security",
        "cyber security", "cyber forensics", "data science", "data analytics",
        "data engineering", "artificial intelligence", "machine learning",
        "software engineering", "software technology", "internet of things",
        "quantum computing", "autonomous systems", "information and cyber",
        "advanced computing", "high performance computing", "cloud computing",
        "distributed computing", "human computer", "computer vision",
        "natural language", "blockchain", "wireless networks and computing",
        "computing", "network security", "computer network",
    ],
    "DA - Data Science & Artificial Intelligence": [
        "data science", "artificial intelligence", "machine learning",
        "data analytics", "data engineering", "business analytics",
        "autonomous systems", "deep learning", "ai and data",
    ],
    "EC - Electronics & Communication Engineering": [
        "electronics", "communication", "vlsi", "embedded", "signal processing",
        "radar", "microwave", "rf ", "photonics", "wireless", "ic design",
        "nanoelectronics", "microelectronics", "optical", "antenna",
    ],
    "EE - Electrical Engineering": [
        "electrical", "power system", "power electronics", "control system",
        "drives", "energy systems", "smart grid", "electric vehicle",
        "high voltage", "traction",
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

# ─── NIRF 2024 Engineering Rankings ─────────────────────────────────────────
# Source: NIRF India Rankings 2024 (Engineering)
# Key: substring that appears in the institute name (lowercase)
# Value: NIRF rank
NIRF_RANKINGS = {
    # Top NITs
    "national institute of technology, tiruchirappalli": 10,
    "nit tiruchirappalli": 10,
    "national institute of technology, warangal": 26,
    "nit warangal": 26,
    "national institute of technology karnataka": 27,
    "nit surathkal": 27,
    "national institute of technology, calicut": 28,
    "nit calicut": 28,
    "national institute of technology, rourkela": 29,
    "nit rourkela": 29,
    "visvesvaraya national institute of technology": 33,
    "vnit nagpur": 33,
    "sardar vallabhbhai national institute of technology": 36,
    "svnit surat": 36,
    "malaviya national institute of technology": 38,
    "mnit jaipur": 38,
    "motilal nehru national institute of technology": 43,
    "mnnit allahabad": 43,
    "dr. b r ambedkar national institute of technology": 46,
    "nit jalandhar": 46,
    "national institute of technology, hamirpur": 52,
    "nit hamirpur": 52,
    "national institute of technology, jamshedpur": 54,
    "nit jamshedpur": 54,
    "maulana azad national institute of technology": 51,
    "manit bhopal": 51,
    "national institute of technology, kurukshetra": 63,
    "nit kurukshetra": 63,
    "national institute of technology, durgapur": 59,
    "nit durgapur": 59,
    "national institute of technology, silchar": 75,
    "nit silchar": 75,
    "national institute of technology, raipur": 84,
    "nit raipur": 84,
    "national institute of technology, patna": 88,
    "nit patna": 88,
    "national institute of technology delhi": 77,
    "nit delhi": 77,
    "national institute of technology, agartala": 101,
    "nit agartala": 101,
    "national institute of technology, srinagar": 110,
    "nit srinagar": 110,
    "national institute of technology, manipur": 130,
    "national institute of technology, meghalaya": 135,
    "national institute of technology, mizoram": 140,
    "national institute of technology, nagaland": 145,
    "national institute of technology, sikkim": 148,
    "national institute of technology, uttarakhand": 150,
    "national institute of technology, andhra pradesh": 120,
    "national institute of technology, arunachal pradesh": 138,
    "national institute of technology, goa": 105,
    "national institute of technology, puducherry": 115,
    # IIITs
    "international institute of information technology, hyderabad": 31,
    "iiit hyderabad": 31,
    "international institute of information technology bangalore": 68,
    "iiit bangalore": 68,
    "indraprastha institute of information technology": 52,
    "iiit delhi": 52,
    "atal bihari vajpayee indian institute of information technology": 82,
    "abv-iiitm gwalior": 82,
    "indian institute of information technology, design and manufacturing, jabalpur": 90,
    "iiitdm jabalpur": 90,
    "indian institute of information technology design and manufacturing kancheepuram": 95,
    "iiitdm kancheepuram": 95,
    "indian institute of information technology, allahabad": 60,
    "iiit allahabad": 60,
    "indian institute of information technology, sri city": 100,
    "indian institute of information technology, vadodara": 98,
    "indian institute of information technology, lucknow": 105,
    "indian institute of information technology, dharwad": 108,
    "indian institute of information technology, kota": 112,
    "indian institute of information technology, ranchi": 115,
    "indian institute of information technology, nagpur": 118,
    "indian institute of information technology, tiruchirappalli": 120,
    "indian institute of information technology, manipur": 130,
}

# ─── Score gap cap (don't recommend colleges this far below user's score) ────
MAX_GAP = 150  # If user score - closing score > MAX_GAP, exclude the college


def _get_nirf_bonus(institute_name: str) -> float:
    """
    Return NIRF bonus points based on institute NIRF 2024 Engineering rank.
    Lower rank = higher bonus.
    """
    name_lower = institute_name.lower().strip()

    # Try exact substring match against known institutes
    nirf_rank = None
    for key, rank in NIRF_RANKINGS.items():
        if key in name_lower or name_lower in key:
            nirf_rank = rank
            break

    # If not found by name, try keyword detection
    if nirf_rank is None:
        if "national institute of technology" in name_lower or " nit " in name_lower:
            nirf_rank = 155  # unranked NIT default
        elif "indian institute of information technology" in name_lower or "iiit" in name_lower:
            nirf_rank = 125  # unranked IIIT default

    if nirf_rank is None:
        # GFTI or others
        if any(kw in name_lower for kw in ["iit", "iiser", "iisc", "bits"]):
            return 18.0
        if any(kw in name_lower for kw in ["central university", "central institute",
                                             "school of planning", "nifft", "nifm",
                                             "defence institute", "diat"]):
            return 3.0
        return 1.0  # Other GFTI/smaller institutes

    # Convert rank to bonus
    if nirf_rank <= 25:
        return 20.0
    elif nirf_rank <= 50:
        return 15.0
    elif nirf_rank <= 75:
        return 10.0
    elif nirf_rank <= 100:
        return 7.0
    elif nirf_rank <= 125:
        return 5.0
    elif nirf_rank <= 150:
        return 4.0
    else:
        return 3.0  # unranked NIT/IIIT still gets a base bonus


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


def get_gate_papers() -> list[str]:
    return list(GATE_PAPER_PROGRAMS.keys())


# ─── Per-paper exclusion keywords ────────────────────────────────────────────
# If a program name contains ANY of these words it is EXCLUDED for that paper,
# even if it partially matched an inclusion keyword.
PAPER_EXCLUSIONS = {
    "CS": [
        "signal processing", "embedded", "electronics and communication",
        "vlsi", "ic design", "microelectronics", "nanoelectronics",
        "microwave", "radar", "rf and", "photonics", "antenna",
        "optical communication", "power system", "power electronics",
        "electrical", "thermal", "mechanical", "manufacturing",
        "civil", "structural", "transportation", "geotechnical",
        "chemical", "petroleum", "textile", "mining",
    ],
    "DA": [
        "signal processing", "embedded", "electronics and communication",
        "vlsi", "ic design", "microelectronics", "nanoelectronics",
        "microwave", "radar", "photonics", "antenna",
        "optical communication", "power system", "power electronics",
        "electrical", "thermal", "mechanical", "manufacturing",
        "civil", "structural", "transportation", "geotechnical",
        "chemical", "petroleum", "textile", "mining",
    ],
    "EC": [
        "computer science", "information technology", "information security",
        "cyber security", "software engineering", "software technology",
        "power system", "power electronics", "high voltage", "traction",
        "thermal", "mechanical", "manufacturing", "civil", "structural",
        "transportation", "geotechnical", "chemical", "petroleum",
        "textile", "mining",
    ],
    "EE": [
        "computer science", "information technology", "information security",
        "cyber security", "software engineering", "vlsi", "embedded",
        "signal processing", "electronics and communication",
        "microelectronics", "thermal", "mechanical", "manufacturing",
        "civil", "structural", "transportation", "geotechnical",
        "chemical", "petroleum", "textile", "mining",
    ],
    "ME": [
        "computer science", "information technology", "cyber security",
        "software engineering", "vlsi", "embedded", "signal processing",
        "electronics and communication", "microelectronics",
        "power system", "high voltage", "civil", "structural",
        "transportation", "geotechnical", "chemical", "petroleum",
        "textile", "mining",
    ],
    "CE": [
        "computer science", "information technology", "cyber security",
        "software engineering", "vlsi", "embedded", "signal processing",
        "electronics and communication", "microelectronics",
        "power system", "high voltage", "thermal", "mechanical",
        "manufacturing", "chemical", "petroleum", "textile", "mining",
    ],
    "CH": [
        "computer science", "information technology", "cyber security",
        "software engineering", "vlsi", "embedded", "signal processing",
        "electronics and communication", "power system", "high voltage",
        "thermal", "mechanical", "manufacturing", "civil", "structural",
        "transportation", "textile", "mining",
    ],
    "IN": [
        "computer science", "information technology", "cyber security",
        "software engineering", "vlsi", "electronics and communication",
        "power system", "thermal", "mechanical", "manufacturing",
        "civil", "structural", "chemical", "textile", "mining",
    ],
    "BT": [
        "computer science", "information technology", "cyber security",
        "software engineering", "vlsi", "embedded", "signal processing",
        "electronics and communication", "power system", "thermal",
        "mechanical", "manufacturing", "civil", "structural", "chemical",
        "textile", "mining",
    ],
}


def get_programs_for_paper(paper: str, df: pd.DataFrame) -> list[str]:
    """
    Return distinct program names that match the chosen GATE paper.
    Applies strict domain exclusion for every paper so cross-domain
    programs never appear (e.g. VLSI never shows for CS paper).
    """
    keywords = GATE_PAPER_PROGRAMS.get(paper, [])
    if not keywords:
        return sorted(df["Program"].dropna().unique().tolist())

    mask = df["Program_lower"].apply(
        lambda p: any(kw in p for kw in keywords)
    )
    matched_df = df.loc[mask, "Program"].dropna().unique().tolist()

    # Apply per-paper exclusion list
    paper_code = paper.split(" - ")[0].strip()  # e.g. "CS", "EC", "EE"
    exclusions = PAPER_EXCLUSIONS.get(paper_code, [])
    if exclusions:
        matched_df = [
            p for p in matched_df
            if not any(ex in p.lower() for ex in exclusions)
        ]

    return sorted(matched_df) if matched_df else sorted(df["Program"].dropna().unique().tolist())


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

    # Closing scores → clean integers (no .000000)
    for col in ["Close_2025", "Close_2024"]:
        if col in result.columns:
            result[col] = pd.to_numeric(result[col], errors="coerce").round(0)

    # Probabilities and scores → 1dp floats
    for col in ["Weighted_Close", "Probability"]:
        if col in result.columns:
            result[col] = result[col].apply(
                lambda x: round(float(x), 1) if pd.notna(x) else float("nan")
            )

    return result
