# backend/server.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import shutil
import os
import json

# Import Database
from database import SessionLocal, engine, Base, ComparisonHistory

# Import Services
from services.text_extractor import extract_text
from services.semantic_analyzer import split_into_sentences, analyze_sentence
from services.change_detector import compare_documents

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ChangeGuard API",
    description="NLP-Based Context-Aware Semantic Change Detection System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class DocumentPair(BaseModel):
    old_text: str
    new_text: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def root():
    return {"project": "ChangeGuard", "status": "running", "stage": "Final"}

@app.post("/extract")
async def extract_document(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".txt", ".pdf", ".docx"]:
        raise HTTPException(status_code=400, detail="Only TXT, PDF, and DOCX are allowed.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        text = extract_text(file_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="The document is empty or text could not be extracted.")
        return {"filename": file.filename, "extracted_text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze")
async def analyze_text(text: str):
    sentences = split_into_sentences(text)
    results = [analyze_sentence(s) for s in sentences]
    return {"sentence_count": len(sentences), "analyses": results}

@app.post("/compare")
async def compare(docs: DocumentPair, db: Session = Depends(get_db)):
    old_sentences = split_into_sentences(docs.old_text)
    new_sentences = split_into_sentences(docs.new_text)
    results = compare_documents(old_sentences, new_sentences)
    
    history_entry = ComparisonHistory(
        old_filename="Pasted Text",
        new_filename="Pasted Text",
        changes_json=json.dumps(results)
    )
    db.add(history_entry)
    db.commit()
    db.refresh(history_entry)
    
    return {"total_changes": len(results), "comparison": results}

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    history = db.query(ComparisonHistory).order_by(ComparisonHistory.timestamp.desc()).limit(10).all()
    return history

@app.get("/history/{history_id}")
def get_history_detail(history_id: int, db: Session = Depends(get_db)):
    entry = db.query(ComparisonHistory).filter(ComparisonHistory.id == history_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="History not found")
    return {"id": entry.id, "timestamp": entry.timestamp, "comparison": json.loads(entry.changes_json)}

@app.get("/style.css")
def get_css():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(base_dir, "..", "frontend", "style.css"))

@app.get("/script.js")
def get_js():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(base_dir, "..", "frontend", "script.js"))

@app.get("/app/", response_class=HTMLResponse)
def serve_frontend():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_file = os.path.abspath(os.path.join(base_dir, "..", "frontend", "index.html"))
    
    if not os.path.exists(frontend_file):
        return f"<h3>Error: Cannot find {frontend_file}.</h3>"
        
    with open(frontend_file, "r", encoding="utf-8") as f:
        return f.read()