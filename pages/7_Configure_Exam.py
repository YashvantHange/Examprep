import streamlit as st
from backend.db import SessionLocal
from backend.crud import list_topics_by_exam
st.set_page_config(
    page_title="Configure Exam",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",  # <- collapse sidebar on load
)

st.set_page_config(page_title="Configure Exam", page_icon="⚙️", layout="centered")

if "exam_selected" not in st.session_state:
    st.warning("Open an exam from the homepage first.")
    st.stop()

exam = st.session_state["exam_selected"]
st.title(f"⚙️ Configure: {exam['title']}")

db = SessionLocal()
topics = list_topics_by_exam(db, exam_id=exam["id"])
db.close()

topic_names = [t.name for t in topics] if topics else []
selected_topics = st.multiselect("Topics (optional):", options=topic_names, default=topic_names)

difficulty = st.selectbox("Difficulty", ["Random", "Easy", "Medium", "Hard"], index=0)
num_questions = st.number_input("Number of questions", min_value=1, max_value=500, value=20, step=1)

col1, col2 = st.columns(2)

# inside the Start button handler (you already clear old state here)
if col1.button("Start Exam 🚀"):
    # Clear any earlier attempt cache
    for k in ["question_payload", "attempt_id", "submitted", "auto_submit", "end_time"]:
        st.session_state.pop(k, None)

    st.session_state["topics_selected"] = selected_topics
    st.session_state["difficulty"] = difficulty
    st.session_state["num_questions"] = num_questions
    st.session_state["exam_started"] = True

    # NEW: put the minimal config in the URL (so refresh can recover)
    st.query_params["exam_id"] = str(exam["id"])
    st.query_params["n"] = str(num_questions)
    st.query_params["difficulty"] = difficulty
    if selected_topics:
        st.query_params["topics"] = ",".join(selected_topics)
    else:
        st.query_params.pop("topics", None)

    st.switch_page("pages/3_Take_Exam.py")

if col2.button("Back"):
    st.session_state.pop("exam_selected", None)
    st.rerun()



