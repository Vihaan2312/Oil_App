import streamlit as st
from google.cloud import firestore


def init():
    creds = st.secrets["firestore"]
    return firestore.Client.from_service_account_info(dict(creds))

def load():
    creds = st.secrets["firestore"]
    db = firestore.Client.from_service_account_info(dict(creds))
    orders = list(db.collection("Orders").stream())
    return [doc.to_dict() for doc in orders]

def pro_load():
    creds = st.secrets["firestore"]
    db = firestore.Client.from_service_account_info(dict(creds))
    return db.collection("Profiles").stream()

def oil_load():
    creds = st.secrets["firestore"]
    db = firestore.Client.from_service_account_info(dict(creds))
    return db.collection("Rates").stream()