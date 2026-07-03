"""
PDF Report Generator for CCMT Admission Predictor
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from datetime import datetime
from pypdf import PdfReader, PdfWriter
import pandas as pd


BRAND_BLUE   = colors.HexColor("#1a237e")
BRAND_LIGHT  = colors.HexColor("#3949ab")
SAFE_GREEN   = colors.HexColor("#2e7d32")
MODERATE_ORG = colors.HexColor("#e65100")
DREAM_RED    = colors.HexColor("#b71c1c")
ROW_ALT      = colors.HexColor("#e8eaf6")
HEADER_BG    = colors.HexColor("#1a237e")


def _chance_color(chance: str) -> colors.Color:
    if "Extremely Safe" in chance or "Very Safe" in chance:
        return SAFE_GREEN
    if "Safe" in chance:
        return colors.HexColor("#1b5e20")
    if "Moderate" in chance:
        return MODERATE_ORG
    return DREAM_RED


def generate_pdf(
    gate_score: float,
    gate_paper: str,
    category: str,
    round_name: str,
    result_df,
    password: str,
) -> bytes:
    """Generate a professional PDF report and return as bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=20, textColor=colors.white, alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#c5cae9"),
        alignment=TA_CENTER, spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=13, textColor=BRAND_BLUE, spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#212121"),
    )
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
    )

    story = []

    # ── Header Banner ─────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("🎓  CCMT Admission Predictor", title_style),
    ]]
    header_table = Table(header_data, colWidths=[17.7 * cm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_BLUE),
        ("TOPPADDING", (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", [8]),
    ]))
    story.append(header_table)

    sub_data = [[
        Paragraph("Centralised Counselling for M.Tech/M.Arch/M.Plan — 2024 & 2025 Data", subtitle_style),
    ]]
    sub_table = Table(sub_data, colWidths=[17.7 * cm])
    sub_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Student Details ───────────────────────────────────────────────────────
    story.append(Paragraph("📋  Student Details", section_style))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_LIGHT))
    story.append(Spacer(1, 0.2 * cm))

    # Format the round name for display
    display_round = round_name
    if "Special Round" in round_name:
        display_round = "Special Round"
        
    details = [
        ["GATE Score", str(gate_score), "GATE Paper", gate_paper.split(" - ")[0]],
        ["Category",   category,         "Round",      display_round],
        ["Report Date", datetime.now().strftime("%d %b %Y, %H:%M"), "Total Colleges", str(len(result_df))],
    ]
    det_table = Table(details, colWidths=[4 * cm, 5 * cm, 4 * cm, 4.7 * cm])
    det_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (0, -1), ROW_ALT),
        ("BACKGROUND",  (2, 0), (2, -1), ROW_ALT),
        ("FONTNAME",    (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (2, 0), (2, -1), "Helvetica-Bold"),
        ("TOPPADDING",  (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#9fa8da")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    story.append(det_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Recommendations Table ─────────────────────────────────────────────────
    story.append(Paragraph("🏛️  Top College Recommendations", section_style))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_LIGHT))
    story.append(Spacer(1, 0.2 * cm))

    short_round = display_round.replace("Round ", "R").replace("Special Round", "SR").replace("National Spot Round", "NSR")
    col_headers = ["#", "Institute", "Program", f"2025 ({short_round})", f"2024 ({short_round})", "Prob %", "Chance"]
    table_data = [col_headers]

    for rank, row in result_df.iterrows():
        chance_str = str(row.get("Chance", ""))
        # Strip emoji for PDF
        clean_chance = chance_str.replace("🟢", "").replace("🟡", "").replace(
            "🟠", "").replace("🔴", "").strip()

        inst = str(row.get("Institute", ""))
        # Shorten long institute names
        if len(inst) > 45:
            inst = inst[:42] + "..."
        prog = str(row.get("Program", ""))
        if len(prog) > 35:
            prog = prog[:32] + "..."

        table_data.append([
            str(rank),
            inst,
            prog,
            str(row.get("Close_2025")) if pd.notna(row.get("Close_2025")) else "N/A",
            str(row.get("Close_2024")) if pd.notna(row.get("Close_2024")) else "N/A",
            f"{row.get('Probability', 0)}%",
            clean_chance,
        ])

    col_widths = [0.7*cm, 5.8*cm, 4.2*cm, 1.7*cm, 1.7*cm, 1.5*cm, 2.1*cm]
    rec_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    ts = [
        ("BACKGROUND",   (0, 0), (-1, 0),  HEADER_BG),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  9),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LEFTPADDING",  (0, 0), (-1, -1), 5),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#9fa8da")),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, ROW_ALT]),
        ("ALIGN",        (0, 0), (0, -1),  "CENTER"),
        ("ALIGN",        (3, 0), (5, -1),  "CENTER"),
    ]
    # Color the chance column per row
    for i, row in enumerate(table_data[1:], start=1):
        chance_text = row[6]
        if "Extremely" in chance_text or "Very Safe" in chance_text:
            c = colors.HexColor("#e8f5e9")
        elif "Safe" in chance_text:
            c = colors.HexColor("#f1f8e9")
        elif "Moderate" in chance_text:
            c = colors.HexColor("#fff8e1")
        else:
            c = colors.HexColor("#ffebee")
        ts.append(("BACKGROUND", (6, i), (6, i), c))

    rec_table.setStyle(TableStyle(ts))
    story.append(rec_table)
    story.append(Spacer(1, 0.6 * cm))

    # ── Legend ────────────────────────────────────────────────────────────────
    story.append(Paragraph("📊  Chance Classification", section_style))
    legend_data = [
        ["Extremely Safe", "Score ≥ Cutoff + 40"],
        ["Very Safe",      "Score ≥ Cutoff + 20"],
        ["Safe",           "Score ≥ Cutoff + 5"],
        ["Moderate",       "Score within ±5 of Cutoff"],
        ["Dream",          "Score < Cutoff − 5"],
    ]
    leg_colors = [
        colors.HexColor("#e8f5e9"),
        colors.HexColor("#f1f8e9"),
        colors.HexColor("#fffde7"),
        colors.HexColor("#fff3e0"),
        colors.HexColor("#ffebee"),
    ]
    leg_table = Table(legend_data, colWidths=[4*cm, 8*cm])
    leg_ts = [
        ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("FONTNAME",  (0, 0), (0, -1),  "Helvetica-Bold"),
        ("TOPPADDING",(0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",(0,0),(-1,-1),8),
        ("GRID",      (0, 0), (-1, -1), 0.4, colors.lightgrey),
    ]
    for i, bg in enumerate(leg_colors):
        leg_ts.append(("BACKGROUND", (0, i), (-1, i), bg))
    leg_table.setStyle(TableStyle(leg_ts))
    story.append(leg_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Disclaimer ────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "⚠️  Disclaimer: This report is based on historical CCMT 2024 & 2025 cutoff data. "
        "Predictions are indicative only. Actual cutoffs may vary. Always verify on the official "
        "CCMT portal: <b>ccmt.nic.in</b>.",
        ParagraphStyle("Disc", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))


    doc.build(story)
    
    # Encrypt the PDF
    buffer.seek(0)
    reader = PdfReader(buffer)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)
        
    writer.encrypt(password)
    
    encrypted_buffer = io.BytesIO()
    writer.write(encrypted_buffer)
    
    return encrypted_buffer.getvalue()
