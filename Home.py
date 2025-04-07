import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt

db = firestore.Client.from_service_account_info("Firestore.json")

st.write("Program is running")
