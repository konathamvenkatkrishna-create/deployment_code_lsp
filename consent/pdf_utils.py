import tempfile
from reportlab.pdfgen import canvas

def generate_pdf(filename_prefix: str, text: str):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    file_path = tmp.name
    tmp.close()

    c = canvas.Canvas(file_path)
    x, y = 40, 800

    for line in text.split("\n"):
        c.drawString(x, y, line)
        y -= 15
        if y < 40:
            c.showPage()
            y = 800

    c.save()
    return file_path
