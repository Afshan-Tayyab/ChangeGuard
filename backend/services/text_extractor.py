# backend/services/text_extractor.py
import pymupdf  # FIX: Changed from 'fitz' to 'pymupdf'
import docx
import os

def extract_text(file_path: str) -> str:
    """Extracts text based on the file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
            
    elif ext == ".pdf":
        text = ""
        # FIX: Use pymupdf instead of fitz
        with pymupdf.open(file_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
        return text
        
    elif ext == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
        
    else:
        raise ValueError(f"Unsupported file format: {ext}")