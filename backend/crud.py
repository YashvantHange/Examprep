from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc, asc
from .models import User, Exam, Topic, Question, Attempt, Answer, Discussion
from .auth import verify_password
from backend.models import Exam, Question
from sqlalchemy import func, desc
from .models import Question, Attempt, Answer


# ---------- Auth ----------
def authenticate(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

# ---------- Exams / Topics ----------
def list_exams(db: Session, q: Optional[str] = None, category: Optional[str] = None,
               difficulty: Optional[str] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    query = db.query(Exam)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(func.lower(Exam.title).like(like))
    if category:
        query = query.filter(Exam.category == category)
    if difficulty:
        query = query.filter(Exam.difficulty == difficulty)
    total = query.count()
    items = query.order_by(Exam.title.asc()).limit(limit).offset(offset).all()
    return {"items": items, "total": total, "limit": limit, "offset": offset}

def get_exam(db, exam_id: int):
    return db.query(Exam).filter(Exam.id == exam_id).first()


def get_or_create_exam(db: Session, *, title: str, category: str, difficulty: str, time_limit: int, description: str="") -> Exam:
    exam = db.query(Exam).filter(func.lower(Exam.title)==title.lower()).first()
    if exam:
        return exam
    exam = Exam(title=title, category=category, difficulty=difficulty, time_limit=time_limit, description=description)
    db.add(exam); db.commit(); db.refresh(exam)
    return exam

def list_topics_by_exam(db: Session, exam_id: int) -> List[Topic]:
    return db.query(Topic).filter(Topic.exam_id==exam_id).order_by(Topic.name.asc()).all()

def get_or_create_topic(db: Session, *, exam_id: int, name: str) -> Topic:
    t = db.query(Topic).filter(Topic.exam_id==exam_id, func.lower(Topic.name)==name.lower()).first()
    if t: return t
    t = Topic(exam_id=exam_id, name=name)
    db.add(t); db.commit(); db.refresh(t)
    return t

# ---------- Questions ----------
def create_question(db: Session, *, exam_id: int, topic_id: Optional[int], question_text: str,
                    type: str, options: Optional[List[str]], correct_answers: List[Any],
                    explanation: Optional[str], difficulty: Optional[str]) -> Question:
    q = Question(
        exam_id=exam_id, topic_id=topic_id, question_text=question_text, type=type,
        options=options, correct_answers=correct_answers, explanation=explanation, difficulty=difficulty
    )
    db.add(q); db.commit(); db.refresh(q)
    return q

def bulk_insert_questions(db: Session, *, exam_id: int, rows: List[dict]) -> int:
    to_add = []
    for r in rows:
        to_add.append(Question(
            exam_id=exam_id,
            topic_id=r.get("topic_id"),
            question_text=r["question_text"],
            type=r["type"],
            options=r.get("options"),
            correct_answers=r.get("correct_answers", []),
            explanation=r.get("explanation"),
            difficulty=r.get("difficulty"),
        ))
    db.bulk_save_objects(to_add)
    db.commit()
    return len(to_add)

def fetch_questions(db: Session, *, exam_id: int, topic_ids: Optional[List[int]] = None,
                    difficulty: Optional[str] = None, limit: int = 20, randomize: bool = True) -> List[Question]:
    q = db.query(Question).filter(Question.exam_id == exam_id)
    if topic_ids:
        q = q.filter(Question.topic_id.in_(topic_ids))
    if difficulty and difficulty.lower() != "random":
        q = q.filter(func.lower(Question.difficulty) == difficulty.lower())
    if randomize:
        q = q.order_by(func.random())
    else:
        q = q.order_by(Question.id.asc())
    return q.limit(limit).all()


def fetch_questions_nonrepeating(
    db,
    exam_id: int,
    user_id: int | None,
    topic_ids: list[int] | None,
    difficulty: str | None,
    limit: int,
    exclude_recent: int = 200,   # window of most recent questions to skip
):
    """
    Randomly sample questions while excluding the user's recent history window.
    If user_id is None, falls back to normal random sampling.
    """
    # base filter
    q = db.query(Question).filter(Question.exam_id == exam_id)

    if topic_ids:
        q = q.filter(Question.topic_id.in_(topic_ids))
    if difficulty:
        q = q.filter(func.lower(Question.difficulty) == difficulty.lower())

    if user_id:
        # last N question_ids answered by this user in this exam
        recent_qids_subq = (
            db.query(Answer.question_id)
              .join(Attempt, Attempt.id == Answer.attempt_id)
              .filter(Attempt.user_id == user_id, Attempt.exam_id == exam_id)
              .order_by(desc(Answer.created_at))
              .limit(exclude_recent)
              .subquery()
        )
        q = q.filter(~Question.id.in_(recent_qids_subq))

    # Postgres random() works via func.random()
    q = q.order_by(func.random()).limit(limit)
    return q.all()


# ---------- Attempts & Answers ----------
def create_attempt(db: Session, *, user_id: Optional[int], exam_id: int, total_questions: int) -> Attempt:
    a = Attempt(user_id=user_id, exam_id=exam_id, total_questions=total_questions)
    db.add(a); db.commit(); db.refresh(a)
    return a

def save_answer(db: Session, *, attempt_id: int, question_id: int, selected_answers, correct: bool, time_spent_seconds: Optional[int] = None) -> Answer:
    ans = Answer(attempt_id=attempt_id, question_id=question_id, selected_answers=selected_answers, correct=correct, time_spent_seconds=time_spent_seconds)
    db.add(ans); db.commit(); db.refresh(ans)
    return ans

def finalize_attempt(db: Session, *, attempt_id: int, score: int, time_taken_seconds: int) -> Attempt:
    a = db.query(Attempt).filter(Attempt.id == attempt_id).first()
    if a:
        from datetime import datetime
        a.score = score
        a.time_taken_seconds = time_taken_seconds
        a.completed_at = datetime.utcnow()
        db.commit(); db.refresh(a)
    return a

def leaderboard_for_exam(db: Session, exam_id: int, limit: int = 20) -> List[Tuple]:
    # Returns list of tuples: (username, score, total_questions, time_taken_seconds, completed_at)
    q = (
        db.query(User.username, Attempt.score, Attempt.total_questions, Attempt.time_taken_seconds, Attempt.completed_at)
        .join(Attempt, Attempt.user_id == User.id)
        .filter(Attempt.exam_id == exam_id, Attempt.score != None)
        .order_by(desc(Attempt.score), asc(Attempt.time_taken_seconds))
        .limit(limit)
    )
    return q.all()

# ---------- Discussions ----------
def add_discussion(db: Session, *, user_id: int, question_id: int, comment: str) -> Discussion:
    d = Discussion(user_id=user_id, question_id=question_id, comment=comment)
    db.add(d); db.commit(); db.refresh(d)
    return d

def list_discussions_for_question(db: Session, question_id: int) -> List[Discussion]:
    return db.query(Discussion).filter(Discussion.question_id == question_id).order_by(Discussion.created_at.desc()).all()

def get_exam_by_id(db, exam_id: int):
    """Fetch a single exam by ID"""
    return db.query(Exam).filter(Exam.id == exam_id).first()

def get_questions_for_exam(db, exam_id: int, limit: int = None):
    """Fetch all questions for a given exam"""
    q = db.query(Question).filter(Question.exam_id == exam_id)
    if limit:
        q = q.limit(limit)
    return q.all()
