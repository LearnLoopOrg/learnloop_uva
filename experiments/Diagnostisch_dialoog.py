import streamlit as st
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

load_dotenv()


def connect_to_openai():
    OPENAI_API_KEY = os.getenv("LL_AZURE_OPENAI_API_KEY")
    OPENAI_API_ENDPOINT = os.getenv("LL_AZURE_OPENAI_API_ENDPOINT")
    return AzureOpenAI(
        api_key=OPENAI_API_KEY,
        api_version="2024-04-01-preview",
        azure_endpoint=OPENAI_API_ENDPOINT,
    )


class SamenvattenInDialoog:
    def __init__(self):
        self.client = connect_to_openai()
        self.initialize_session_state()

    def initialize_session_state(self):
        """
        Initialize session variables if they don't exist.
        """
        if "openai_model" not in st.session_state:
            st.session_state.openai_model = "LLgpt-4o"

        if "messages" not in st.session_state:
            st.session_state.messages = []

    def display_chat_messages(self):
        """
        Display chat messages in the Streamlit app.
        """
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"], avatar="🔵" if message["role"] == "assistant" else "🔘"
            ):
                st.markdown(message["content"])

    def add_to_assistant_responses(self, response):
        """
        Add the response message to the chat.
        """
        st.session_state.messages.append({"role": "assistant", "content": response})

    def add_to_user_responses(self, user_input):
        """
        Add the user input to the chat.
        """
        st.session_state.messages.append({"role": "user", "content": user_input})

    def generate_assistant_response(self):
        """
        Generate a response from the assistant.
        """
        samenvatting = """

#### ## Zuur-Base Reactie
- Een zuur doneert protonen (1 punt) aan een base (1 punt) tijdens de reactie (1 punt).

#### ## Productie van Insuline en Glycogeen
- De productie van insuline (1 punt) en glycogeen (1 punt) door de lever (1 punt).

#### ## Watercyclus
- **Verdamping:** Water verdampt uit oceanen en meren (1 punt).  
- **Condensatie:** Waterdamp vormt wolken (1 punt).  
- **Neerslag:** Water valt terug naar de aarde als regen of sneeuw (1 punt).  
- **Infiltratie:** Water sijpelt de bodem in (1 punt).

#### ## Fotosynthese
- Fotosynthese vindt plaats in chloroplasten (1 punt) en gebruikt lichtenergie (1 punt) om kooldioxide (1 punt) en water (1 punt) om te zetten in glucose (1 punt) en zuurstof (1 punt).

#### ## Nucleotiden
- Nucleotiden bestaan uit een suiker (1 punt), een fosfaatgroep (1 punt) en een stikstofbase (1 punt).

#### ## Circulatiesysteem
- Het circulatiesysteem omvat het hart (1 punt), bloedvaten (1 punt) en bloed (1 punt).

#### ## Celdeling
- **Profase:** Chromosomen condenseren (1 punt).  
- **Metafase:** Chromosomen lijnen zich op in het midden van de cel (1 punt).  
- **Anafase:** Zusterchromatiden worden gescheiden (1 punt).  
- **Telofase:** Kernomhulsels vormen zich rond de gescheiden chromatiden (1 punt).

#### ## Genexpressie
- **Stap 1:** DNA wordt omgezet in mRNA (1 punt).  
- **Stap 2:** mRNA wordt gesponnen en bewerkt (1 punt).  
- **Stap 3:** mRNA wordt vertaald naar een eiwit in het ribosoom (1 punt).  
- **Stap 4:** Eiwit wordt gevouwen en geactiveerd (1 punt).

#### ## Verschillen tussen Plantencellen en Diercellen
- Plantencellen bevatten chloroplasten (1 punt), diercellen niet (1 punt).

#### ## Enzymen
- Enzymen versnellen chemische reacties (1 punt) door het verlagen van de activeringsenergie (1 punt).

#### ## DNA
- DNA bevat genetische informatie (1 punt) in de vorm van basenparen (1 punt) die coderingsinstructies (1 punt) leveren.

#### ## Verschil tussen Prokaryoten en Eukaryoten
- Prokaryoten hebben geen kern (1 punt), terwijl eukaryoten een goed gedefinieerde kern hebben (1 punt).

#### ## Leverziekten
- Leverziekten hebben weinig invloed (1 punt) op de spijsvertering (1 punt) en stofwisseling (1 punt).

#### ## Anaërobe en Aerobe Ademhaling
- Anaërobe ademhaling vindt plaats zonder zuurstof (1 punt), terwijl aerobe ademhaling zuurstof vereist (1 punt).

#### ## Symptomen van Griep
- **Hoge koorts** (1 punt).  
- **Hoofdpijn** (1 punt).  
- **Spierpijn** (1 punt).  
- **Vermoeidheid** (1 punt).
- **Keelpijn** (1 punt).

"""
        role_prompt = f"""
Je gaat een socratische dialoog voeren met een student die een onderwerp probeert samen te vatten. De samenvatting die je moet begeleiden is opgedeeld in verschillende onderwerpen en subonderwerpen. Elk belangrijk element is voorzien van punten, die aangeven wat de student moet noemen om de volledige samenvatting goed te hebben. Je doel is om de student te helpen alle punten te benoemen, zonder deze direct voor te zeggen.

**Hoe gebruik je de samenvatting tijdens het gesprek?**

1. **Start met een algemene vraag:** Begin elk onderwerp door een brede vraag te stellen over dat onderwerp. Bijvoorbeeld: "Wat weet je over de zuur-base reactie?" Hierdoor stimuleer je de student om zijn huidige kennis uit te leggen.

2. **Vergelijk de antwoorden:** Vergelijk het antwoord van de student met de punten in de samenvatting. Als de student één of meerdere punten correct benoemt, markeer je deze mentaal als 'behandeld'.

3. **Identificeer ontbrekende elementen:** Zodra je merkt dat bepaalde punten nog niet genoemd zijn, stel je vragen die de student naar deze ontbrekende elementen leiden. Begin met abstracte vragen en maak ze steeds concreter als de student de antwoorden niet meteen weet.
   - **Voorbeeld abstracte vraag:** "Hoe denk je dat een zuur reageert met een base in een reactie?"  
   - **Voorbeeld concretere vraag:** "Wat gebeurt er met de protonen tijdens de zuur-base reactie?"

4. **Herhaal het proces:** Zodra alle punten voor een onderwerp besproken zijn, vraag dan of de student het onderwerp zou willen samenvatting in zijn eigen woorden. Daarna ga je door naar het volgende onderwerp in de samenvatting. Stel weer een brede vraag om te beginnen en werk op dezelfde manier totdat de student alle onderwerpen en punten heeft besproken.

5. **Check je werk:** Vraag regelmatig aan de student of hij of zij denkt dat alle belangrijke punten besproken zijn. Indien nodig, geef een korte samenvatting van wat al behandeld is en vraag of er nog iets ontbreekt.

6. **Sluit af:** Vraag de student aan het eind om een korte samenvatting te geven van alles wat besproken is. Bevestig dat de student nu alle punten van de samenvatting heeft geraakt.

**Voorbeeld:**

Uitvoerder: "Wat weet je al over de watercyclus?"

Student: "Water verdampt uit de oceanen en vormt wolken."

Uitvoerder: "Goed, dat is de verdamping en condensatie. Wat gebeurt er daarna in de cyclus?" (student kan vervolgens verder praten over neerslag en infiltratie).

### Samenvatting:
{samenvatting}

### Gesprek met student:

"""
        stream = self.client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=[
                {"role": "system", "content": role_prompt},
                *(
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ),
            ],
            stream=True,
        )

        return stream

    def handle_user_input(self):
        """
        Process user input and generate a response.
        """
        if user_input := st.chat_input("Jouw antwoord"):
            self.add_to_user_responses(user_input)
            with st.chat_message("user", avatar="🔘"):
                st.markdown(f"{user_input}")

            with st.chat_message("assistant", avatar="🔵"):
                response = st.write_stream(self.generate_assistant_response())
                self.add_to_assistant_responses(response)

                if (
                    st.session_state.messages[-1]["content"]
                    == "Top! Laten we doorgaan naar de volgende fase."
                ):
                    st.write("Einde van de sessie. Bedankt voor het samenvatten!")

    def run(self):
        self.initialize_session_state()

        st.title("Samenvatten in dialoog")

        if st.session_state.messages == []:
            intro_text = "We gaan samen de belangrijkste punten van het college samenvatten. Zullen we beginnen?"
            self.add_to_assistant_responses(intro_text)

        self.display_chat_messages()
        self.handle_user_input()


if __name__ == "__main__":
    probleemstelling = SamenvattenInDialoog()
    probleemstelling.run()
