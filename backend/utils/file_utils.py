import fitz  # PyMuPDF
import docx
import io
import logging

logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_stream: io.BytesIO) -> str:
    """Extracts text from a PDF file stream."""
    try:
        # Convert BytesIO to bytes for fitz
        pdf_data = file_stream.getvalue()
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text() or "")
        doc.close()
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Could not extract text from PDF: {e}")

def extract_text_from_docx(file_stream: io.BytesIO) -> str:
    """Extracts text from a DOCX file stream."""
    try:
        document = docx.Document(file_stream)
        text = []
        for para in document.paragraphs:
            text.append(para.text)
        return "\n".join(text)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise ValueError(f"Could not extract text from DOCX: {e}")