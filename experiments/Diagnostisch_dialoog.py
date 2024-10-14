import streamlit as st
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
import json

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

        if "knowledge_levels" not in st.session_state:
            st.session_state.knowledge_levels = {
                "Introduction to Parkinson's": 3,
                "Symptoms": 3,
                "Diagnosis": 2,
                "Treatment": 1,
            }

    def display_chat_messages(self):
        """
        Display chat messages (text or image) in the Streamlit app.
        """
        for message in st.session_state.messages:
            if message["type"] == "text":
                # Display text message
                with st.chat_message(
                    message["role"],
                    avatar="🔵" if message["role"] == "assistant" else "🔘",
                ):
                    st.markdown(message["content"])
            elif message["type"] == "image":
                # Display image
                with st.chat_message(
                    message["role"],
                    avatar="🔵" if message["role"] == "assistant" else "🔘",
                ):
                    st.image(message["content"])

    def add_to_assistant_responses(self, response):
        st.session_state.messages.append(
            {"role": "assistant", "content": response, "type": "text"}
        )

    def add_image_to_assistant_responses(self, image_path):
        st.session_state.messages.append(
            {"role": "assistant", "content": image_path, "type": "image"}
        )

    def add_to_user_responses(self, user_input):
        st.session_state.messages.append(
            {"role": "user", "content": user_input, "type": "text"}
        )

    def generate_assistant_response(self):
        """
        Generate a response from the assistant.
        """
        role_prompt_old = f"""
Je gaat een socratische dialoog voeren met een student die een onderwerp probeert samen te vatten. De samenvatting die je moet begeleiden is opgedeeld in verschillende onderwerpen en subonderwerpen. Elk belangrijk element is voorzien van punten, die aangeven wat de student moet noemen om de volledige samenvatting goed te hebben. Je doel is om de student te helpen alle punten te benoemen, zonder deze direct voor te zeggen.

**Hoe gebruik je de samenvatting tijdens het gesprek?**

1. **Start met een algemene vraag:** Begin elk onderwerp door een brede vraag te stellen over dat onderwerp. Bijvoorbeeld: "Wat weet je over de zuur-base reactie?" Hierdoor stimuleer je de student om zijn huidige kennis uit te leggen.

2. **Vergelijk de antwoorden:** Vergelijk het antwoord van de student met de punten in de samenvatting. Als de student één of meerdere punten correct benoemt, noteer je deze als 'behandeld'.

3. **Identificeer ontbrekende elementen:** Zodra je merkt dat bepaalde punten nog niet genoemd zijn, stel je vragen die de student naar deze ontbrekende elementen leiden. Begin met abstracte vragen en maak ze steeds concreter als de student de antwoorden niet meteen weet.
   - **Voorbeeld abstracte vraag:** "Hoe denk je dat een zuur reageert met een base in een reactie?"  
   - **Voorbeeld concretere vraag:** "Wat gebeurt er met de protonen tijdens de zuur-base reactie?"

4. **Herhaal het proces:** Zodra alle punten voor een onderwerp besproken zijn, vraag dan of de student het onderwerp zou willen samenvatten in zijn eigen woorden. Daarna ga je door naar het volgende onderwerp in de samenvatting. Stel weer een brede vraag om te beginnen en werk op dezelfde manier totdat de student alle onderwerpen en punten heeft besproken.

5. **Check je werk:** Vraag regelmatig aan de student of hij of zij denkt dat alle belangrijke punten besproken zijn. Indien nodig, geef een korte samenvatting van wat al behandeld is en vraag of er nog iets ontbreekt.

6. **Sluit af:** Vraag de student aan het eind om een korte samenvatting te geven van alles wat besproken is. Bevestig dat de student nu alle punten van de samenvatting heeft geraakt.

**Belangrijk:** Na elk antwoord van de student, structureer je jouw reactie in JSON format als volgt:

- **student_knowledge:** [Hier noteer je de correcte kennis die de student heeft gegeven, in volledige zinnen als een string.] Als er geen relevante kennis is, antwoord dan met lege string.
- **response:** [Hier schrijf je jouw reactie terug naar de student om het gesprek voort te zetten als een string.]

**Geef geen extra tekst buiten deze twee velden.**

### Samenvatting:
{open("samenvatting.txt").read()}

### Gesprek met student:

"""
        role_prompt = f"""
You will conduct a Socratic dialogue with a student who is trying to summarize a topic. Each topic has multiple levels of questions, with higher-level questions being more advanced. Your task is to:

1. Ask the student an initial, broad question about the topic (e.g., "What do you know about Parkinson's?").
2. Evaluate the student's response to determine which questions can be skipped based on their existing knowledge.
3. For each question, track its status (either "not asked", "asked", or "done").
4. If the student's response covers more advanced material, skip lower-level questions and mark them as "done".
5. After each correct answer, increment the student's knowledge level for the current topic.
6. Move to the next topic once all questions for the current topic are marked as "done".
7. Provide your responses and updates in JSON format with the following structure:
   - **student_knowledge:** [A string summarizing the student's correct knowledge based on their response.]
   - **response:** [The next question or follow-up response as a string.]
   - **question_status:** [A list of questions for the current topic, each with a status of either "not asked", "asked", or "done".]

The list of questions for the current topic is as follows:
{json.dumps(self.get_questions(topic), indent=2)}

Conversation with the student:
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
            response_format={"type": "json_object"},
        )

        return stream

    def select_segments(self, student_knowledge_file, summary_file):
        prompt = f"""
        Gegeven is een tekstbestand met de kennis van de student en een samenvatting van het college. Jouw taak is om alleen de elementen uit de summary terug te geven die de student nog niet correct heeft genoemd. Deze segmenten moet je teruggeven in de volgorde waarin ze in de samenvatting voorkomen.
        
        ### Kennis van de student:
        {open(student_knowledge_file).read()}

        ### Samenvatting:
        {open(summary_file).read()}

        """
        response = self.client.chat.completions.create(
            model=st.session_state.openai_model,
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "text"},
        )

        return response.choices[0].message.content

    def get_next_incomplete_topic(self):
        """
        Get the next topic that still has unanswered questions.
        """
        for topic, questions in self.get_all_topics_with_questions().items():
            if any(q["status"] != "done" for q in questions):
                return topic
        return None  # All topics are complete

    def handle_user_input(self):
        if user_input := st.chat_input("Jouw antwoord"):
            self.add_to_user_responses(user_input)

            # Display the user input in the chat
            with st.chat_message("user", avatar="🔘"):
                st.markdown(f"{user_input}")

            if user_input.strip().upper() == "STOP":
                # selected_segments = self.select_segments(
                #     "student_knowledge.txt", "samenvatting.txt"
                # )
                selected_segments = "TEST"

                self.add_to_assistant_responses(
                    f"### Samenvatting:\n\n{selected_segments}"
                )
                # Voeg een afbeelding toe aan de chatgeschiedenis (bijvoorbeeld een relevant diagram)
                image_path = "test_image.jpg"  # Vervang dit door je eigen afbeelding
                self.add_image_to_assistant_responses(image_path)
                st.rerun()

            else:
                with st.chat_message("assistant", avatar="🔵"):
                    # Get the response from the assistant using streaming
                    response = st.write_stream(self.generate_assistant_response())
                    response = response["choices"][0]["message"]["content"]
                    json_response = json.loads(response)

                    # Save the student's correct knowledge to file or state
                    open("student_knowledge.txt", "a").write(
                        json_response["student_knowledge"]
                    )

                    # Get the score and update knowledge level
                    if "score" in json_response:
                        score = json_response["score"]
                        self.update_knowledge_level(
                            st.session_state.current_topic, score
                        )

                    # Update the question status based on the response
                    if "question_status" in json_response:
                        for question in json_response["question_status"]:
                            if question["status"] == "done":
                                self.update_question_status(
                                    st.session_state.current_topic,
                                    question["question"],
                                    "done",
                                )

                    # Check if the current topic is complete (all questions are "done")
                    if all(
                        q["status"] == "done" for q in json_response["question_status"]
                    ):
                        next_topic = self.get_next_incomplete_topic()
                        if next_topic:
                            st.session_state.current_topic = next_topic
                            self.add_to_assistant_responses(f"Next topic: {next_topic}")

                            # Ask the first question of the next topic
                            first_question = self.get_question(
                                next_topic,
                                st.session_state.knowledge_levels[next_topic],
                            )
                            self.add_to_assistant_responses(first_question)
                        else:
                            self.add_to_assistant_responses("All topics complete!")
                    else:
                        # Ask the next question in the current topic
                        next_question = self.get_question(
                            st.session_state.current_topic,
                            st.session_state.knowledge_levels[
                                st.session_state.current_topic
                            ],
                        )
                        self.add_to_assistant_responses(next_question)

                    # Add the assistant's response to the conversation
                    self.add_to_assistant_responses(json_response["response"])

    def update_knowledge_level(topic, score):
        current_score = st.session_state.knowledge_levels[topic]
        if score > current_score:
            st.session_state.knowledge_levels[topic] = score

    def get_questions(self, topic):
        questions = {
            "Introduction to Parkinson's": [
                {"question": "What is Parkinson's?", "status": None, "level": 1},
                {
                    "question": "Can you explain how Parkinson's develops?",
                    "status": None,
                    "level": 2,
                },
                {
                    "question": "What is dopamine's role in Parkinson's disease?",
                    "status": None,
                    "level": 3,
                },
            ],
            "Symptoms": [
                {
                    "question": "What are the main symptoms of Parkinson's?",
                    "status": None,
                    "level": 1,
                },
                {
                    "question": "How do the symptoms of Parkinson's disease progress?",
                    "status": None,
                    "level": 2,
                },
                {
                    "question": "What are the non-motor symptoms of Parkinson's?",
                    "status": None,
                    "level": 3,
                },
            ],
            "Diagnosis": [
                {
                    "question": "How is Parkinson's disease diagnosed?",
                    "status": None,
                    "level": 1,
                },
                {
                    "question": "What are the diagnostic criteria for Parkinson's?",
                    "status": None,
                    "level": 2,
                },
                {
                    "question": "What tests are used to diagnose Parkinson's?",
                    "status": None,
                    "level": 3,
                },
            ],
            "Treatment": [
                {
                    "question": "What are the treatment options for Parkinson's?",
                    "status": None,
                    "level": 1,
                },
                {
                    "question": "How does medication help manage Parkinson's symptoms?",
                    "status": None,
                    "level": 2,
                },
                {
                    "question": "What are the surgical treatments for Parkinson's?",
                    "status": None,
                    "level": 3,
                },
            ],
        }
        # return next(
        #     (q["question"] for q in questions[topic] if q["level"] == level), None
        # )
        return questions.get(topic, [])

    def run(self):
        self.initialize_session_state()

        st.title("Samenvatten in dialoog")

        if st.session_state.messages == []:
            intro_text = "We gaan samen de belangrijkste punten van het college samenvatten. Zullen we beginnen?"
            self.add_to_assistant_responses(intro_text)

        self.display_chat_messages()
        self.handle_user_input()

        with st.sidebar:
            colors = {1: "red", 2: "orange", 3: "green"}
            for topic, score in st.session_state.knowledge_levels.items():
                color = colors[score]
                st.markdown(
                    f'<span style="color:{color}">{topic}</span>',
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    open("student_knowledge.txt", "w").close()
    probleemstelling = SamenvattenInDialoog()
    probleemstelling.run()
