"""Export PDF du rapport d'investissement (reportlab, pur Python)."""
import io
from xml.sax.saxutils import escape


def build_pdf(study, financial, criteria, ranks, alloc, lead, agree, justification, method_profile=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

    navy, teal = colors.HexColor('#132F50'), colors.HexColor('#2DACA6')
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=ss['Title'], textColor=navy, fontSize=22, alignment=0)
    h2 = ParagraphStyle('h2', parent=ss['Heading2'], textColor=teal, spaceBefore=12)
    body = ParagraphStyle('b', parent=ss['BodyText'], fontSize=9.5, leading=13)

    def table(header, data, widths=None):
        t = Table([header] + data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), navy), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                               ('FONTSIZE', (0, 0), (-1, -1), 7.5), ('GRID', (0, 0), (-1, -1), .25, colors.HexColor('#C9D6E2')),
                               ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F6FA')])]))
        return t

    def f(v):
        return 'N/D' if v is None or v != v else (f'{v:.3f}' if isinstance(v, float) else str(v))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.6 * cm, bottomMargin=1.6 * cm,
                            title='OptiVest · ' + study['study_name'])
    s = [Paragraph('OPTIVEST · INVESTMENT INTELLIGENCE', body), Paragraph(escape(study['study_name']), h1),
         Paragraph(f"Budget {study['budget']:.2f} M MAD · taux d'actualisation {study['rate']:.1%} · horizon {study['horizon']} ans", body),
         Paragraph('Recommandation', h2),
         Paragraph(f"Leader multicritère (rang moyen) : <b>{escape(str(lead))}</b>. Accord moyen des méthodes (Spearman) : {agree:.3f}.", body),
         Paragraph(f"Portefeuille optimisé sous budget : <b>{escape(', '.join(alloc['selected']) or 'aucun')}</b> · "
                   f"investissement {alloc['investment']:.2f} M · VAN totale {alloc['total_npv']:+.2f} M.", body),
         Paragraph('Indicateurs financiers', h2)]
    cols = [c for c in financial.columns]
    s.append(table(cols, [[f(v) for v in row] for row in financial.itertuples(index=False)]))
    s += [Paragraph('Pondération active', h2), table(['Critère', 'Sens', 'Poids'], [[c, k, f'{w:.3f}'] for c, k, w in criteria]),
          Paragraph('Classements par méthode', h2)]
    s.append(table(['Projet'] + list(ranks.columns), [[str(i)] + [f(v) for v in r] for i, r in zip(ranks.index, ranks.values)]))
    if method_profile:
        s += [Paragraph('Choix méthodologique', h2)] + [Paragraph('• ' + escape(w), body) for w in method_profile['justifications']]
    s += [Paragraph('Justification', h2), Paragraph(escape(justification or 'À compléter.').replace('\n', '<br/>'), body),
          Paragraph('Hypothèses et limites', h2),
          Paragraph("Flux de fin d'année, taux constant, projets indépendants et indivisibles, notes de risque et d'alignement subjectives. "
                    "Les données de démonstration sont fictives ; un classement MCDM n'est pas une prédiction de succès financier.", body)]
    doc.build(s)
    return buf.getvalue()
