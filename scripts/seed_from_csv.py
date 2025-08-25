import os, csv
from glob import glob
from backend.db import SessionLocal, Base, engine
from backend.crud import get_or_create_exam, get_or_create_topic, bulk_insert_questions
from backend.models import Topic

Base.metadata.create_all(bind=engine)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
EXAMS_CSV = os.path.join(DATA_DIR, "exams.csv")
TOPICS_CSV = os.path.join(DATA_DIR, "topics.csv")

def parse_options(s): return [p.strip() for p in s.split("|")] if s else []
def parse_correct(s):
    if not s: return []
    s = s.replace(",", ";")
    return [int(x) for x in [p.strip() for p in s.split(";")] if x.isdigit()]

def seed_exams(db):
    title_to_exam = {}
    if not os.path.exists(EXAMS_CSV): return title_to_exam
    with open(EXAMS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            exam = get_or_create_exam(
                db,
                title=row["title"],
                category=row.get("category","General"),
                difficulty=row.get("difficulty","Medium"),
                time_limit=int(row.get("time_limit",60)),
                description=row.get("description","")
            )
            title_to_exam[exam.title] = exam
    return title_to_exam

def seed_topics(db, title_to_exam):
    if not os.path.exists(TOPICS_CSV): return
    with open(TOPICS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            etitle = row["exam_title"].strip()
            tname = row["topic_name"].strip()
            if etitle in title_to_exam:
                get_or_create_topic(db, exam_id=title_to_exam[etitle].id, name=tname)

def seed_questions(db, title_to_exam):
    total = 0
    for path in glob(os.path.join(DATA_DIR, "questions_*.csv")):
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                etitle = row["exam_title"].strip()
                tname = row.get("topic_name","").strip()
                if etitle not in title_to_exam:
                    continue
                # find topic_id if exists
                topic_id = None
                if tname:
                    topic = db.query(Topic).filter(Topic.exam_id==title_to_exam[etitle].id, Topic.name==tname).first()
                    topic_id = topic.id if topic else None
                rows.append({
                    "topic_id": topic_id,
                    "question_text": row["question_text"].strip(),
                    "type": row["type"].strip(),
                    "options": parse_options(row.get("options","")),
                    "correct_answers": parse_correct(row.get("correct_answers","")),
                    "explanation": row.get("explanation",""),
                    "difficulty": row.get("difficulty",""),
                })
        if rows:
            count = bulk_insert_questions(db, exam_id=title_to_exam[etitle].id, rows=rows)
            print(f"{os.path.basename(path)} -> inserted {count}")
            total += count
    print(f"Total inserted: {total}")

def main():
    db = SessionLocal()
    try:
        title_to_exam = seed_exams(db)
        seed_topics(db, title_to_exam)
        seed_questions(db, title_to_exam)
    finally:
        db.close()

if __name__ == "__main__":
    main()
