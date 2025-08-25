import os
import streamlit as st
from dotenv import load_dotenv
from backend.db import Base, engine, SessionLocal
from backend.auth import current_user, login_user, logout_user
from backend.crud import authenticate, list_exams

load_dotenv()
APP_TITLE = os.getenv("APP_TITLE", "ExamPrep Pro")

st.set_page_config(
    page_title="ExamPrep Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",  # <- collapse sidebar on load
)


st.set_page_config(page_title=APP_TITLE, page_icon="📝", layout="wide")

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Sidebar auth
st.sidebar.title(APP_TITLE)

st.title("📝 Welcome to ExamPrep Pro")
st.write("Pick an exam to begin.")

db = SessionLocal()
res = list_exams(db, limit=100, offset=0)
items = res["items"]
db.close()

if not items:
    st.info("No exams found. Seed data in the Admin or via CSV seeding script.")
    st.stop()

cols = st.columns(3)
for i, e in enumerate(items):
    with cols[i % 3]:
        with st.container(border=True):
            st.subheader(e.title)
            st.caption(f"Category: **{e.category}** · Base Difficulty: **{e.difficulty}** · Time: **{e.time_limit}** min")
            st.write(e.description or "")
            c1, c2, c3 = st.columns(3)
            if c1.button("▶️ Start", key=f"start_{e.id}"):
                st.session_state["exam_selected"] = {
                    "id": e.id, "title": e.title, "category": e.category,
                    "difficulty": e.difficulty, "time_limit": e.time_limit,
                    "description": e.description
                }
                st.switch_page("pages/7_Configure_Exam.py")
            

