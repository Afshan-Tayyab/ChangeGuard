# backend/server.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import hashlib
import shutil
import os
import json

# Import Database
from database import SessionLocal, engine, Base, ComparisonHistory, User

# Import Services
from services.text_extractor import extract_text
from services.semantic_analyzer import split_into_sentences, analyze_sentence
from services.change_detector import compare_documents

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
    return {"project": "ChangeGuard", "status": "running", "stage": "Dashboard Update"}

# --- AUTHENTICATION ROUTES ---
@app.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Use SHA-256 for secure hashing without bcrypt errors
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    new_user = User(username=username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    if not user or user.hashed_password != hashed_pw:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {"message": "Login successful", "username": user.username}

@app.get("/dashboard-stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(ComparisonHistory).count()
    history = db.query(ComparisonHistory).order_by(ComparisonHistory.timestamp.desc()).limit(5).all()
    return {"total_comparisons": total, "recent_history": history}

# --- NLP & COMPARISON ROUTES ---
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

@app.post("/compare-files")
async def compare_files(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    allowed_exts = [".txt", ".pdf", ".docx"]
    old_ext = os.path.splitext(old_file.filename)[1].lower()
    new_ext = os.path.splitext(new_file.filename)[1].lower()
    
    if old_ext not in allowed_exts or new_ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Only TXT, PDF, and DOCX files are allowed.")

    old_path = os.path.join(UPLOAD_DIR, f"old_{old_file.filename}")
    new_path = os.path.join(UPLOAD_DIR, f"new_{new_file.filename}")
    
    with open(old_path, "wb") as buffer:
        shutil.copyfileobj(old_file.file, buffer)
    with open(new_path, "wb") as buffer:
        shutil.copyfileobj(new_file.file, buffer)

    try:
        old_text = extract_text(old_path)
        new_text = extract_text(new_path)
        
        if not old_text.strip() or not new_text.strip():
            raise HTTPException(status_code=400, detail="One or both documents are empty or text could not be extracted.")

        old_sentences = split_into_sentences(old_text)
        new_sentences = split_into_sentences(new_text)
        results = compare_documents(old_sentences, new_sentences)
        
        history_entry = ComparisonHistory(
            old_filename=old_file.filename,
            new_filename=new_file.filename,
            changes_json=json.dumps(results)
        )
        db.add(history_entry)
        db.commit()
        db.refresh(history_entry)
        
        return {
            "old_filename": old_file.filename,
            "new_filename": new_file.filename,
            "total_changes": len(results),
            "comparison": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(old_path): os.remove(old_path)
        if os.path.exists(new_path): os.remove(new_path)

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

# --- FRONTEND SERVING ROUTES ---
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

@app.get("/login", response_class=HTMLResponse)
def serve_login():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    login_file = os.path.abspath(os.path.join(base_dir, "..", "frontend", "login.html"))
    
    if not os.path.exists(login_file):
        return f"<h3>Error: Cannot find {login_file}.</h3>"
        
    with open(login_file, "r", encoding="utf-8") as f:
        return f.read()