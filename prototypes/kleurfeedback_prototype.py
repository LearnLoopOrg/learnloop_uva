import streamlit as st
import re

# Input: de gemarkeerde tekst
text = """
De factoren zijn:

- (groen) te weinig eten kan lichamelijke klachten met zich meebrengen waardoor organen uitvallen (groen).
- (oranje) hun mentale staat gaat enorm achteruit door te weinig eten, maar ook doordat ze mentaal lijden aan OCD bijvoorbeeld (oranje).
- (oranje) De multifactoriële behandeling speelt daarop in door te kijken naar deze verschillende aspecten (oranje) [door zowel fysieke gezondheid te herstellen als psychologische ondersteuning te bieden om de psychische belasting, waaronder het zelfmoordrisico, te verminderen].
"""


# Functie om tekst met de juiste kleur te markeren
def highlight_text(text):
    # Definieer kleurcodes volgens jouw voorkeur
    color_dict = {
        "groen": "#edf3ec",  # Groene markering
        "oranje": "#fbedd6",  # Oranje markering
        "rood": "#fdebec",  # Rode markering (voor foute delen)
        "blauw": "#e7f3f8",  # Blauw voor toegevoegde tekst
    }

    # Zoek patronen zoals (kleur) tekst (kleur)
    pattern = r"\((groen|oranje|rood)\)(.*?)\(\1\)"

    # Vervang elk gemarkeerd stuk met de corresponderende HTML-code voor achtergrondkleur
    def replace_match(match):
        color = match.group(1)
        content = match.group(2)
        color_code = color_dict[color]
        return f'<span style="background-color:{color_code}; border-radius: 5px; padding: 2px 4px;">{content.strip()}</span>'

    # Gebruik regex om de tekst te parsen en te markeren
    highlighted_text = re.sub(pattern, replace_match, text)

    # Voeg HTML toe voor de toegevoegde delen in vierkante haakjes (blauw markeren)
    highlighted_text = re.sub(
        r"\[([^\]]+)\]",
        r'<span style="background-color:#e7f3f8; border-radius: 5px; padding: 2px 4px;">\1</span>',
        highlighted_text,
    )

    return highlighted_text


st.title("Gemarkeerde Samenvatting")
highlighted_text = highlight_text(text)
st.markdown(highlighted_text, unsafe_allow_html=True)
