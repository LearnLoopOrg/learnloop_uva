import streamlit as st

# Input area for the user to edit text
user_input = st.text_area(
    "Edit your text here:",
    "In deze fase van het project is het **cruciaal** om een duidelijke **strategie** te hebben. We moeten **focus** behouden en onze **doelen** helder voor ogen houden. Alleen zo kunnen we de **efficiëntie** van ons team optimaliseren en het gewenste **resultaat** behalen.",
)

import streamlit as st
from streamlit_quill import st_quill

# Initial input text
input_text = "In deze fase van het project is het <strong>cruciaal</strong> om een duidelijke <strong>strategie</strong> te hebben."

# st.markdown(
#     """
#     <style>
#     /* Adjust the iframe height */
#     iframe[title="streamlit_quill.streamlit_quill"] {
#         height: 100px !important; /* Set your desired height here */
#         border: 2px solid #0000; /* Set your desired border color here */
#     }

#     /* Adjust the border of the Quill editor */
#     .ql-container {
#         border: 2px solid #0000 !important; /* Set your desired border color here */
#         border-radius: 5px; /* Set your desired border radius
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )


# Define a custom toolbar
custom_toolbar = [
    ["bold", "italic", "underline"],  # Text style
    ["link"],  # Insert link
]

# Display a rich text editor with a custom toolbar
user_input = st_quill(value=input_text, html=True, toolbar=custom_toolbar)

# import streamlit as st
# from streamlit_input_box import input_box

# state = st.session_state

# if "texts" not in state:
#     state.texts = []

# text = input_box(min_lines=3, max_lines=10, just_once=True)

# if text:
#     state.texts.append(text)

# for text in state.texts:
#     st.text(text)


import streamlit as st
from streamlit_quill import st_quill

# CSS to adjust the border of the Quill editor
st.markdown(
    """
    <style>
    /* Remove the top border */
    .ql-container.ql-snow {
        border-top: 0;
    }
    
    /* Adjust the border color */
    .ql-container {
        border: 1px solid #3498db !important; /* Replace with your desired color */
        box-sizing: border-box;
        font-family: Helvetica, Arial, sans-serif;
        font-size: 13px;
        height: 100%;
        margin: 0;
        position: relative;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Quill editor
content = st_quill(value="Your text here")

# Output
st.write(content)
