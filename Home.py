import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt
import json

# Load service account from secrets
key_dict = st.secrets["firebase_service_account"]
db = firestore.Client.from_service_account_info(key_dict)

st.write("Program is running")
