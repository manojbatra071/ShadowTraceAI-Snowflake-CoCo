from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "ShadowTraceAI-Application-Functionality-Guide.docx"

NAVY = "102A43"
INK = "243B53"
MUTED = "627D98"
TEAL = "0F766E"
BLUE = "2E74B5"
LIGHT_BLUE = "E8EEF5"
LIGHT_TEAL = "ECFDF8"
LIGHT_GRAY = "F4F6F9"
MID_GRAY = "D8E1EA"
RED = "B42318"
LIGHT_RED = "FFF3F2"
WHITE = "FFFFFF"

CONTENT_WIDTH_DXA = 9360
TABLE_INDENT_DXA = 120


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_geometry(table, widths_dxa: list[int]) -> None:
    if sum(widths_dxa) != CONTENT_WIDTH_DXA:
        raise ValueError(f"Table widths must total {CONTENT_WIDTH_DXA}: {widths_dxa}")
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    tbl_pr = table._tbl.tblPr

    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(CONTENT_WIDTH_DXA))
    tbl_w.set(qn("w:type"), "dxa")

    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), str(TABLE_INDENT_DXA))
    tbl_ind.set(qn("w:type"), "dxa")

    tbl_layout = tbl_pr.find(qn("w:tblLayout"))
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "fixed")

    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths_dxa:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)

    for row in table.rows:
        for index, cell in enumerate(row.cells):
            width = widths_dxa[index]
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(width))
            tc_w.set(qn("w:type"), "dxa")
            cell.width = Inches(width / 1440)
            set_cell_margins(cell)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def set_table_borders(table, color=MID_GRAY, size="6") -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        node = borders.find(qn(f"w:{edge}"))
        if node is None:
            node = OxmlElement(f"w:{edge}")
            borders.append(node)
        node.set(qn("w:val"), "single")
        node.set(qn("w:sz"), size)
        node.set(qn("w:color"), color)


def set_run_font(run, size=11, color=INK, bold=False, italic=False, name="Calibri") -> None:
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    run.font.size = Pt(size)
    run.font.color.rgb = RGBColor.from_string(color)
    run.bold = bold
    run.italic = italic


def add_page_field(paragraph) -> None:
    paragraph.add_run("Page ")
    run = paragraph.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char, instr, separate, text, end])


def add_numbering_definition(document: Document, ordered: bool) -> int:
    numbering = document.part.numbering_part.element
    abstract_ids = [int(node.get(qn("w:abstractNumId"))) for node in numbering.findall(qn("w:abstractNum"))]
    num_ids = [int(node.get(qn("w:numId"))) for node in numbering.findall(qn("w:num"))]
    abstract_id = max(abstract_ids, default=0) + 1
    num_id = max(num_ids, default=0) + 1

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "singleLevel")
    abstract.append(multi)
    level = OxmlElement("w:lvl")
    level.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start")
    start.set(qn("w:val"), "1")
    level.append(start)
    num_fmt = OxmlElement("w:numFmt")
    num_fmt.set(qn("w:val"), "decimal" if ordered else "bullet")
    level.append(num_fmt)
    lvl_text = OxmlElement("w:lvlText")
    lvl_text.set(qn("w:val"), "%1." if ordered else "•")
    level.append(lvl_text)
    p_pr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num")
    tab.set(qn("w:pos"), "540")
    tabs.append(tab)
    p_pr.append(tabs)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "540")
    ind.set(qn("w:hanging"), "270")
    p_pr.append(ind)
    level.append(p_pr)
    abstract.append(level)
    numbering.append(abstract)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId")
    abstract_ref.set(qn("w:val"), str(abstract_id))
    num.append(abstract_ref)
    numbering.append(num)
    return num_id


def add_list_item(document, text: str, num_id: int) -> None:
    paragraph = document.add_paragraph()
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = OxmlElement("w:numPr")
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), "0")
    num_id_el = OxmlElement("w:numId")
    num_id_el.set(qn("w:val"), str(num_id))
    num_pr.extend([ilvl, num_id_el])
    p_pr.append(num_pr)
    paragraph.paragraph_format.space_after = Pt(4)
    paragraph.paragraph_format.line_spacing = 1.25
    set_run_font(paragraph.add_run(text), size=11)


def add_paragraph(document, text: str, bold_prefix: str | None = None) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    paragraph.paragraph_format.line_spacing = 1.25
    if bold_prefix and text.startswith(bold_prefix):
        set_run_font(paragraph.add_run(bold_prefix), bold=True)
        set_run_font(paragraph.add_run(text[len(bold_prefix):]))
    else:
        set_run_font(paragraph.add_run(text))


