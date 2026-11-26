"""Draws a landscape A4 completion certificate."""
from io import BytesIO

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

INK = HexColor("#14213d")
ACCENT = HexColor("#4f46e5")
GOLD = HexColor("#c8932a")
MUTED = HexColor("#5b6475")


def _fitted(pdf, text, font, size, y, centre, max_width, colour):
    while size > 10 and stringWidth(text, font, size) > max_width:
        size -= 1
    pdf.setFont(font, size)
    pdf.setFillColor(colour)
    pdf.drawCentredString(centre, y, text)


def render_certificate(certificate, verify_url):
    buffer = BytesIO()
    width, height = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(width, height))
    pdf.setTitle(f"Certificate - {certificate['course_title']}")
    centre = width / 2
    usable = width - 160

    pdf.setFillColor(HexColor("#fdfcf8"))
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setStrokeColor(ACCENT)
    pdf.setLineWidth(10)
    pdf.rect(24, 24, width - 48, height - 48)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.5)
    pdf.rect(40, 40, width - 80, height - 80)

    _fitted(pdf, "LearnSphere", "Helvetica-Bold", 18, height - 88, centre, usable, ACCENT)
    _fitted(pdf, "Certificate of Completion", "Times-Bold", 40, height - 152, centre, usable, INK)
    _fitted(pdf, "This certificate is proudly presented to", "Helvetica", 13,
            height - 196, centre, usable, MUTED)
    _fitted(pdf, certificate["student_name"], "Times-BoldItalic", 36,
            height - 248, centre, usable, INK)
    pdf.setStrokeColor(GOLD)
    pdf.line(centre - 180, height - 264, centre + 180, height - 264)
    _fitted(pdf, "for successfully completing all lessons and quizzes of the course",
            "Helvetica", 13, height - 292, centre, usable, MUTED)
    _fitted(pdf, certificate["course_title"], "Helvetica-Bold", 22,
            height - 328, centre, usable, ACCENT)

    for x, value, label in (
        (centre - 200, certificate["issued_at"][:10], "Date of issue"),
        (centre + 200, certificate["instructor_name"], "Course instructor"),
    ):
        _fitted(pdf, value, "Helvetica-Bold", 13, 140, x, 220, INK)
        pdf.setStrokeColor(MUTED)
        pdf.setLineWidth(0.8)
        pdf.line(x - 110, 132, x + 110, 132)
        _fitted(pdf, label, "Helvetica", 10, 116, x, 220, MUTED)

    _fitted(pdf, f"Certificate ID: {certificate['code']}", "Helvetica-Bold", 10,
            78, centre, usable, INK)
    _fitted(pdf, f"Verify at {verify_url}", "Helvetica", 9, 62, centre, usable, MUTED)
    pdf.linkURL(verify_url, (centre - 200, 56, centre + 200, 74))
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
