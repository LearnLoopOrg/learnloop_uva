import streamlit as st
import json

with open("data/uva_dummy_db.json", "r") as f:
    string = f.read()
    st.markdown(string)


with open("data/uva_dummy_db.json", "r") as f:
    data = json.load(f)

st.markdown(data["university_name"])
