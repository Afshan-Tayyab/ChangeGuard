# ChangeGuard: NLP-Based Semantic Change Detection

## How to Run
1. Open terminal in the `ChangeGuard` folder.
2. Activate environment: `.\venv\Scripts\Activate.ps1`
3. Go to backend: `cd backend`
4. Run server: `uvicorn main:app --reload`
5. Open browser to: `http://127.0.0.1:8000/app/`

## Technologies Used
- **FastAPI** (Backend Server)
- **spaCy** (NLP processing, POS tagging, Dependency Parsing)
- **scikit-learn** (TF-IDF Similarity)
- **PyMuPDF & python-docx** (Document extraction)
- **HTML/CSS/JS** (Frontend UI)

## Project Features
- Semantic change detection (Modality, Negation, Action, Subject, Object).
- Sentence matching using TF-IDF cosine similarity.
- Context-aware impact explanations.
