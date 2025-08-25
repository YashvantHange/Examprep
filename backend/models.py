from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempts = relationship("Attempt", back_populates="user")

class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False, unique=True)
    category = Column(String, index=True, nullable=False)
    difficulty = Column(String, index=True, nullable=False)  # Easy, Medium, Hard (overall baseline)
    time_limit = Column(Integer, nullable=False)  # minutes
    description = Column(Text, default="")

    topics = relationship("Topic", back_populates="exam", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="exam", cascade="all, delete-orphan")

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)

    exam = relationship("Exam", back_populates="topics")
    questions = relationship("Question", back_populates="topic")

    __table_args__ = (UniqueConstraint('exam_id', 'name', name='uq_topic_per_exam'),)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"))
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    question_text = Column(Text, nullable=False)
    type = Column(String, nullable=False)  # MCQ, TRUE_FALSE, MULTI_SELECT
    options = Column(JSON, nullable=True)  # list[str] or None
    correct_answers = Column(JSON, nullable=False)  # list[int|bool|str]
    explanation = Column(Text, nullable=True)
    difficulty = Column(String, nullable=True)  # per-question: Easy/Medium/Hard (optional)

    exam = relationship("Exam", back_populates="questions")
    topic = relationship("Topic", back_populates="questions")
    answers = relationship("Answer", back_populates="question")

class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    exam_id = Column(Integer, ForeignKey("exams.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    total_questions = Column(Integer, nullable=True)
    time_taken_seconds = Column(Integer, nullable=True)

    user = relationship("User", back_populates="attempts")
    exam = relationship("Exam", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt")

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    selected_answers = Column(JSON, nullable=False)  # list[int|bool|str]
    correct = Column(Boolean, default=False)
    time_spent_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attempt = relationship("Attempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")

class Discussion(Base):
    __tablename__ = "discussions"
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
