#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build English translation of the CBC lab report PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle)
from reportlab.lib.enums import TA_LEFT

OUT = "/root/openclaw/tmp/Gromov_DA_CBC_Report_EN.pdf"

HEADER = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=15,
                        leading=18, spaceAfter=6)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9.5, leading=13,
                     textColor=colors.HexColor("#444444"))
SEC = ParagraphStyle("sec", fontName="Helvetica-Bold", fontSize=10.5,
                     leading=13, spaceBefore=10, spaceAfter=4,
                     textColor=colors.HexColor("#1a4f8b"))
CELL = ParagraphStyle("c", fontName="Helvetica", fontSize=9.5, leading=12)
CELLB = ParagraphStyle("cb", fontName="Helvetica-Bold", fontSize=9.5,
                       leading=12)
NOTE = ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=8.5,
                      leading=11, textColor=colors.HexColor("#666666"))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=16*mm, bottomMargin=16*mm,
                        title="Complete Blood Count — Gromov D.A. (EN)",
                        author="Translated from Russian original")

story = []
story.append(Paragraph("COMPLETE BLOOD COUNT (CBC)", HEADER))
story.append(Paragraph("English translation of the Russian laboratory report"
                       " (ОАК, order № 3304905314). All values are given as in"
                       " the original document.", NOTE))
story.append(Spacer(1, 6))

# --- Patient / order info ---
info = [
    ["Patient:", "GROMOV Dmitry Aleksandrovich",
     "Order №:", "3304905314"],
    ["Date of birth:", "03.04.1986 (39 y.o.)",
     "Sex:", "M"],
    ["Biomaterial:", "Whole blood (EDTA)",
     "Client:", 'LLC "Vida"'],
    ["Registration:", "04.03.2026",
     "Laboratory:", 'LLC "DNKOM"'],
    ["Sample collection:", "04.03.2026 09:47",
     "Payment:", "Card 5%"],
]
t = Table(info, colWidths=[34*mm, 62*mm, 34*mm, 60*mm])
t.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
    ("FONTNAME", (3, 0), (3, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("TOPPADDING", (0, 0), (-1, -1), 1.5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
]))
story.append(t)
story.append(Spacer(1, 4))

# --- Helper to build a section table ---
def section(title, rows):
    story.append(Paragraph(title, SEC))
    data = [[Paragraph("Parameter", CELLB), Paragraph("Result", CELLB),
             Paragraph("Units", CELLB), Paragraph("Reference range", CELLB)]]
    for p, r, u, ref in rows:
        data.append([Paragraph(p, CELL), Paragraph(r, CELL),
                     Paragraph(u, CELL), Paragraph(ref, CELL)])
    tbl = Table(data, colWidths=[88*mm, 26*mm, 26*mm, 50*mm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4d0")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f5f7fa")]),
    ]))
    story.append(tbl)

section("Red blood cell (erythrocyte) parameters", [
    ["Hemoglobin (Hb)", "160.00", "g/L", "138.50 – 166.70"],
    ["Red blood cells (RBC)", "5.19", "×10¹²/L", "4.30 – 5.57"],
    ["Hematocrit (HCT)", "48.00", "%", "39.15 – 51.65"],
    ["Mean corpuscular volume (MCV)", "92.50", "fL", "81.30 – 100.12"],
    ["Mean corpuscular hemoglobin (MCH)", "30.80", "pg", "26.04 – 33.56"],
    ["Red cell distribution width (RDW-CV)", "13.20", "%", "11.22 – 15.56"],
    ["Red cell distribution width (RDW-SD)", "45.40", "fL", "35.26 – 48.70"],
    ["Nucleated red blood cells (NRBC)", "0.00", "×10⁹/L", "0.00 – 0.03"],
    ["Nucleated red blood cells (NRBC)", "0.00", "%", "0.00 – 0.50"],
    ["Mean corpusc. Hb concentration (MCHC)", "333.0", "g/L", "320.0 – 370.0"],
])

section("White blood cell (leukocyte) parameters", [
    ["White blood cells (WBC)", "6.88", "×10⁹/L", "3.89 – 9.23"],
    ["Neutrophils (NEU)", "4.00", "×10⁹/L", "1.78 – 6.04"],
    ["Eosinophils (EOS)", "0.06", "×10⁹/L", "0.04 – 0.58"],
    ["Basophils (BAS)", "0.01", "×10⁹/L", "0.01 – 0.09"],
    ["Monocytes (MON)", "0.63", "×10⁹/L", "0.29 – 0.72"],
    ["Lymphocytes (LYM)", "2.18", "×10⁹/L", "1.39 – 3.15"],
    ["Immature granulocytes (IG)", "0.01", "×10⁹/L", "0.00 – 0.04"],
    ["Neutrophils (NEU)", "58.10", "%", "40.80 – 70.39"],
    ["Eosinophils (EOS)", "0.90", "%", "0.73 – 8.86"],
    ["Basophils (BAS)", "0.20", "%", "0.20 – 1.50"],
    ["Monocytes (MON)", "9.10", "%", "4.17 – 11.37"],
    ["Lymphocytes (LYM)", "31.70", "%", "20.11 – 46.79"],
    ["Immature granulocytes (IG)", "0.10", "%", "0.00 – 0.50"],
])

section("Microscopic examination (manual differential)", [
    ["Band neutrophils", "1", "%", "1 – 5"],
    ["Segmented neutrophils", "57", "%", "40.8 – 70.39"],
    ["Eosinophils", "1", "%", "0.73 – 8.86"],
    ["Basophils", "0", "%", "0.2 – 1.5"],
    ["Monocytes", "9", "%", "4.17 – 11.37"],
    ["Lymphocytes", "32", "%", "20.11 – 46.79"],
])

section("Platelet parameters", [
    ["Platelets (PLT)", "246", "×10⁹/L", "165 – 396.2"],
    ["Thrombocrit (PCT)", "0.29", "%", "0.12 – 0.35"],
    ["Mean platelet volume (MPV)", "11.90", "fL", "9.10 – 12.60"],
    ["Platelet distribution width (PDW)", "14.8", "fL", "9.3 – 16.7"],
    ["Platelet large cell ratio (P-LCR)", "36.20", "%", "17.21 – 46.29"],
])

section("Erythrocyte sedimentation rate (ESR)", [
    ["ESR (Westergren)", "2", "mm/h", "2 – 15"],
])

story.append(Spacer(1, 8))
story.append(Paragraph("Tests performed on: Alifax Test-2; Yenisey F81", CELL))
story.append(Paragraph("Date of testing: 04.03.2026 17:34", CELL))
story.append(Paragraph("Approved by: Kolchenko O. L.", CELL))
story.append(Spacer(1, 6))
story.append(Paragraph("Note: this is an unofficial translation provided for"
                       " reference. The original Russian report remains the"
                       " authoritative document.", NOTE))

doc.build(story)
print("OK:", OUT)
