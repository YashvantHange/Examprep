import time
from datetime import datetime, timedelta
import streamlit as st
from backend.db import SessionLocal
from backend.crud import (
    fetch_questions,
    create_attempt,
    save_answer,
    finalize_attempt,
    list_topics_by_exam,
    get_exam,           # make sure this exists; returns Exam by id
)
from backend.models import Question
from sqlalchemy import func
st.set_page_config(
    page_title="Take Exam",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",  # <- collapse sidebar on load
)

st.set_page_config(page_title="Take Exam", page_icon="📝", layout="wide")

# --- 0) Bootstrap from URL if session was cleared (browser refresh)
qp = st.query_params
if "exam_selected" not in st.session_state:
    # Try to reconstruct from URL
    exam_id = qp.get("exam_id")
    if exam_id:
        db = SessionLocal()
        ex = get_exam(db, int(exam_id))
        db.close()
        if ex:
            st.session_state["exam_selected"] = {
                "id": ex.id,
                "title": ex.title,
                "category": ex.category,
                "difficulty": ex.difficulty,
                "time_limit": ex.time_limit,
                "description": ex.description or "",
            }
            st.session_state["exam_started"] = True
            # also restore chosen config if present
            if "n" in qp:
                st.session_state["num_questions"] = int(qp.get("n"))
            if "difficulty" in qp:
                st.session_state["difficulty"] = qp.get("difficulty")
            if "topics" in qp:
                st.session_state["topics_selected"] = qp.get("topics").split(",")
        # else: fall through to guard

# --- Guards
if "exam_selected" not in st.session_state or not st.session_state.get("exam_started"):
    st.warning("Please configure the exam first.")
    st.stop()

exam = st.session_state["exam_selected"]
num_q = st.session_state.get("num_questions", 10)
difficulty = st.session_state.get("difficulty", "Random")
selected_topic_names = st.session_state.get("topics_selected", [])

# --- 1) If we already have question_payload in session, use it.
# Otherwise try to rebuild from URL (q & end); if not present, fetch and freeze new questions.
if "question_payload" not in st.session_state:
    if "q" in st.query_params and "end" in st.query_params:
        # Rebuild from URL params
        ids = [int(x) for x in st.query_params.get("q").split(",") if x.strip().isdigit()]
        end_ts = int(st.query_params.get("end"))

        db = SessionLocal()
        # Fetch those questions in a single query
        qs = db.query(Question).filter(Question.id.in_(ids)).all()
        by_id = {q.id: q for q in qs}
        ordered = [by_id[i] for i in ids if i in by_id]

        st.session_state["question_payload"] = [
            {
                "id": q.id,
                "question_text": q.question_text,
                "type": q.type,
                "options": q.options or (["True", "False"] if q.type == "TRUE_FALSE" else []),
                "correct_answers": q.correct_answers or [],
                "explanation": getattr(q, "explanation", None),
            }
            for q in ordered
        ]
        st.session_state["end_time"] = end_ts

        # attempt_id may or may not exist; if missing, create it
        if "attempt_id" not in st.session_state:
            db2 = SessionLocal()
            user_id = st.session_state.get("user", {}).get("id")
            attempt = create_attempt(db2, user_id=user_id, exam_id=exam["id"], total_questions=len(ordered))
            st.session_state["attempt_id"] = attempt.id
            db2.close()

        db.close()
    else:
        # Fresh fetch + freeze + write to URL for resume
        db = SessionLocal()

        topics_all = list_topics_by_exam(db, exam_id=exam["id"])
        name_to_id = {t.name: t.id for t in topics_all}
        topic_ids = [name_to_id[n] for n in selected_topic_names if n in name_to_id]

        questions = fetch_questions(
            db,
            exam_id=exam["id"],
            topic_ids=topic_ids if topic_ids else None,
            difficulty=difficulty if difficulty and difficulty.lower() != "random" else None,
            limit=num_q,
            randomize=True,
        )

        payload = [
            {
                "id": q.id,
                "question_text": q.question_text,
                "type": q.type,
                "options": q.options or (["True", "False"] if q.type == "TRUE_FALSE" else []),
                "correct_answers": q.correct_answers or [],
                "explanation": getattr(q, "explanation", None),
            }
            for q in questions
        ]
        st.session_state["question_payload"] = payload

        # Create attempt (once)
        user_id = st.session_state.get("user", {}).get("id")
        attempt = create_attempt(db, user_id=user_id, exam_id=exam["id"], total_questions=len(payload))
        st.session_state["attempt_id"] = attempt.id

        # Timer init
        end_ts = (datetime.utcnow() + timedelta(minutes=exam["time_limit"])).timestamp()
        st.session_state["end_time"] = int(end_ts)

        # Write resume params into the URL
        st.query_params["q"] = ",".join(str(x["id"]) for x in payload)
        st.query_params["end"] = str(int(end_ts))
        # keep previously set params from Configure page
        st.query_params["exam_id"] = str(exam["id"])
        st.query_params["n"] = str(num_q)
        st.query_params["difficulty"] = difficulty
        if selected_topic_names:
            st.query_params["topics"] = ",".join(selected_topic_names)
        else:
            st.query_params.pop("topics", None)

        db.close()

