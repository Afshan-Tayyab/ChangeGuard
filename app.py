# app.py
import streamlit as st
import sys
import os
import json
import tempfile
import hashlib
import spacy

# Load the spaCy model (it is installed via requirements.txt)
nlp = spacy.load("en_core_web_sm")

# Add backend to path so Streamlit can find the NLP engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from database import SessionLocal, engine, Base, ComparisonHistory, User
from services.text_extractor import extract_text
from services.semantic_analyzer import split_into_sentences
from services.change_detector import compare_documents

Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="ChangeGuard", page_icon="🛡️", layout="wide")

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# --- AUTHENTICATION ---
def login_page():
    st.title("🛡️ ChangeGuard Login")
    st.markdown("### NLP-Based Semantic Change Detection")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            db = SessionLocal()
            user = db.query(User).filter(User.username == username).first()
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            if user and user.hashed_password == hashed_pw:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials.")
            db.close()
            
    with tab2:
        new_user = st.text_input("New Username", key="reg_user")
        new_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            db = SessionLocal()
            if db.query(User).filter(User.username == new_user).first():
                st.error("Username already exists.")
            else:
                hashed_pw = hashlib.sha256(new_pass.encode()).hexdigest()
                db.add(User(username=new_user, hashed_password=hashed_pw))
                db.commit()
                st.success("Account created! Please login.")
            db.close()

# --- MAIN APP ---
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    menu = st.sidebar.radio("Navigation", ["Dashboard", "Compare Documents", "History", "About"])
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # DASHBOARD
    if menu == "Dashboard":
        st.title("📊 Dashboard")
        db = SessionLocal()
        total = db.query(ComparisonHistory).count()
        st.metric("Total Comparisons", total)
        db.close()
        
    # COMPARE DOCUMENTS
    elif menu == "Compare Documents":
        st.title("📄 Compare Documents")
        
        col1, col2 = st.columns(2)
        with col1:
            old_file = st.file_uploader("Upload Old Document", type=["txt", "pdf", "docx"])
        with col2:
            new_file = st.file_uploader("Upload New Document", type=["txt", "pdf", "docx"])
            
        if st.button("Compare Documents", type="primary"):
            if old_file and new_file:
                with st.spinner("Extracting text and analyzing with NLP..."):
                    # Save uploaded files temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{old_file.name.split('.')[-1]}") as tmp_old:
                        tmp_old.write(old_file.getvalue())
                        old_path = tmp_old.name
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{new_file.name.split('.')[-1]}") as tmp_new:
                        tmp_new.write(new_file.getvalue())
                        new_path = tmp_new.name
                        
                    try:
                        old_text = extract_text(old_path)
                        new_text = extract_text(new_path)
                        
                        old_sentences = split_into_sentences(old_text)
                        new_sentences = split_into_sentences(new_text)
                        results = compare_documents(old_sentences, new_sentences)
                        
                        # Save to Database
                        db = SessionLocal()
                        db.add(ComparisonHistory(
                            old_filename=old_file.name,
                            new_filename=new_file.name,
                            changes_json=json.dumps(results)
                        ))
                        db.commit()
                        db.close()
                        
                        st.success("Comparison Complete!")
                        
                        # Display Results
                        for item in results:
                            if item["status"] == "Modified":
                                st.warning(f"**MODIFIED**")
                                st.write(f"**Old:** {item['old_sentence']}")
                                st.write(f"**New:** {item['new_sentence']}")
                                for change in item["changes_detected"]:
                                    st.info(f"**{change['type']}**\n\n**Old:** {change['old']} | **New:** {change['new']}\n\n*Impact:* {change['impact']}")
                                st.markdown("---")
                            elif item["status"] == "Unchanged":
                                st.success(f"**UNCHANGED:** {item['old_sentence']}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        os.remove(old_path)
                        os.remove(new_path)

    # HISTORY
    elif menu == "History":
        st.title("🕰️ Comparison History")
        db = SessionLocal()
        history = db.query(ComparisonHistory).order_by(ComparisonHistory.timestamp.desc()).all()
        db.close()
        
        if not history:
            st.info("No history available.")
        else:
            for h in history:
                with st.expander(f"ID: {h.id} | {h.old_filename} → {h.new_filename} | {h.timestamp.strftime('%Y-%m-%d %H:%M')}"):
                    st.json(json.loads(h.changes_json))

    # ABOUT
    elif menu == "About":
        st.title("About ChangeGuard")
        st.markdown("""
        ChangeGuard is an NLP-based document comparison system that identifies changes in meaning between old and updated documents. 
        It detects changes in conditions, permissions, obligations, deadlines, restrictions, and exceptions, and explains their possible impact.
        
        **Technologies:** Python, FastAPI, spaCy, scikit-learn, NLTK, SQLite, Streamlit.
        """)

# --- ROUTER ---
if not st.session_state.logged_in:
    login_page()
else:
    main_app()