import json
from io import BytesIO
from datetime import datetime, timezone


def build_export_payload(
    repository_identifier: str,
    num_commits: int,
    total_files: int,
    avg_risk: float,
    bus_factor: int,
    metrics,
    coupling,
    logical_coupling,
    ai_report: str = None,
):
    payload = {
        "exported_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_input": {
            "repository": repository_identifier,
            "commits": num_commits,
        },
        "kpis": {
            "total_files": total_files,
            "avg_risk": float(avg_risk),
            "bus_factor": int(bus_factor),
        },
        "metrics": metrics,
        "coupling": coupling,
        "logical_coupling": logical_coupling,
    }

    if ai_report:
        payload["ai_report"] = ai_report

    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_markdown_export(
    repository_identifier: str,
    num_commits: int,
    total_files: int,
    avg_risk: float,
    bus_factor: int,
    metrics,
    coupling,
    ai_report: str = None,
):
    top_hotspots = metrics[:5] if metrics else []
    top_coupling = coupling[:5] if coupling else []

    lines = [
        "# Export de Análise - Repo Health AI",
        "",
        "## Contexto para IA",
        "Use os dados abaixo para gerar diagnóstico de saúde evolutiva, riscos de manutenção, silos de conhecimento e plano de ação priorizado.",
        "",
        "## Metadados",
        f"- Repositório: {repository_identifier}",
        f"- Commits analisados: {num_commits}",
        f"- Total de arquivos analisados: {total_files}",
        f"- Risco médio: {avg_risk:,.2f}",
        f"- Bus Factor: {bus_factor}",
        "",
        "## Top Hotspots (foco de risco)",
    ]

    if top_hotspots:
        for item in top_hotspots:
            lines.append(
                f"- {item['file']}: risk={item['risk_score']}, churn={item['churn']}, complexity={item['complexity']}, authors={item['top_authors']}"
            )
    else:
        lines.append("- Nenhum hotspot disponível.")

    lines.extend(["", "## Top Acoplamentos (dependências ocultas)"])
    if top_coupling:
        for item in top_coupling:
            lines.append(
                f"- {item['file_a']} ↔ {item['file_b']}: shared_commits={item['shared_commits']}, strength={item['strength']}"
            )
    else:
        lines.append("- Nenhum acoplamento disponível.")

    lines.extend([
        "",
        "## JSON Completo (métricas)",
        "```json",
        json.dumps(
            {
                "repository": repository_identifier,
                "num_commits": num_commits,
                "kpis": {
                    "total_files": total_files,
                    "avg_risk": float(avg_risk),
                    "bus_factor": int(bus_factor),
                },
                "metrics": metrics,
                "coupling": coupling,
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
    ])

    if ai_report:
        lines.extend(["", "## Último Relatório IA", "", ai_report])

    return "\n".join(lines)


def build_pdf_export(
    repository_identifier: str,
    num_commits: int,
    total_files: int,
    avg_risk: float,
    bus_factor: int,
    metrics,
    coupling,
):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except Exception as e:
        raise RuntimeError("Biblioteca de PDF não disponível. Instale 'reportlab'.") from e

    top_hotspots = metrics[:10] if metrics else []
    top_coupling = coupling[:5] if coupling else []

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="Repo Health AI - Relatório",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleCustom",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1F2A44"),
        spaceAfter=8,
    )
    subtitle_style = ParagraphStyle(
        name="SubtitleCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#667085"),
        spaceAfter=10,
    )
    section_style = ParagraphStyle(
        name="SectionCustom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1F2A44"),
        spaceBefore=6,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        name="BodyCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#344054"),
        spaceAfter=3,
    )

    story = []
    story.append(Paragraph("Repo Health AI - Relatório de Saúde Evolutiva", title_style))
    story.append(
        Paragraph(
            f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} · Repositório: {repository_identifier}",
            subtitle_style,
        )
    )

    kpi_table = Table(
        [
            ["Commits Analisados", "Arquivos", "Risco Médio", "Bus Factor"],
            [str(num_commits), str(total_files), f"{avg_risk:,.2f}", str(bus_factor)],
        ],
        colWidths=[40 * mm, 30 * mm, 35 * mm, 28 * mm],
    )
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EEF4FF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1F2A44")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Resumo Executivo", section_style))
    summary_text = (
        "Este relatório prioriza hotspots e dependências ocultas para apoiar decisões de refatoração, "
        "distribuição de conhecimento e redução de risco técnico."
    )
    story.append(Paragraph(summary_text, body_style))

    story.append(Paragraph("Top Hotspots", section_style))
    if top_hotspots:
        hotspot_data = [["Arquivo", "Risk", "Churn", "Complexidade", "Autores"]]
        for item in top_hotspots:
            authors = ", ".join([f"{k}:{v}" for k, v in item.get("top_authors", {}).items()])
            hotspot_data.append(
                [
                    str(item.get("file", "-"))[:36],
                    str(item.get("risk_score", "-")),
                    str(item.get("churn", "-")),
                    str(item.get("complexity", "-")),
                    authors[:34] if authors else "-",
                ]
            )

        hotspot_table = Table(hotspot_data, colWidths=[52 * mm, 22 * mm, 20 * mm, 24 * mm, 44 * mm])
        hotspot_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (1, 1), (3, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D5DD")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FCFCFD")]),
                ]
            )
        )
        story.append(hotspot_table)
    else:
        story.append(Paragraph("Nenhum hotspot disponível.", body_style))

    story.append(Spacer(1, 8))
    story.append(Paragraph("Top Acoplamentos", section_style))
    if top_coupling:
        coupling_data = [["Arquivo A", "Arquivo B", "Co-alterações", "Força"]]
        for item in top_coupling:
            coupling_data.append(
                [
                    str(item.get("file_a", "-"))[:40],
                    str(item.get("file_b", "-"))[:40],
                    str(item.get("shared_commits", "-")),
                    str(item.get("strength", "-")),
                ]
            )

        coupling_table = Table(coupling_data, colWidths=[50 * mm, 50 * mm, 28 * mm, 30 * mm])
        coupling_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F2F4F7")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (2, 1), (3, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D5DD")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FCFCFD")]),
                ]
            )
        )
        story.append(coupling_table)
    else:
        story.append(Paragraph("Nenhum acoplamento disponível.", body_style))

    document.build(story)
    data = buffer.getvalue()
    buffer.close()
    return data
