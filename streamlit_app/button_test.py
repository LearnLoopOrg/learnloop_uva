import streamlit as st

# Controleer of 'button_clicked' in de sessiestatus zit, anders initialiseert het
if 'button_clicked' not in st.session_state:
    st.session_state['button_clicked'] = False

# Functie om de knopstatus te veranderen
def button_click():
    st.session_state['button_clicked'] = not st.session_state['button_clicked']

# HTML en CSS voor knoppen
button_html = f"""
    <style>
    .special-button {{
        background-color: {'red' if st.session_state['button_clicked'] else 'green'};
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
    }}
    .other-button {{
        background-color: blue;
        color: white;
        border: none;
        padding: 10px 20px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
    }}
    </style>
    <button class="special-button" onclick="document.getElementById('special-button-form').submit();">
        Special Button
    </button>
    <button class="other-button">
        Another Button
    </button>
    <button class="other-button">
        Yet Another Button
    </button>
    <form id="special-button-form" action="" method="post">
        <input type="hidden" name="special_button" value="clicked" />
    </form>
"""

# Check of de speciale knop is ingedrukt door het controleren van de post-waarde
if st.experimental_get_query_params().get("special_button"):
    button_click()

# Voeg de HTML-inhoud toe aan de Streamlit-app
st.markdown(button_html, unsafe_allow_html=True)

# Andere inhoud gebaseerd op knopstatus
if st.session_state['button_clicked']:
    st.write("De special button is ingedrukt!")
else:
    st.write("De special button is niet ingedrukt.")
