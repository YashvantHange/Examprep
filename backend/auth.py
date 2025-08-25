import streamlit as st
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return _pwd.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return _pwd.verify(p, hashed)

def login_user(user_dict: dict):
    st.session_state["user"] = user_dict

def logout_user():
    if "user" in st.session_state:
        del st.session_state["user"]

def current_user():
    return st.session_state.get("user")
