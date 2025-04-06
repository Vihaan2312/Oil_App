import streamlit as st
from google.cloud import firestore
import pandas as pd
import datetime as dt

class OilApp:
    def __init__(self):
        # Initialization code
        self.db = firestore.Client()
        self.today = dt.datetime.now()
        st.write("App initialized")

    def run(self):
        # Main logic of the app
        st.write("Program is running")

# Create an instance and run the app
app = OilApp()
app.run()