def add_callout(document, label: str, text: str, fill=LIGHT_TEAL, accent=TEAL) -> None:
    table = document.add_table(rows=1, cols=1)
    set_table_geometry(table, [CONTENT_WIDTH_DXA])
    set_table_borders(table, accent, "8")
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    paragraph = cell.paragraphs[0]
    paragraph.paragraph_format.space_after = Pt(0)
    paragraph.paragraph_format.line_spacing = 1.2
    set_run_font(paragraph.add_run(f"{label}: "), bold=True, color=accent)
    set_run_font(paragraph.add_run(text), color=INK)
    document.add_paragraph().paragraph_format.space_after = Pt(1)


def add_table(document, headers: list[str], rows: list[list[str]], widths_dxa: list[int]) -> None:
    table = document.add_table(rows=1, cols=len(headers))
    set_table_geometry(table, widths_dxa)
    set_table_borders(table)
    header = table.rows[0]
    set_repeat_table_header(header)
    for index, text in enumerate(headers):
        cell = header.cells[index]
        set_cell_shading(cell, LIGHT_BLUE)
        paragraph = cell.paragraphs[0]
        paragraph.paragraph_format.space_after = Pt(0)
        set_run_font(paragraph.add_run(text), size=9.5, color=NAVY, bold=True)
    for row_values in rows:
        row = table.add_row()
        for index, text in enumerate(row_values):
            cell = row.cells[index]
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.1
            set_run_font(paragraph.add_run(str(text)), size=9.2, color=INK)
    set_table_geometry(table, widths_dxa)
    document.add_paragraph().paragraph_format.space_after = Pt(2)


def add_heading(document, text: str, level: int = 1) -> None:
    paragraph = document.add_paragraph(text, style=f"Heading {level}")
    paragraph.paragraph_format.keep_with_next = True


def add_section_break(document) -> None:
    document.add_section(WD_SECTION.NEW_PAGE)


def configure_document(document: Document) -> tuple[int, int]:
    section = document.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)

    styles = document.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor.from_string(INK)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25

    heading_tokens = {
        1: (16, BLUE, 18, 10),
        2: (13, BLUE, 14, 7),
        3: (12, "1F4D78", 10, 5),
    }
    for level, (size, color, before, after) in heading_tokens.items():
        style = styles[f"Heading {level}"]
        style.font.name = "Calibri"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    header = section.header
    hp = header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
    set_run_font(hp.add_run("SHADOWTRACEAI  |  APPLICATION FUNCTIONALITY GUIDE"), size=8.5, color=MUTED, bold=True)
    hp.paragraph_format.space_after = Pt(0)

    footer = section.footer
    fp = footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    set_run_font(fp.add_run("Deployed hackathon prototype  |  "), size=8.5, color=MUTED)
    add_page_field(fp)
    for run in fp.runs:
        set_run_font(run, size=8.5, color=MUTED)

    return add_numbering_definition(document, False), add_numbering_definition(document, True)


