# src/export_helpers.py
import tempfile
from fpdf import FPDF
import io

def dataframe_to_pdf(df, title="Exported Table"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    for col in df.columns:
        pdf.cell(40, 10, col, 1, 0, 'C')
    pdf.ln()
    for idx, row in df.iterrows():
        for item in row:
            pdf.cell(40, 10, str(item), 1, 0, 'C')
        pdf.ln()
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    pdf.output(tmpfile.name)
    return tmpfile.name

def plotly_export(fig, fmt='png'):
    buf = io.BytesIO()
    fig.write_image(buf, format=fmt)
    buf.seek(0)
    return buf