# --- 2) Always work off frozen payload
qpayload = st.session_state["question_payload"]

st.title(f"📝 {exam['title']} — Test")
st.caption(f"Difficulty: {difficulty} · Questions: {len(qpayload)} · Time Limit: {exam['time_limit']} min")

# --- 3) Timer (live clock via JS) + autosubmit check
end_ts = st.session_state.get("end_time")
remaining = max(0, int(end_ts - datetime.utcnow().timestamp())) if end_ts else 0

st.components.v1.html(f"""
    <div id="timer" style="font-size:22px; font-weight:bold; color:#d9534f; margin:10px 0;">
        Loading timer...
    </div>
    <script>
        var remaining = {remaining};
        var el = document.getElementById('timer');
        function tick() {{
            var m = Math.floor(remaining / 60);
            var s = remaining % 60;
            el.textContent = "⏱️ Time remaining: " + String(m).padStart(2,'0') + ":" + String(s).padStart(2,'0');
            remaining -= 1;
            if (remaining < 0) {{
                el.textContent = "⏱️ Time's up!";
                clearInterval(iv);
            }}
        }}
        tick();
        var iv = setInterval(tick, 1000);
    </script>
""", height=50)

if remaining <= 0 and not st.session_state.get("submitted"):
    st.warning("Time's up! Submitting automatically…")
    st.session_state["auto_submit"] = True

# --- 4) Collect responses (no default tick)
answers = []
for i, q in enumerate(qpayload, 1):
    st.subheader(f"Q{i}. {q['question_text']}")
    key = f"q_{q['id']}"
    opts = q["options"]
    if q["type"] == "MULTI_SELECT":
        sel = st.multiselect("Select all that apply:", opts, key=key, default=[])
    else:
        sel = st.radio("Select one:", opts, key=key, index=None)
    answers.append((q, sel))

# --- 5) Submit + review
# --- Submit
manual_submit = st.button("Submit & Review ✅")

if manual_submit or st.session_state.get("auto_submit"):
    st.session_state["submitted"] = True

    db = SessionLocal()
    correct_count = 0

    st.markdown("---")
    st.header("📊 Review")

    for idx, (q, sel) in enumerate(answers, start=1):
        # q is a DICT from the frozen payload
        opts = q["options"]
        qtype = q["type"]
        correct_idxs = q["correct_answers"] or []
        is_correct = False

        if qtype == "MULTI_SELECT":
            your_set = set(sel)
            correct_set = set(opts[i] for i in correct_idxs) if correct_idxs else set()
            is_correct = your_set == correct_set
            your_label = ", ".join(sel) if sel else "—"
            correct_label = ", ".join(correct_set) if correct_set else "—"
        else:
            # Single choice (MCQ / TRUE_FALSE)
            if sel is None:
                is_correct = False
                your_label = "—"
                correct_idx = correct_idxs[0] if correct_idxs else -1
            else:
                correct_idx = correct_idxs[0] if correct_idxs else -1
                is_correct = (opts.index(sel) == correct_idx) if (sel in opts and correct_idx >= 0) else False
                your_label = sel

            correct_label = opts[correct_idx] if (correct_idx >= 0 and correct_idx < len(opts)) else "—"

        if is_correct:
            correct_count += 1
            st.success(f"Q{idx}: Correct ✅")
        else:
            st.error(f"Q{idx}: Incorrect ❌")

        st.write(f"**Your answer:** {your_label}")
        st.write(f"**Correct answer:** {correct_label}")
        if q.get("explanation"):
            with st.expander("Explanation"):
                st.write(q["explanation"])

        # Persist the answer
        selected_payload = sel if qtype == "MULTI_SELECT" else ([sel] if isinstance(sel, str) else sel)
        save_answer(
            db,
            attempt_id=st.session_state["attempt_id"],
            question_id=q["id"],
            selected_answers=selected_payload if selected_payload is not None else [],
            correct=is_correct,
            time_spent_seconds=None,
        )

    # finalize attempt
    remaining = max(0, int(st.session_state.get("end_time", 0) - datetime.utcnow().timestamp()))
    elapsed = exam["time_limit"] * 60 - remaining
    finalize_attempt(db, attempt_id=st.session_state["attempt_id"], score=correct_count, time_taken_seconds=elapsed)
    db.close()

    st.markdown("---")
    st.success(f"**Final Score:** {correct_count} / {len(st.session_state['question_payload'])}")

    colA, colB = st.columns(2)
    if colA.button("🏁 Finish"):
        for k in ["exam_started","auto_submit","attempt_id","question_payload","submitted","end_time"]:
            st.session_state.pop(k, None)
        for k in ["q","end"]:
            st.query_params.pop(k, None)
        st.switch_page("app.py")

    if colB.button("🔁 Retake Now"):
        for k in ["exam_started","auto_submit","attempt_id","question_payload","submitted","end_time"]:
            st.session_state.pop(k, None)
        for k in ["q","end"]:
            st.query_params.pop(k, None)
        st.session_state["exam_started"] = True
        st.experimental_rerun()