def build_document() -> None:
    document = Document()
    bullet_num, ordered_num = configure_document(document)

    # Editorial cover
    spacer = document.add_paragraph()
    spacer.paragraph_format.space_after = Pt(76)
    kicker = document.add_paragraph()
    kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    kicker.paragraph_format.space_after = Pt(16)
    set_run_font(kicker.add_run("APPLICATION FUNCTIONAL SPECIFICATION"), size=10, color=TEAL, bold=True)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.space_after = Pt(8)
    set_run_font(title.add_run("ShadowTraceAI"), size=31, color=NAVY, bold=True)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(18)
    set_run_font(subtitle.add_run("AML Intelligence Copilot on Snowflake"), size=16, color=BLUE)

    descriptor = document.add_paragraph()
    descriptor.alignment = WD_ALIGN_PARAGRAPH.CENTER
    descriptor.paragraph_format.space_after = Pt(54)
    set_run_font(
        descriptor.add_run("Detailed screen behavior, data contracts, decision workflow, controls, and acceptance criteria"),
        size=11,
        color=MUTED,
        italic=True,
    )

    metadata = [
        ("Document version", "1.0"),
        ("Status", "Deployed hackathon prototype"),
        ("Primary case", "CASE-C003 / ACC-C-003"),
        ("Audience", "AML investigators, reviewers, engineering teams, risk leaders, and judges"),
        ("Prepared", date(2026, 8, 18).strftime("%d %B %Y")),
    ]
    add_table(document, ["Document control", "Value"], [[a, b] for a, b in metadata], [2700, 6660])
    add_callout(
        document,
        "Purpose",
        "Explain exactly what the application does, what users see and do, which Snowflake objects supply each capability, and how a reviewer decision becomes an auditable case event.",
    )

    document.add_page_break()
    add_heading(document, "1. Executive overview", 1)
    add_paragraph(
        document,
        "ShadowTraceAI is a Snowflake-native investigation workspace for modern-slavery and human-trafficking AML alerts. It brings transaction behavior, customer and KYC context, device and IP access, external intelligence, document metadata, network relationships, explainable scoring, narrative evidence, reviewer decisions, and audit events into one governed application.",
    )
    add_paragraph(
        document,
        "The application is designed to support an investigator, not replace one. Detection and scoring are deterministic SQL. The intelligence brief is grounded in stored evidence. The recommended route guides review, while a named human must select and justify the final case decision.",
    )
    add_callout(
        document,
        "Deployed reference outcome",
        "CASE-C003 scores 92/100, receives the CRITICAL band and STRONG evidence rating, detects five modern-slavery typologies, and recommends ESCALATE TO SAR for human assessment.",
        fill=LIGHT_RED,
        accent=RED,
    )

    add_heading(document, "1.1 Capability summary", 2)
    capability_rows = [
        ["Case triage", "Prioritizes alerts by explainable risk score and evidence strength.", "Overview"],
        ["Typology detection", "Shows five modern-slavery indicators with point contributions and explanations.", "Typology Signals"],
        ["Network analysis", "Visualizes employer, worker, controller, funnel, cash-out, and shared-access relationships.", "Account Network"],
        ["Evidence review", "Combines documents, external intelligence, and relevant transactions.", "Evidence"],
        ["Explainable scoring", "Breaks the 0-100 score into seven queryable components.", "Risk Score"],
        ["Investigation narrative", "Presents an evidence-grounded executive summary, hypothesis, gaps, and action.", "Case Intelligence Brief"],
        ["Human decision", "Validates and records one of four authorized reviewer outcomes.", "Reviewer Decision"],
        ["Audit readiness", "Shows system and human events and exports the case timeline to CSV.", "Audit Trail"],
    ]
    add_table(document, ["Capability", "What it delivers", "App area"], capability_rows, [2200, 4800, 2360])

    add_heading(document, "1.2 Contents", 2)
    for item in [
        "Product scope, users, and operating principles",
        "End-to-end case journey and navigation model",
        "Detailed functionality for all eight application tabs",
        "Cross-cutting behavior, data contracts, and error handling",
        "Security, human oversight, and audit controls",
        "Functional acceptance criteria and known limitations",
        "Appendix: CASE-C003 reference walkthrough and glossary",
    ]:
        add_list_item(document, item, bullet_num)

    add_heading(document, "2. Product scope and users", 1)
    add_heading(document, "2.1 In-scope functionality", 2)
    for item in [
        "Read Snowflake-hosted alerts and supporting data for synthetic AML cases.",
        "Detect wage harvesting, account control, spending anomaly, geographic risk, and sector risk.",
        "Build a case-centric account network from payroll, onward transfers, cash-outs, and shared access.",
        "Calculate a deterministic risk score, band, evidence strength, risk factors, and route.",
        "Generate a deterministic case intelligence brief and expose a bounded prompt for optional Cortex use.",
        "Capture a named reviewer decision, rationale, updated alert status, and linked audit event.",
        "Export the audit trail for demonstration and downstream review.",
    ]:
        add_list_item(document, item, bullet_num)

    add_heading(document, "2.2 Primary user roles", 2)
    add_table(
        document,
        ["Role", "Primary objective", "Typical activity"],
        [
            ["AML investigator", "Understand why a case is suspicious.", "Review signals, network, evidence, score, and brief."],
            ["AML reviewer", "Make and justify the controlled case decision.", "Validate evidence and record one authorized outcome."],
            ["Team lead / QA", "Assess consistency and decision quality.", "Review scoring rationale, decisions, and audit history."],
            ["Data / analytics engineer", "Maintain governed detection logic.", "Manage SQL views, thresholds, data quality, and scoring versions."],
            ["Audit / compliance", "Reconstruct what happened and who acted.", "Inspect system events, human rationale, object IDs, and timestamps."],
        ],
        [1900, 3500, 3960],
    )

    add_heading(document, "2.3 Deliberate boundaries", 2)
    for item in [
        "The application does not autonomously file a suspicious activity report.",
        "The recommended route is advisory and does not replace regulatory judgment.",
        "The included data is synthetic and must not be interpreted as a production monitoring model.",
        "External intelligence records are demonstration inputs, not live commercial watchlist feeds.",
        "Cortex-generated language is optional; core scoring and the deterministic brief remain operational without it.",
    ]:
        add_list_item(document, item, bullet_num)

    document.add_page_break()
    add_heading(document, "3. End-to-end functional journey", 1)
    add_callout(
        document,
        "Application flow",
        "Alert selection -> typology detection -> connected-account analysis -> evidence review -> explainable score -> intelligence brief -> reviewer decision -> audit event.",
    )
    journey_steps = [
        ("Select the case", "The sidebar loads available cases, risk results, priority, and ownership from Snowflake."),
        ("Orient the review", "The Overview identifies the score, evidence strength, recommended route, alert reason, owner, and opened date."),
        ("Validate suspicious patterns", "The investigator checks each detected typology and its SQL explanation."),
        ("Inspect the network", "The investigator traces payroll, onward transfers, consolidation, cash-out, and shared-access relationships."),
        ("Reconcile evidence", "Documents, external intelligence, and transactions are reviewed together."),
        ("Challenge the score", "The reviewer sees the seven score components and top risk factors instead of a black-box number."),
        ("Read the case brief", "The application organizes suspicion, evidence, gaps, and the proposed next action."),
        ("Record a controlled decision", "The reviewer chooses an authorized route, names themselves, supplies rationale, and acknowledges the human gate."),
        ("Verify the audit trail", "The decision, actor, timestamp, rationale, object ID, and system events are available in chronological evidence."),
    ]
    for title_text, description in journey_steps:
        add_list_item(document, f"{title_text}: {description}", ordered_num)

    add_heading(document, "4. Navigation and case context", 1)
    add_heading(document, "4.1 Sidebar", 2)
    add_paragraph(
        document,
        "The sidebar is the persistent case-control surface. It displays the ShadowTraceAI identity, identifies the Snowflake-native investigation context, and provides the Active case selector. Each label combines case ID, risk band, and account display name so the reviewer can distinguish cases without opening them.",
    )
    for item in [
        "Active case: changes the working case for every tab.",
        "Refresh case data: clears the 30-second case cache and reruns the application.",
        "Context labels: state the Domain-Specific AI Copilot track, Snowflake SQL foundation, Cortex readiness, and human decision gate.",
    ]:
        add_list_item(document, item, bullet_num)

    add_heading(document, "4.2 Workspace header", 2)
    add_paragraph(
        document,
        "The workspace header confirms the selected case, account display name, alert status, and live Snowflake data state. The same case context remains in effect while the user moves across the eight top-level tabs.",
    )
    add_callout(
        document,
        "Context integrity",
        "All tab queries are parameterized with the selected case ID or its primary account ID. Changing the sidebar case changes the analytical context across the full workspace.",
    )

    document.add_page_break()
    add_heading(document, "5. Screen-by-screen functional specification", 1)

    add_heading(document, "5.1 Overview", 2)
    add_paragraph(document, "Purpose: Give the investigator a decision-oriented summary before opening detailed evidence.", "Purpose:")
    for item in [
        "Composite risk card with score out of 100 and risk band.",
        "Evidence-strength metric: STRONG, MODERATE, or LIMITED.",
        "Recommended route translated into a readable action label.",
        "Alert summary explaining why the case was created.",
        "Alert type, assigned owner, and opened date.",
    ]:
        add_list_item(document, item, bullet_num)
    add_table(
        document,
        ["Displayed element", "Snowflake source", "Functional meaning"],
        [
            ["Score / band", "vw_case_risk_summary", "Current deterministic case severity."],
            ["Evidence strength", "vw_case_risk_summary", "Degree of multi-source corroboration."],
            ["Recommended route", "vw_case_risk_summary", "Next-step recommendation, not an automatic action."],
            ["Alert summary and metadata", "case_alerts", "Original alert purpose, type, owner, and timestamp."],
        ],
        [2300, 2700, 4360],
    )
    add_callout(document, "CASE-C003 result", "92/100, CRITICAL, STRONG evidence, recommended route Escalate to SAR.", fill=LIGHT_RED, accent=RED)

    add_heading(document, "5.2 Typology Signals", 2)
    add_paragraph(document, "Purpose: Show which modern-slavery patterns fired, how many points each contributed, and why the SQL considered the pattern suspicious.", "Purpose:")
    for item in [
        "Detected-signal pills provide a rapid summary and point contribution.",
        "The signal table shows signal type, detection state, points, and human-readable explanation.",
        "Risk points use a progress display capped at 25 for quick comparison.",
        "Signals are ordered by contribution so the strongest pattern appears first.",
    ]:
        add_list_item(document, item, bullet_num)
    add_table(
        document,
        ["Typology", "Detection rule", "Points", "CASE-C003 evidence"],
        [
            ["Wage harvesting", "At least 3 workers transfer at least 70% of wages within 24 hours.", "25", "Five workers rapidly transfer wages to common controllers."],
            ["Account control", "A shared device and IP accesses at least 4 related accounts.", "25", "Common access links worker, controller, and funnel accounts."],
            ["Spending anomaly", "At least 3 workers direct at least 80% of outgoing value to transfer or cash.", "14", "Minimal ordinary card spend and rapid depletion."],
            ["Geographic risk", "At least 3 worker countries plus foreign cash withdrawal.", "12", "Cross-border recruitment corridor and out-of-country cash-out."],
            ["Sector risk", "Labour-intensive sector plus incomplete beneficial ownership.", "8", "Construction account with incomplete ownership information."],
        ],
        [1700, 3500, 800, 3360],
    )

    add_heading(document, "5.3 Account Network", 2)
    add_paragraph(document, "Purpose: Move the investigation from isolated transactions to connected actors, accounts, and flows.", "Purpose:")
    add_paragraph(
        document,
        "The app queries vw_case_network and renders a radial Plotly graph centered on the primary account. Node labels use account display names where available. The graph is accompanied by a row-level edge table for evidentiary precision.",
    )
    add_table(
        document,
        ["Visual role", "Classification logic", "Typical interpretation"],
        [
            ["Primary employer", "Selected case account", "Origin of payroll and focal corporate account."],
            ["Worker", "Receives PAYROLL edge", "Individual wage recipient."],
            ["Controller", "Receives FUNDS_TO_CONTROLLER edge", "Common onward-transfer destination."],
            ["Funnel", "Receives CONSOLIDATION edge", "Account aggregating controlled funds."],
            ["Cash-out", "CASH_OUT edge or EXTERNAL_CASH", "Terminal withdrawal or external cash destination."],
            ["Connected", "Other relationship", "Additional contextual node."],
        ],
        [1900, 3200, 4260],
    )
    for item in [
        "Hovering a node reveals account ID and role.",
        "Hovering an edge reveals the relationship type.",
        "The supporting table provides source, target, relationship, event count, total amount, and evidence text.",
        "An empty network displays an informational state instead of a blank chart.",
    ]:
        add_list_item(document, item, bullet_num)

    add_heading(document, "5.4 Evidence", 2)
    add_paragraph(document, "Purpose: Let investigators reconcile three evidence domains without leaving the case workspace.", "Purpose:")
    add_heading(document, "Documents subtab", 3)
    add_paragraph(document, "Displays document ID and type, file name, extraction confidence, parsed risk indicators, evidence summary, and review status. Semi-structured indicator arrays are converted into readable comma-separated labels.")
    add_heading(document, "External intelligence subtab", 3)
    add_paragraph(document, "Displays source type, matched entity, risk level, match strength, published date, summary, and clickable source URL. The query includes the primary account and accounts found on either side of the case network.")
    add_heading(document, "Transactions subtab", 3)
    add_paragraph(document, "Displays timestamp, source, destination, amount, currency, type, channel, country, and description for the primary account and network sources, ordered newest first.")
    add_table(
        document,
        ["Evidence domain", "Primary table", "Investigation question"],
        [
            ["Documents", "document_evidence", "Do payroll, identity, contract, or accommodation records corroborate control or exploitation?"],
            ["External intelligence", "external_watchlist", "Are connected entities associated with adverse media, sanctions, or other high-risk intelligence?"],
            ["Transactions", "transactions", "How did funds move, how quickly, through which channels, and to which geography?"],
        ],
        [1900, 2400, 5060],
    )

    add_heading(document, "5.5 Risk Score", 2)
    add_paragraph(document, "Purpose: Make the 0-100 score challengeable, reproducible, and traceable to visible evidence.", "Purpose:")
    add_paragraph(
        document,
        "The score equals detected typology points plus external-intelligence corroboration and document-evidence corroboration, capped at 100. The score card shows band, evidence strength, and scoring version. A horizontal bar chart displays the component object stored in score_breakdown.",
    )
    add_table(
        document,
        ["Component", "Maximum", "CASE-C003", "Source"],
        [
            ["Wage harvesting", "25", "25", "vw_wage_harvesting_signals"],
            ["Account control", "25", "25", "vw_account_control_signals"],
            ["Spending anomaly", "14", "14", "vw_spending_anomaly_signals"],
            ["Geographic risk", "12", "12", "vw_geographic_risk_signals"],
            ["Sector risk", "8", "8", "vw_sector_risk_signals"],
            ["External intelligence", "4", "4", "external_watchlist"],
            ["Document evidence", "4", "4", "document_evidence"],
            ["Total", "100", "92", "vw_case_risk_summary"],
        ],
        [2500, 1500, 1700, 3660],
    )
    add_table(
        document,
        ["Score range", "Risk band", "Recommended route"],
        [
            ["90-100", "CRITICAL", "ESCALATE_TO_SAR"],
            ["70-89", "HIGH", "REQUEST_MORE_EVIDENCE"],
            ["40-69", "MEDIUM", "MONITOR_CASE"],
            ["0-39", "LOW", "CLOSE_AS_FALSE_POSITIVE"],
        ],
        [2000, 2200, 5160],
    )
    add_callout(document, "Human-control rule", "The score recommends a route; it never files a SAR autonomously.")

    add_heading(document, "5.6 Case Intelligence Brief", 2)
    add_paragraph(document, "Purpose: Turn structured evidence into a concise investigation narrative while preserving the underlying evidence trail.", "Purpose:")
    add_table(
        document,
        ["Brief section", "Functional content"],
        [
            ["Executive summary", "High-level case condition, key linked activity, and current severity."],
            ["Suspicion hypothesis", "Evidence-bounded explanation of the possible modern-slavery pattern."],
            ["Evidence summary", "Condensed multi-source facts supporting the hypothesis."],
            ["Missing evidence", "Known gaps the reviewer should resolve before or after escalation."],
            ["Recommended action", "Proposed route and proportionate next step."],
            ["Cortex prompt", "Expandable grounded prompt for optional Snowflake Cortex / Intelligence summarization."],
        ],
        [2500, 6860],
    )
    add_paragraph(
        document,
        "The default brief is deterministic and is produced by vw_case_intelligence_brief. This ensures the application remains operational even if a model is unavailable. The optional prompt can be reviewed, executed with authorized Cortex access, and compared against the deterministic narrative.",
    )

    add_heading(document, "5.7 Reviewer Decision", 2)
    add_paragraph(document, "Purpose: Convert analytical evidence into a named, justified, and auditable human outcome.", "Purpose:")
    add_table(
        document,
        ["User-facing choice", "Stored decision code", "Resulting alert status"],
        [
            ["Escalate to SAR", "ESCALATE_TO_SAR", "REVIEWED"],
            ["Request more evidence", "REQUEST_MORE_EVIDENCE", "EVIDENCE_REQUESTED"],
            ["Monitor case", "MONITOR_CASE", "REVIEWED"],
            ["Close as false positive", "CLOSE_AS_FALSE_POSITIVE", "REVIEWED"],
        ],
        [3000, 3500, 2860],
    )
    add_heading(document, "Input validation", 3)
    for item in [
        "Reviewer name must be present.",
        "Rationale must be present.",
        "The reviewer must acknowledge that this is a human decision and no SAR is filed automatically.",
        "The procedure rejects any decision code outside the four-value allowlist.",
    ]:
        add_list_item(document, item, bullet_num)
    add_heading(document, "Transactional behavior", 3)
    for item in [
        "Generate a unique decision ID and audit event ID.",
        "Insert the reviewer decision into case_decisions.",
        "Insert the linked REVIEWER_DECISION event into audit_events.",
        "Update the case alert status and assign it to the reviewer.",
        "Commit all changes together; roll back all changes if any operation fails.",
        "Return the decision ID so the app can confirm successful linkage.",
    ]:
        add_list_item(document, item, ordered_num)
    add_callout(document, "Control objective", "A decision can never appear without its companion audit event because both records are written in the same Snowflake transaction.")

    add_heading(document, "5.8 Audit Trail", 2)
    add_paragraph(document, "Purpose: Reconstruct case history across automated analysis and human review.", "Purpose:")
    for item in [
        "Displays event timestamp, actor type, actor name, event type, detail, object type, and object ID.",
        "Orders events newest first for operational review.",
        "Includes alert creation, signal evaluation, evidence linkage, risk calculation, and reviewer decisions.",
        "Exports the selected case timeline as a CSV named with the lowercase case ID.",
    ]:
        add_list_item(document, item, bullet_num)

    document.add_page_break()
    add_heading(document, "6. Cross-cutting application behavior", 1)
    add_table(
        document,
        ["Behavior", "Implementation", "User impact"],
        [
            ["Snowflake session", "Uses get_active_session in the native app; falls back to st.connection locally.", "Same code supports Snowflake and local development."],
            ["Parameterized queries", "Case and account values are passed as parameters.", "Reduces injection risk and preserves query clarity."],
            ["Case cache", "Case-list query is cached for 30 seconds.", "Fast navigation with bounded freshness."],
            ["Manual refresh", "Refresh button clears cached data and reruns the app.", "Reviewer can immediately see new decisions or alert state."],
            ["Semi-structured values", "JSON and Snowflake arrays/objects are parsed for readable display.", "Risk factors and document indicators remain understandable."],
            ["Responsive design", "Wide layout, light theme, wrapping header, and scalable components.", "Usable across laptop and larger review displays."],
            ["Downloads", "Audit DataFrame is serialized to UTF-8 CSV.", "Portable evidence for demonstration or controlled review."],
        ],
        [1800, 4000, 3560],
    )

    add_heading(document, "7. Snowflake data and object contracts", 1)
    add_table(
        document,
        ["Object", "Type", "Application responsibility"],
        [
            ["accounts", "Table", "Names, account type, sector, geography, employer linkage, and declared profile."],
            ["transactions", "Table", "Payroll, transfer, card-spend, cash-out, channel, and geography behavior."],
            ["kyc_profiles", "Table", "Customer type, occupation/business, ownership, source of funds, and KYC risk."],
            ["device_ip_signals", "Table", "Shared device/IP access and successful-login evidence."],
            ["external_watchlist", "Table", "Adverse media/watchlist source, match strength, risk, summary, and URL."],
            ["document_evidence", "Table", "Document metadata, extraction confidence, indicators, summary, and status."],
            ["case_alerts", "Table", "Case identity, priority, status, owner, creation time, and alert summary."],
            ["case_risk_scores", "Table", "Persisted score snapshot, factors, route, breakdown, and version."],
            ["case_decisions", "Table", "Reviewer choice, name, rationale, and timestamp."],
            ["audit_events", "Table", "Machine and human events with actor, detail, object linkage, and metadata."],
            ["vw_all_typology_signals", "View", "Unified five-signal contract for Typology Signals."],
            ["vw_case_network", "View", "Case edges used by graph and network evidence table."],
            ["vw_case_risk_summary", "View", "Live score, band, evidence strength, factors, route, and breakdown."],
            ["vw_case_intelligence_brief", "View", "Deterministic investigation narrative and bounded prompt."],
            ["sp_record_case_decision", "Procedure", "Atomic decision, audit, and alert-status transaction."],
        ],
        [2800, 1300, 5260],
    )

    add_heading(document, "8. Error and empty-state behavior", 1)
    add_table(
        document,
        ["Condition", "Application response", "Operator action"],
        [
            ["Snowflake connection or setup incomplete", "Shows an error, lists the six build scripts, displays connection detail, and stops.", "Verify connection and execute SQL files in order."],
            ["No cases available", "Shows a warning and stops.", "Load seed data and rebuild views."],
            ["No network edges", "Shows an informational message instead of an empty chart.", "Confirm the case has network-qualified transactions."],
            ["Decision fields incomplete", "Shows a validation error without calling the procedure.", "Provide reviewer, rationale, and acknowledgement."],
            ["Decision procedure fails", "Shows the Snowflake exception and leaves the transaction rolled back.", "Correct permissions or input, then retry."],
            ["Cached view appears stale", "Existing values remain until cache expiry or refresh.", "Select Refresh case data."],
        ],
        [2400, 4100, 2860],
    )

    add_heading(document, "9. Security, governance, and responsible use", 1)
    for item in [
        "Data stays within Snowflake for native execution; local development uses an explicit Snowflake connection.",
        "The procedure executes as caller, so reviewer writes remain subject to the caller's Snowflake privileges.",
        "The score and route are transparent SQL outputs with an explicit scoring version.",
        "The human acknowledgement prevents the UI from presenting an analytical recommendation as an automatic filing.",
        "Decision rationale and reviewer identity become part of the audit record.",
        "The demo credential helper stores only a Windows DPAPI-encrypted credential under the Git-ignored .snowflake directory; production should use organization-approved authentication and least privilege.",
        "Synthetic data must remain clearly labeled and separated from production AML information.",
    ]:
        add_list_item(document, item, bullet_num)

    add_heading(document, "10. Functional acceptance criteria", 1)
    acceptance_rows = [
        ["FA-01", "App loads CASE-C003 from Snowflake without a connection error.", "Overview renders case and risk data."],
        ["FA-02", "CASE-C003 shows 92, CRITICAL, STRONG, and Escalate to SAR.", "Four values reconcile to vw_case_risk_summary."],
        ["FA-03", "All five typology signals are detected.", "Five detected rows with total typology contribution of 84."],
        ["FA-04", "Network shows employer, workers, controller, funnel, and cash-out.", "Graph and edge table render without missing context."],
        ["FA-05", "Documents, intelligence, and transactions load.", "Each Evidence subtab returns relevant rows."],
        ["FA-06", "Seven score components reconcile to 92.", "25 + 25 + 14 + 12 + 8 + 4 + 4 = 92."],
        ["FA-07", "Brief presents all five narrative sections and prompt.", "No unsupported or autonomous filing claim appears."],
        ["FA-08", "Reviewer decision enforces required inputs.", "Submission is blocked until reviewer, rationale, and acknowledgement exist."],
        ["FA-09", "Escalate to SAR creates decision and audit rows.", "Returned decision ID links to REVIEWER_DECISION event."],
        ["FA-10", "Audit trail can be downloaded.", "CSV contains visible events for selected case."],
        ["FA-11", "Benign CASE-C010 remains LOW.", "Risk test returns PASS."],
        ["FA-12", "Application stays consistently light.", "Theme applies to canvas, sidebar, tables, forms, tabs, charts, and alerts."],
    ]
    add_table(document, ["ID", "Criterion", "Expected evidence"], acceptance_rows, [1000, 4700, 3660])

    add_heading(document, "11. Known limitations and production roadmap", 1)
    add_table(
        document,
        ["Prototype limitation", "Production enhancement"],
        [
            ["Synthetic cases and simplified typology thresholds", "Calibrate against validated historical cases, QA labels, and jurisdiction-specific policy."],
            ["Static external-intelligence seed data", "Integrate licensed sanctions, PEP, adverse-media, and case-management feeds."],
            ["No fine-grained application authorization model", "Implement least-privilege roles, row access policies, masking, and environment separation."],
            ["No case assignment queue or SLA dashboard", "Add work allocation, aging, escalation, and quality-control workflow."],
            ["Optional Cortex brief is not required for the core path", "Add governed model selection, prompt/version logging, evaluation, and output approval."],
            ["Decision route does not file externally", "Integrate only with authorized SAR workflow after legal, control, and human-approval design."],
            ["Limited automated UI tests", "Add regression tests for queries, components, permissions, and end-to-end reviewer actions."],
        ],
        [4100, 5260],
    )

    document.add_page_break()
    add_heading(document, "Appendix A. CASE-C003 reference walkthrough", 1)
    walkthrough = [
        "Select CASE-C003 / Horizon Works Construction Ltd.",
        "Confirm 92/100 CRITICAL, STRONG evidence, and Escalate to SAR on Overview.",
        "Show all five detected typologies and explain each point contribution.",
        "Trace payroll from ACC-C-003 through worker accounts to controller, funnel, and external cash-out.",
        "Open Documents, External intelligence, and Transactions to reconcile the supporting facts.",
        "Explain the seven score components and the SHADOWTRACE_SQL_V1 scoring version.",
        "Read the executive summary, suspicion hypothesis, evidence summary, missing evidence, and action.",
        "Enter the reviewer name and rationale, select Escalate to SAR, acknowledge the human gate, and record the decision.",
        "Open Audit Trail and show the linked human decision event; download the case CSV if needed.",
    ]
    for item in walkthrough:
        add_list_item(document, item, ordered_num)

    add_heading(document, "Appendix B. Glossary", 1)
    add_table(
        document,
        ["Term", "Definition in ShadowTraceAI"],
        [
            ["AML", "Anti-money laundering controls and investigation activities."],
            ["Case", "The investigation unit identified by case_id and anchored to a primary account."],
            ["Typology", "A recognizable suspicious pattern represented as deterministic SQL logic."],
            ["Risk score", "Capped 0-100 sum of typology and corroborating evidence points."],
            ["Risk band", "LOW, MEDIUM, HIGH, or CRITICAL classification derived from score thresholds."],
            ["Evidence strength", "LIMITED, MODERATE, or STRONG rating based on signal, intelligence, and document corroboration."],
            ["Recommended route", "System-proposed next step that remains subject to human review."],
            ["SAR", "Suspicious activity report; ShadowTraceAI can recommend assessment but does not file one automatically."],
            ["Controller", "Account receiving rapid onward transfers from worker accounts."],
            ["Funnel", "Account consolidating funds from a controller or related network accounts."],
            ["Audit event", "Timestamped machine or human event linked to a case and governed object."],
            ["Cortex prompt", "Evidence-bounded input prepared for optional Snowflake generative summarization."],
        ],
        [2200, 7160],
    )

    add_callout(
        document,
        "Document ownership",
        "Update this guide whenever screen behavior, SQL contracts, scoring thresholds, decision codes, or audit semantics change. Functional changes should be versioned with the corresponding SQL and application release.",
        fill=LIGHT_GRAY,
        accent=BLUE,
    )

    # Carry section geometry and running furniture to any sections introduced by page breaks.
    for section in document.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.header_distance = Inches(0.492)
        section.footer_distance = Inches(0.492)

    document.core_properties.title = "ShadowTraceAI Application Functionality Guide"
    document.core_properties.subject = "Detailed functional specification for the Snowflake-native AML application"
    document.core_properties.author = "ShadowTraceAI Team"
    document.core_properties.keywords = "Snowflake, AML, modern slavery, functionality, Streamlit, investigation"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build_document()
