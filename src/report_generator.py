from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.data_loader import REPORTS_DIR, infer_player_team
from src.metrics import batter_strengths_weaknesses, bowler_strengths_weaknesses


def confidence_label(balls: int) -> str:
    if balls >= 300:
        return "High"
    if balls >= 80:
        return "Medium"
    return "Low sample size"


def make_tactical_report(player: str, role: str, deliveries: pd.DataFrame, matchups: pd.DataFrame) -> dict[str, Any]:
    role = role.lower()
    if role.startswith("bat"):
        strengths, weaknesses, plan = batter_strengths_weaknesses(player, deliveries, matchups)
        sample = int((deliveries.get("batter", pd.Series(dtype=str)).astype(str) == player).sum()) if not deliveries.empty and "batter" in deliveries.columns else 0
        title = "Batter Tactical Report"
    else:
        strengths, weaknesses, plan = bowler_strengths_weaknesses(player, deliveries, matchups)
        sample = int((deliveries.get("bowler", pd.Series(dtype=str)).astype(str) == player).sum()) if not deliveries.empty and "bowler" in deliveries.columns else 0
        title = "Bowler Tactical Report"
    return {
        "title": title,
        "player": player,
        "team": infer_player_team(deliveries, player),
        "role": role.title(),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_source": "Processed Cricsheet ball-by-ball deliveries.csv",
        "sample_size": sample,
        "confidence": confidence_label(sample),
        "strengths": strengths,
        "weaknesses": weaknesses,
        "tactical_plan": plan,
        "training_recommendations": _training_from_weaknesses(weaknesses, role),
        "limitations": [
            "Insights are based only on available Cricsheet ball-by-ball data.",
            "Cricsheet does not always provide batting hand, bowling style, shot type, line/length, or field settings.",
            "Coach/analyst review is required before professional selection or tactical decisions.",
        ],
    }


def _training_from_weaknesses(weaknesses: list[str], role: str) -> list[str]:
    text = " ".join(weaknesses).lower()
    recs = []
    if role.startswith("bat"):
        if "dot" in text:
            recs.append("Rotation drill: 30-ball middle-over simulation with one gap-hit target every two balls.")
        if "dismissal" in text:
            recs.append("Dismissal review: tag wicket balls by phase and build a first-20-balls risk plan.")
        if "scoring-rate" in text or "strike" in text:
            recs.append("Tempo drill: boundary option plus safe single option for each bowler type.")
    else:
        if "economy" in text:
            recs.append("Control drill: six-ball sets focused on one-side field and miss-hit zones.")
        if "boundary" in text:
            recs.append("Boundary prevention plan: map release errors and train yorker/length variation under pressure.")
        if "low strike" in text or "wicket" in text:
            recs.append("Wicket-taking plan: field-assisted attacking lengths to each batter type.")
    if not recs:
        recs.append("Maintain role-specific match simulation with performance analyst review after each block.")
    return recs


def export_report_pdf(report: dict[str, Any], output_path: Path | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_player = "".join(c for c in report["player"] if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    if output_path is None:
        output_path = REPORTS_DIR / f"{safe_player}_{report['role']}_tactical_report.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=1.3*cm, leftMargin=1.3*cm, topMargin=1.2*cm, bottomMargin=1.2*cm)
    story = []
    story.append(Paragraph(f"<b>{report['title']}</b>", styles["Title"]))
    story.append(Paragraph(f"Player: <b>{report['player']}</b> | Role: {report['role']} | Team: {report.get('team','')}", styles["Normal"]))
    story.append(Paragraph(f"Generated: {report['generated_at']} | Data source: {report['data_source']}", styles["Normal"]))
    story.append(Spacer(1, 10))
    info = [["Sample size", str(report["sample_size"])], ["Confidence", report["confidence"]]]
    table = Table(info, colWidths=[5*cm, 10*cm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0b3d24")), ("TEXTCOLOR", (0,0), (-1,-1), colors.black), ("GRID", (0,0), (-1,-1), .5, colors.grey)]))
    story.append(table)
    for heading, key in [
        ("Top Strengths", "strengths"),
        ("Top Weaknesses", "weaknesses"),
        ("Tactical Plan", "tactical_plan"),
        ("Training Recommendations", "training_recommendations"),
        ("Limitations", "limitations"),
    ]:
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"<b>{heading}</b>", styles["Heading2"]))
        for item in report.get(key, []):
            story.append(Paragraph(f"• {item}", styles["Normal"]))
    doc.build(story)
    return output_path
