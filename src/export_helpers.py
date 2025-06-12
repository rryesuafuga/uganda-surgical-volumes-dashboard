# src/export_helpers.py
import tempfile
from fpdf import FPDF
import io
import streamlit as st

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
    """
    Export plotly figure to image format.
    Returns None if kaleido is not available.
    """
    try:
        # Try to import kaleido for image export
        import kaleido
        buf = io.BytesIO()
        fig.write_image(buf, format=fmt)
        buf.seek(0)
        return buf
    except ImportError:
        st.warning(f"Image export requires the 'kaleido' package. Install it with: pip install kaleido")
        return None
    except Exception as e:
        st.error(f"Error exporting image: {str(e)}")
        return None

def safe_download_button(label, data, filename, mime_type, key=None):
    """
    Create a download button only if data is available
    """
    if data is not None:
        st.download_button(label, data, file_name=filename, mime=mime_type, key=key)
    else:
        st.info(f"Install 'kaleido' package to enable {filename} downloads")