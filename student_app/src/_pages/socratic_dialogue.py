import streamlit as st
import json
import base64


class SocraticDialogue:
    def __init__(self):
        pass

    def create_questions_json_from_content_and_topic_json(self):
        print("Creating questions JSON from content and topic JSON...")
        topics_data = self.db_dal.fetch_module_topics(st.session_state.selected_module)
        segments_data = self.db_dal.fetch_module_content(
            st.session_state.selected_module
        )

        final_data = {}
        # Loop door de topics en verzamel de bijbehorende segmenten
        for topic in topics_data["topics"]:
            topic_title = topic["topic_title"]
            segment_indexes = topic["segment_indexes"]

            # Maak een lijst voor vragen en verzamel alle theorie-segmenten en vragen voor dit topic
            topic_content = {
                "response": None,
                "student_knowledge": None,
                "questions": [],
            }

            # Voeg de relevante segmenten toe
            for index in segment_indexes:
                if index < len(segments_data["segments"]):
                    segment = segments_data["segments"][index]

                    # Voeg theorie-segment toe als response
                    if segment["type"] == "theory":
                        topic_content["response"] = segment["text"]
                        topic_content["student_knowledge"] = segment["title"]

                    # Voeg vragen toe
                    if segment["type"] == "question":
                        question_data = {
                            "question": segment.get("question"),
                            "status": None,  # Kan worden bijgewerkt indien nodig
                            "level": 1,  # Kan worden aangepast indien nodig
                            "score": None,  # Kan worden berekend of toegevoegd
                            "answer": segment.get("answer")
                            or segment.get("answers", {}).get("correct_answer"),
                        }
                        topic_content["questions"].append(question_data)

            # Voeg dit topic toe aan de uiteindelijke data
            final_data[topic_title] = topic_content

        output_file = f"{self.base_path}data/questions.json"
        # Schrijf het resultaat naar een nieuw JSON-bestand
        with open(output_file, "w") as f:
            json.dump(final_data, f, indent=4)

        print(f"Gecombineerde JSON is opgeslagen in {output_file}")

    def reset_session_states(self):
        st.session_state.messages = []
        st.session_state.message_ids = []

    def initialize_session_states(self):
        """
        Initialize session variables if they don't exist.
        """
        print("Initializing session states...")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "current_topic" not in st.session_state:
            st.session_state.current_topic = self.get_next_incomplete_topic()

        if "message_ids" not in st.session_state:
            st.session_state.message_ids = []

        if "prompt_number" not in st.session_state:
            st.session_state.prompt_number = 2

    def display_chat_messages(self):
        """
        Display chat messages (text or image) in the Streamlit app.
        """
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"],
                avatar="🔵" if message["role"] == "teacher" else "🔘",
            ):
                st.markdown(message["content"])
                if "image" in message:
                    st.image(open(message["image"], "rb").read())

    def add_to_assistant_responses(self, response, image_path):
        # Hash the response to avoid duplicates in the chat
        message_id = hash(response)
        if message_id not in st.session_state.message_ids:
            st.session_state.message_ids.append(message_id)

            if image_path is not None:
                image_id = hash(image_path)
                if image_id not in st.session_state.message_ids:
                    st.session_state.messages.append(
                        {
                            "role": "teacher",
                            "content": response,
                            "image": image_path,
                        }
                    )
            else:
                st.session_state.messages.append(
                    {
                        "role": "teacher",
                        "content": response,
                    }
                )

    def add_to_user_responses(self, user_input):
        st.session_state.messages.append({"role": "user", "content": user_input})

    def encode_image_to_base64(self, image_path):
        """Leest een afbeelding in en encodeert deze naar base64."""
        if image_path:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")

        return None

    def generate_text_response(self, topic, messages, openai_client, openai_model):
        example_output_diagnosed = {
            "student_knowledge": "De student weet dat insuline de bloedsuikerspiegel verlaagt door de opname van glucose in cellen te stimuleren.",
            "response": "Wat weet je al over insuline en de bloedsuikerspiegel?",
            "questions": [
                {
                    "question": "Welk effect heeft insuline op de bloedsuikerspiegel?",
                    "status": "not asked",
                    "level": 1,
                    "score": "2/3",
                    "answer": "Insuline verlaagt de bloedsuikerspiegel door de opname van glucose in cellen te stimuleren (2 punten).",
                    "student_answer": ["Insuline verlaagt de bloedsuikerspiegel."],
                },
                {
                    "question": "Wat is de rol van insuline in het lichaam?",
                    "status": "not asked",
                    "level": 2,
                    "score": "1/2",
                    "answer": "Insuline reguleert de bloedsuikerspiegel (1 punt) en zorgt voor de opslag van glucose in de lever (1 punt).",
                    "student_answer": [],
                },
                {
                    "question": "Hoe wordt insuline geproduceerd in het lichaam?",
                    "status": "done",
                    "level": 3,
                    "score": "1/1",
                    "answer": "Insuline wordt geproduceerd door de bètacellen in de alvleesklier (1 punt).",
                    "student_answer": [],
                },
            ],
            "status": "diagnosed",
        }

        example_output_undiagnosed = {
            "student_knowledge": "De student weet dat insuline de bloedsuikerspiegel verlaagt door de opname van glucose in cellen te stimuleren.",
            "questions": [
                {
                    "question": "Welk effect heeft insuline op de bloedsuikerspiegel?",
                    "status": "not asked",
                    "level": 1,
                    "score": "2/3",
                    "answer": "Insuline verlaagt de bloedsuikerspiegel door de opname van glucose in cellen te stimuleren (2 punten).",
                    "student_answer": [],
                },
                {
                    "question": "Wat is de rol van insuline in het lichaam?",
                    "status": "not asked",
                    "level": 2,
                    "score": "1/2",
                    "answer": "Insuline reguleert de bloedsuikerspiegel (1 punt) en zorgt voor de opslag van glucose in de lever (1 punt).",
                    "student_answer": [],
                },
                {
                    "question": "Hoe wordt insuline geproduceerd in het lichaam?",
                    "status": "done",
                    "level": 3,
                    "score": "1/1",
                    "answer": "Insuline wordt geproduceerd door de bètacellen in de alvleesklier (1 punt).",
                    "student_answer": [],
                },
            ],
            "status": "diagnosed",
        }

        # Prompts
        undiagnosed_prompt = f"""
    You are part of a conversational system that aims to guide students through topics and questions. Your goal is to assess the student's knowledge on a given topic. The content is organized into topics, each containing multiple questions with corresponding answer models. Your role is to guide the student through each topic by evaluating their understanding of the entire subject.

    At the start of a new topic: **{topic}**, ask the student what they already know about this specific topic, explicitly mentioning its name.

    ### Instructions:

    1. **Initial Question**: Begin by asking the student what they know about the current topic.
    2. **Evaluate Knowledge**: Based on the student's response, compare their knowledge to the answer models provided for each question in the topic. Identify which questions the student implicitly answered by determining how many points (marked as '(1 punt)' in the answer models) were addressed.
    3. **Update Scores**:
        - Adjust the score for each question based on how many points the student earned, e.g., '2/3' or '0/X' (where X is the total available points for the question).
        - If the student earns all points for a question, mark that question as 'done' and move on to the next unanswered question.
    4. **Diagnose Completion**:
        - If you received the students answer (on your question on what they know about the topic), change the general **status** field to 'diagnosed'.
        - Then, proceed to asking the first question in the questions list that the student didn't answer fully yet with it's answer. Prioritizing questions in order from lowest to highest difficulty.

    ### The response must be in clear, conversational text, guiding the student through the topic.

    **Example Output**:
    Wat weet je al over insuline en de bloedsuikerspiegel?

    **Example JSON response**:
    {example_output_undiagnosed}
    """

        diagnosed_prompt = f"""
    Your role in this system is to guide the student through each topic by asking questions, providing feedback, and assessing their progress based on unresolved questions. The content is organized into topics, each containing multiple questions and corresponding answer models. You are given the question data of only one topic.

    Your task is either to:

    1. Ask the student a new question.
    2. Provide feedback on the student's answer to a previously asked question and update their score for that question accordingly.

    You should proceed by focusing on specific unanswered questions, starting with the easiest and increasing in difficulty. Continue asking a question until the student provides a satisfactory response that earns full points (e.g., 2/2 points).

    Take the following steps step-by-step, take your time and don't skip any steps:
    After each student response:

    - **Evaluate the answer** by comparing it to the answer model.
    - **Determine how many points the student earned** based on how many of the points, given as '(1 punt)' in the answer model, were addressed in the student's answer.
    - **Update the score** for the question accordingly by adjusting the score field to reflect the student's progress (e.g., '2/3' or '0/X' where X is the total points available).
    - If the student has earned all points for a question, **mark it as 'done'** by setting the status to 'done' and moving on to the next unanswered question. The next question should be the one with the lowest difficulty that the student has not yet fully answered, which is indicated by the status 'not asked' or 'asked' or the score 'Y/X' where Y < X. Explicitly ask the student this question in your response to their previous answer.

    Always respond in clear, conversational text, providing feedback and guiding the student.

    Example response:
    Hoe beïnvloedt insuline de bloedsuikerspiegel tijdens maaltijden of fysieke inspanning?

    Example JSON response:
    {example_output_diagnosed}
    """

        # Determine which prompt to use
        questions = self.get_questions()
        status = questions[topic].get("status", "undiagnosed")
        if status == "diagnosed":
            instructions = diagnosed_prompt
        else:
            instructions = undiagnosed_prompt

        # Prepare messages
        messages = [
            {"role": "system", "content": instructions},
            *[{"role": m["role"], "content": m["content"]} for m in messages],
            *[
                {
                    "role": "user",
                    "content": f'<img src="data:image/png;base64,{self.encode_image_to_base64(m["image"])}">',
                }
                for m in messages
                if m.get("image")
            ],
        ]

        stream = openai_client.chat.completions.create(
            model=openai_model,
            messages=messages,
            stream=True,
        )

        return stream

    def generate_json_response(self, topic, messages, openai_client, openai_model):
        example_output_diagnosed = {
            "student_knowledge": "De student weet dat insuline de bloedsuikerspiegel verlaagt door de opname van glucose in cellen te stimuleren.",
            "response": "Wat weet je al over insuline en de bloedsuikerspiegel?",
            "questions": [
                {
                    "question": "Welk effect heeft insuline op de bloedsuikerspiegel?",
                    "status": "not asked",
                    "level": 1,
                    "score": "2/3",
                    "answer": "Insuline verlaagt de bloedsuikerspiegel door de opname van glucose in cellen te stimuleren (2 punten).",
                    "student_answer": ["Insuline verlaagt de bloedsuikerspiegel."],
                },
                {
                    "question": "Wat is de rol van insuline in het lichaam?",
                    "status": "not asked",
                    "level": 2,
                    "score": "1/2",
                    "answer": "Insuline reguleert de bloedsuikerspiegel (1 punt) en zorgt voor de opslag van glucose in de lever (1 punt).",
                    "student_answer": [],
                },
                {
                    "question": "Hoe wordt insuline geproduceerd in het lichaam?",
                    "status": "done",
                    "level": 3,
                    "score": "1/1",
                    "answer": "Insuline wordt geproduceerd door de bètacellen in de alvleesklier (1 punt).",
                    "student_answer": [],
                },
            ],
            "status": "diagnosed",
        }

        example_output_undiagnosed = {
            "student_knowledge": "De student weet dat insuline de bloedsuikerspiegel verlaagt door de opname van glucose in cellen te stimuleren.",
            "questions": [
                {
                    "question": "Welk effect heeft insuline op de bloedsuikerspiegel?",
                    "status": "not asked",
                    "level": 1,
                    "score": "2/3",
                    "answer": "Insuline verlaagt de bloedsuikerspiegel door de opname van glucose in cellen te stimuleren (2 punten).",
                    "student_answer": [],
                },
                {
                    "question": "Wat is de rol van insuline in het lichaam?",
                    "status": "not asked",
                    "level": 2,
                    "score": "1/2",
                    "answer": "Insuline reguleert de bloedsuikerspiegel (1 punt) en zorgt voor de opslag van glucose in de lever (1 punt).",
                    "student_answer": [],
                },
                {
                    "question": "Hoe wordt insuline geproduceerd in het lichaam?",
                    "status": "done",
                    "level": 3,
                    "score": "1/1",
                    "answer": "Insuline wordt geproduceerd door de bètacellen in de alvleesklier (1 punt).",
                    "student_answer": [],
                },
            ],
            "status": "diagnosed",
        }

        # Prompts
        undiagnosed_prompt = f"""
    You are part of a conversational system that aims to guide students through topics and questions. Your goal is to assess the student's knowledge on a given topic. The content is organized into topics, each containing multiple questions with corresponding answer models. Your role is to guide the student through each topic by evaluating their understanding of the entire subject. Your response must be in valid JSON format.

    At the start of a new topic: **{topic}**, ask the student what they already know about this specific topic, explicitly mentioning its name.

    ### Instructions:

    1. **Initial Question**: Begin by asking the student what they know about the current topic.
    2. **Evaluate Knowledge**: Based on the student's response, compare their knowledge to the answer models provided for each question in the topic. Identify which questions the student implicitly answered by determining how many points (marked as '(1 punt)' in the answer models) were addressed.
    3. **Update Scores**:
        - Adjust the score for each question based on how many points the student earned, e.g., '2/3' or '0/X' (where X is the total available points for the question).
        - If the student earns all points for a question, mark that question as 'done' and move on to the next unanswered question.
    4. **Diagnose Completion**:
        - If you received the students answer (on your question on what they know about the topic), change the general **status** field to 'diagnosed'.
        - Then, proceed to asking the first question in the questions list that the student didn't answer fully yet with it's answer. Prioritizing questions in order from lowest to highest difficulty.

    ### The JSON response must include the following fields:

    - **response**: Provide feedback to the student, explaining what they got right or wrong. Offer a follow-up question or comment to further guide their learning.
    - **student_knowledge**: Give a brief summary of what the student understood based on their answer.
    - **questions**: This contains the original question data but updated to reflect the student's progress. For each question, update the following fields:
        - **score**: Reflect how many points the student earned for each question they addressed, showing the result as a fraction (e.g., '2/3'). If no points were earned, display '0/X' (with X being the total points available for the question).
        - **status**: Mark questions as 'done' if fully answered, or leave them as 'not asked' or 'asked' as applicable.
        - **student_answer**: Add each answer of the student to this list for each question.
    - **status:** Update the status of the topic from 'undiagnosed' to 'diagnosed' once you've received the student's response.

    Response format is only JSON:
    ```json
    [Your JSON response]
    ```
    **Example Output:**
    ```json
    {example_output_undiagnosed}
    ```

    ### Current Topic Questions and Answer Models:

    {self.get_questions()[topic]}
    """

        diagnosed_prompt = f"""
        Your role in this system is to guide the student through each topic by asking questions, providing feedback, and assessing their progress based on unresolved questions. The content is organized into topics, each containing multiple questions and corresponding answer models. You are given the question data of only one topic.

        Your task is either to:

        1. Ask the student a new question.
        2. Provide feedback on the student's answer to a previously asked question and update their score for that question accordingly.

        You should proceed by focusing on specific unanswered questions, starting with the easiest and increasing in difficulty. Continue asking a question until the student provides a satisfactory response that earns full points (e.g., 2/2 points).

        Take the following steps step-by-step, take your time and don't skip any steps: After each student response:

        - **Evaluate the answer** by comparing it to the answer model.
        - **Determine how many points the student earned** based on how many of the points, given as '(1 punt)' in the answer model, were addressed in the student's answer.
        - **Update the score** for the question accordingly by adjusting the score field to reflect the student's progress (e.g., '2/3' or '0/X' where X is the total points available).
        - If the student has earned all points for a question, **mark it as 'done'** by setting the status to 'done' and moving on to the next unanswered question. The next question should be the one with the lowest difficulty that the student has not yet fully answered, which is indicated by the status 'not asked' or 'asked' or the score 'Y/X' where Y < X. Explicitly ask the student this question in your response to their previous answer.

        The JSON response must include the following fields:

        - **response**: This is your feedback to the student. It should include an explanation of their answer, mentioning what was correct or incorrect, and a follow-up question or comment to guide their learning.
        - **student_knowledge**: Provide a concise summary of what the student correctly understood, based on their answer.
        - **questions**: This is the question data provided in the input, but with updates to reflect the student's current progress. For each question, update the following fields:
            - **status**: Update to 'not asked', 'asked', or 'done', depending on the progress of each question. Only modify the status of the current question.
            - **score**: Update the score for the current question, indicating the points earned as a fraction (e.g., '2/3'). If no points were earned for the current question, display '0/X', where X is the total possible points for the question. Leave the scores for the other questions unchanged.

        Always provide your response in valid JSON format:

        ```json
        [Your JSON response]
        ```

        **Example JSON response:**

        ```json
        {example_output_diagnosed}
        ```

        **Question data:**

        {self.get_questions()[topic]}
        """

        # Determine which prompt to use
        questions = self.get_questions()
        status = questions[topic].get("status", "undiagnosed")
        if status == "diagnosed":
            instructions = diagnosed_prompt
        else:
            instructions = undiagnosed_prompt

        # Prepare messages
        messages = [
            {"role": "system", "content": instructions},
            *[{"role": m["role"], "content": m["content"]} for m in messages],
            *[
                {
                    "role": "user",
                    "content": f'<img src="data:image/png;base64,{self.encode_image_to_base64(m["image"])}">',
                }
                for m in messages
                if m.get("image")
            ],
        ]

        # OpenAI API call for JSON response
        response = openai_client.chat.completions.create(
            model=openai_model,
            messages=messages,
            response_format={"type": "json_object"},
        )

        json_response = json.loads(response.choices[0].message.content)

        if json_response:
            return json_response

    def get_next_incomplete_topic(self):
        for topic, questions in self.get_questions().items():
            print(f"Checking topic: {topic}")
            print(f"Questions: {questions}")

            if any(q["status"] != "done" for q in questions["questions"]):
                return topic

    def update_current_topic(self):
        print(f"Updating current topic: {st.session_state.current_topic}")
        question_data = self.get_questions()[st.session_state.current_topic][
            "questions"
        ]
        # Check if the current topic is fully complete
        if all(q["status"] == "done" for q in question_data):
            st.balloons()
            next_topic = self.get_next_incomplete_topic()
            if next_topic:
                st.session_state.current_topic = next_topic
            else:
                st.write("Alle onderwerpen zijn voltooid!")

    def get_next_question_with_image(self):
        file_path = f"{self.base_path}data/questions.json"
        # Openen en inlezen van de JSON-file
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Doorloop de content en zoek naar de vraag met een scorebreuk
        for topic, content in data.items():
            questions = content.get("questions", [])
            for question in questions:
                score = question.get("score", "")
                if score is None:
                    continue
                # Check of de score een breuk is (dus niet gelijk zoals 1/1, 2/2 etc.)
                if "/" in score:
                    score_parts = score.split("/")
                    if score_parts[0] != score_parts[1]:  # Score breuk nog niet gelijk
                        image = question.get("image")
                        if image:  # Check of er een afbeelding aanwezig is
                            return image  # Retourneer het pad van de afbeelding
        return None  # Geen afbeelding gevonden

    # def handle_user_input(self):
    #     if user_input := st.chat_input("Jouw antwoord"):
    #         self.add_to_user_responses(user_input)

    #         # Display the user input in the chat
    #         with st.chat_message("user", avatar="🔘"):
    #             st.markdown(f"{user_input}")

    #         # Generate assistant response based on current topic
    #         with st.chat_message("assistant", avatar="🔵"):
    #             # Render image if available
    #             if image_path := self.get_next_question_with_image():
    #                 st.image(image_path)

    #             json_response, text_response = self.generate_responses()

    #             if json_response:
    #                 image_path = None
    #                 self.update_question_data(json_response)
    #                 self.add_to_assistant_responses(text_response, image_path)
    #                 self.update_current_topic()
    #             else:
    #                 st.write("Geen JSON-reactie ontvangen van OpenAI.")

    def update_question_data(self, json_response):
        question_data = self.get_questions()
        question_data[st.session_state.current_topic] = json_response
        with open(f"{self.base_path}data/questions.json", "w") as file:
            json.dump(question_data, file, indent=4)

    def get_questions(self):
        with open(f"{self.base_path}data/questions.json", "r") as file:
            return json.load(file)

    def calculate_topic_completion(self, topic):
        """
        Calculate the completion percentage of a topic based on the number of 'done' questions.
        """
        print(f"Calculating completion for topic: {topic}")
        questions = self.get_questions()[topic]["questions"]
        total_questions = len(questions)
        done_questions = sum(1 for q in questions if q["status"] == "done")

        if total_questions == 0:
            return 0  # Avoid division by zero if there are no questions

        completion_percentage = (done_questions / total_questions) * 100
        return int(completion_percentage)

    def generate_responses(self):
        topic = st.session_state.current_topic
        messages = st.session_state.messages
        openai_client = st.session_state.openai_client
        openai_model = st.session_state.openai_model

        text_response = st.write_stream(
            self.generate_text_response(topic, messages, openai_client, openai_model)
        )
        json_response = self.generate_json_response(
            topic, messages, openai_client, openai_model
        )

        return json_response, text_response

    def render_sidebar(self):
        with st.sidebar:
            st.subheader("Settings")
            st.radio("Selecteer een prompt", [1, 2, 3, 4], key="prompt_number")
            st.button("Reset chat", on_click=self.reset_session_states)
            st.text_area("Extra instructies", key="extra_instructions_from_user")
            st.title(st.session_state.selected_module)
            st.write("\n")
            for topic, questions in self.get_questions().items():
                # Bereken het percentage voltooide vragen
                completion_percentage = self.calculate_topic_completion(topic)

                # Bepaal de kleur op basis van het percentage voltooide vragen
                if completion_percentage == 0:
                    color = "grey"
                elif completion_percentage <= 25:
                    color = "red"
                elif 25 < completion_percentage <= 70:
                    color = "orange"
                elif 70 < completion_percentage < 100:
                    color = "orange"
                elif completion_percentage == 100:
                    color = "green"

                # Toon het onderwerp (groter) en het percentage in de gekozen kleur
                st.markdown(
                    f'<h3 style="color:{color}; margin-bottom: 0 em;">{topic}</h3>',
                    unsafe_allow_html=True,
                )

                # Toon de vragen onder elk topic met een kleinere lettergrootte
                for question in questions["questions"]:
                    score = question.get("score", None)

                    # Function that turns 1/2 into percentage
                    if score is None:
                        # Display grey color if no score is available
                        status_icon = "⚪"
                        question_color = "grey"
                    else:
                        score = int(score.split("/")[0]) / int(score.split("/")[1])
                        if score < 0.25:
                            status_icon = "🔴"
                            question_color = "black"
                        elif score >= 0.25 and score < 0.75:
                            status_icon = "🟠"
                            question_color = "black"
                        elif score >= 0.75 and score < 1:
                            status_icon = "🟡"
                            question_color = "black"
                        elif score >= 1:
                            status_icon = "🟢"
                            question_color = "black"

                    # Pas de vraagopmaak aan met een kleinere tekstgrootte en grijze kleur bij None
                    st.markdown(
                        f'<p style="font-size:14px; color:{question_color}; margin-left: 0.2em;">{status_icon} {question["question"]}</p>',
                        unsafe_allow_html=True,
                    )

    def read_data_file(self, file_name):
        with open(f"{self.base_path}data/{file_name}", "r", encoding="utf-8") as file:
            return file.read()

    def write_data_file(self, file_name, data):
        with open(f"{self.base_path}data/{file_name}", "w", encoding="utf-8") as file:
            file.write(data)

    def evaluate_student_response(self):
        print("Evaluating student response...")
        conversation = st.session_state.messages
        knowledge_tree = self.read_data_file("knowledge_tree.txt")

        prompt = f"""
Gegevven is een socratisch dialoog met een student waarin de student antwoord geeft op vragen van de docent. Jouw doel is om de docent te helpen door de antwoorden van de student op de vragen te evalueren aan de hand van het antwoordmodel in de gegeven kennisboom. Daarbij moet je onderstaande stappen volgen en een geupdate versie van de kennis boom teruggeven.

Volg de volgende stappen zorgvuldig, neem je tijd en sla geen enkele stap over:
- **Evalueer het antwoord** door het te vergelijken met het antwoordmodel in de kennisboom.
- **Bepaal hoeveel punten de student heeft verdiend** op basis van hoeveel van de punten, aangegeven als '(1 punt)' in het voorbeeldantwoord, in het antwoord van de student zijn verwerkt. De student hoeft nooit letterlijk de woorden in het antwoordmodel te benoemen om de punten te verdienen. Het is jouw taak om te interpreteren wat de student bedoelt en te bepalen of die verwoording vergelijkbaar genoeg is om de punten te verdienen.
- **Werk de score voor de vraag in de kennisboom bij** door het scoreveld aan te passen om de voortgang van de student weer te geven (bijv. van '1/3' naar '2/3' als de student één van de drie punten erbij verdiend heeft.).
- Als de student alle punten voor een vraag heeft verdiend, **markeer deze als 'voltooid'** door het status veld in de kennisboom in te stellen op 'done' en ga verder naar de volgende onbeantwoorde vraag. Als de student niet alle punten behaald heeft voor een vraag (bijv. 0/1, 2/3, 1/2 etc.), maar de vraag wel gesteld is door de docent, moet je 'asked' invullen bij de status. Vragen die nog niet gesteld zijn moet je op 'not asked' laten staan.
- Geef de volledige kennisboom terug met de bijgewerkte scores en statussen.

### Kennisboom:
{knowledge_tree}

### Gesprekgeschiedenis met student:
{conversation}

### Bijgewerkte kennisboom:
"""
        response = self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": prompt},
            ],
            response_format={"type": "text"},
        )
        output = response.choices[0].message.content
        print(output)

        self.write_data_file("knowledge_tree.txt", output)

    def generate_teacher_response(self):
        conversation = st.session_state.messages
        if conversation == []:
            conversation = [
                "[no conversation yet, start the conversation, but don't include this message in your response]"
            ]  # Do not append to messages

        knowledge_tree = self.read_data_file("knowledge_tree.txt")

        example_conversation = self.read_data_file("example_conversation.txt")

        prompt_1 = f"""
You are a teacher guiding a student through a structured knowledge tree that covers various levels of abstraction. Your goal is to identify the student's current knowledge and guide them Socratically, encouraging them to fill in any knowledge gaps on their own. You help the student work through the entire knowledge tree with full understanding.

**Your instructions:**

1. **Start at the highest level of abstraction:**
   - Begin by asking the student what they know about the main topic.
   - *Example:* "Can you tell me everything you know about **Philosophy of Mind**?"

2. **Assume the student has knowledge unless proven otherwise:**
   - Assume the student is familiar with the topic and encourage them to share what they know.
   - *Example:* "What are some key concepts or topics within **Philosophy of Mind**?"

3. **Introduce underlying topics and discuss one at a time:**
   - First, list the subtopics, then dive into one specific subtopic in the same conversation.
   - *Example:* "Under **Philosophy of Mind**, there are topics like **Arguments for Substance Dualism**, **Arguments against Substance Dualism**, and **Strengths and Weaknesses of Substance Dualism**. Let's start with **Arguments for Substance Dualism**. What do you know about that?"

4. **Let the student respond before explaining:**
   - Ask if the student is familiar with a concept before providing an explanation.
   - *Example:* "Do you know what **Substance Dualism** means, or should we explore it together?"

5. **Encourage breaking down complex ideas:**
   - Suggest dividing complex topics into smaller parts to make them easier to understand.
   - *Example:* "Shall we break down **Leibniz's Law** to understand it better?"

6. **Follow the structure of the knowledge tree:**
   - Stick to the topics and questions listed in the knowledge tree.
   - *Note:* Avoid introducing topics not included in the knowledge tree.

7. **Focus on one concept at a time:**
   - Concentrate on one idea and ensure the student understands it before moving on.
   - *Example:* "Let's first discuss **Materialism**. Can you explain what this means?"

8. **Have the student explain in their own words:**
   - Ask the student to restate the concept in their own words to check for understanding.
   - *Example:* "Can you now explain what **Materialism** means in your own words?"

9. **Confirm understanding before moving on:**
   - Ensure the student fully grasps the current topic before proceeding.
   - *Example:* "Great! Since you understand **Materialism**, we can now look at **Reductionism**."

10. **Guide the student logically through topics:**
    - Present topics in a logical order so the student understands why each one is important.
    - *Example:* "Now that we've discussed arguments for Substance Dualism, it makes sense to look at counterarguments. What do you know about **Materialism**?"

11. **Avoid giving unsolicited information:**
    - Do not provide explanations or details until you've verified that the student needs them.
    - *Note:* Avoid explaining multiple terms at once without first asking the student.

12. **Correct gently and encourage:**
    - If the student misunderstands or makes a mistake, offer corrections in a supportive manner.
    - *Example:* "Almost right! **Reductionism** isn't about minimalism, but about breaking down complex phenomena into simpler parts. Shall we explore this further together?"

13. **Ask for repetition and confirmation after explaining:**
    - After explaining, ask the student to summarize the concept to ensure they've understood.
    - *Example:* "Now that we've discussed what **Leibniz's Law** is, can you summarize it in your own words?"

14. **Be patient and supportive:**
    - Acknowledge the student's challenges and continue to offer encouragement.
    - *Example:* "Don't worry if you're unsure right now. We can take it step by step."

**Knowledge tree:**
{knowledge_tree}

**Conversation with student:**
{conversation}
"""
        prompt_2 = f"""
Je bent een docent die de kennis van een student socratisch identificeert en aanvult. Begin door de student te vragen alles te vertellen wat hij weet over een onderwerp (blurting). Op basis hiervan bepaal je welke onderdelen van een kennisstructuur de student niet heeft genoemd. Stel gerichte vragen over deze ontbrekende elementen. Wanneer de student iets niet weet, splits je het op in eenvoudigere concepten of voorkennis, en werk je van boven naar beneden door de kennisboom. Behandel elk abstractieniveau stap voor stap en zorg dat de student actief zijn begrip demonstreert voordat je verdergaat.

---

**Voorbeelden:**

1. Begin met een brede vraag op het hoogste abstractieniveau:
   - **Goed:** "Welke belangrijke onderwerpen vallen onder 'Philosophy of Mind'?"
   - **Fout:** "Wat weet je over 'Argumenten voor substantiedualisme'?"

2. Vraag naar kennis vóórdat je uitleg geeft:
   - **Goed:** "Weet je welke argumenten substantiedualisme ondersteunen?"
   - **Fout:** "De belangrijkste argumenten zijn Leibniz's Law en Descartes' Cogito."

3. Laat de student uitleggen en controleer begrip:
   - **Goed:** "Kun je nu in je eigen woorden uitleggen wat Leibniz's Law betekent?"
   - **Fout:** "Oké, laten we doorgaan."

4. Werk gestructureerd de kennisboom af en herhaal niet wat al goed is beantwoord:
   - **Goed:** "Prima! Laten we nu de tegenargumenten tegen substantiedualisme bespreken."
   - **Fout:** "Kun je nogmaals uitleggen wat substantiedualisme is?"

5. Vraag naar verschillen om de kennis te testen:
   - **Goed:** "Kun je het verschil uitleggen tussen materialisme en reductionisme?"
   - **Fout:** "Wat betekenen materialisme en reductionisme?"

6. Geef geen hints weg en geef ook niet te veel weg door al een deel van het juiste antwoord te geven in je vraagstelling.
7. Als een student een antwoord volledig goed beantwoord heeft, dan moet je naast je normale reactie met een groen vinkje (✅) aangeven dat het antwoord goed is.

8. Evalueer het antwoord en geef een score:
Je moet verdergaan door je te richten op specifieke onbeantwoorde vragen, beginnend met de makkelijkste en oplopend in moeilijkheidsgraad. Blijf een vraag stellen totdat de student een bevredigend antwoord geeft dat de volledige punten oplevert (bijv. 2/2 of 3/3 punten).

Volg de volgende stappen zorgvuldig, neem je tijd en sla geen enkele stap over. Na elk antwoord van de student:

- **Evalueer het antwoord** door het te vergelijken met het voorbeeldantwoord.
- **Bepaal hoeveel punten de student heeft verdiend** op basis van hoeveel van de punten, aangegeven als '(1 punt)' in het voorbeeldantwoord, in het antwoord van de student zijn verwerkt.
- **Werk de score bij** voor de vraag door het scoreveld aan te passen om de voortgang van de student weer te geven (bijv. '2/3' of '0/X' waarbij X het totaal aantal beschikbare punten is).
- Als de student alle punten voor een vraag heeft verdiend, **markeer deze als 'voltooid'** door de status in te stellen op 'done' en ga verder naar de volgende onbeantwoorde vraag. De volgende vraag moet de minst moeilijke vraag zijn die de student nog niet volledig heeft beantwoord, wat wordt aangegeven door de status 'not asked' of 'asked' of de score 'Y/X' waarbij Y < X. Stel de student expliciet deze vraag in je reactie op hun vorige antwoord.

9. Antwoord in het nederlands.

## Volg dezelfde structuur en vorm als in dit voorbeeldgesprek:
{example_conversation}

## Kennisboom waar je de student doorheen moet lopen:
{knowledge_tree}

## Huidige gesprek met student:
{conversation}
"""

        prompt_3 = f"""
Je bent een docent die de kennis van een student socratisch identificeert en door een kennisboom heen loopt waarbij je door de abstractieniveau's heen loopt. Begin door de student te vragen alles te vertellen wat hij weet over een onderwerp (blurting). Op basis hiervan bepaal je in eerste instantie welke onderdelen van de gegeven kennisboom de student wel en niet kent. Werk de kennisboom af door de vragen per onderwerp te stellen, de antwoorden van de student te evalueren en de kennisboom te updaten met scores en de status. Stel gerichte vragen over deze ontbrekende elementen. Wanneer de student iets niet weet, splits je het op in eenvoudigere concepten of voorkennis, en werk je van boven naar beneden door de kennisboom. Behandel elk abstractieniveau stap voor stap en zorg dat de student alle punten in het antwoord van elke vraag voor het huidige abstractieniveau en onderwerp heeft behaald voordat je verdergaat. Je krijgt een aantal richtlijnen waar je je aan moet houden, gevolgd door een voorbeeld van een verkeerde reactie. Daarnaast krijg je een voorbeeld van een goed gesprek met een student en het huidige gesprek moet je op een vergelijkbare manier houden. Daarnaast krijg je de kennisboom waarin al een score is toegekend aan het antwoord van de student op basis van het antwoordmodel. Die kennisboom moet je langzaam afwerken en alleen vragen stellen die nog niet volledig beantwoord zijn. En als laatste krijg je het huidige gesprek met de student.

## Richtlijnen:
- Als de student een antwoord volledig goed beantwoord heeft, dan moet je naast je normale reactie met een groen vinkje (✅) aangeven dat het antwoord goed is.
- Als de student 1/2, 2/3, 3/4 of 3/5 van de punten verdiend heeft, dan moet je de student aanvullen met wat er mist en door gaan naar de volgende vraag.
- Als een student meermaals onvolledig antwoord heeft gegeven, moet je als alle relevante informatie gegeven is, de student vragen om het nogmaals in eigen woorden uit te leggen.

## Voorbeeld van verkeerde reactie:
Teacher: Laten we beginnen met een brede vraag op het hoogste abstractieniveau. Kun je me alles vertellen wat je weet over neuropsychologie?
Student: Iets met cognitie en hersnefuncties
Teacher: Dat is een goed begin! Kun je wat dieper ingaan op de relatie tussen gedrag, cognitie en hersenfuncties binnen de neuropsychologie? Wat onderzoekt deze discipline precies?
Wat is hier fout? De docent geeft al een deel van het antwoord weg, namelijk 'de relatie tussen gedrag, cognitie en hersenfuncties' terwijl de student alleen cognities en hersenfuncties heeft genoemd.

## Volg dezelfde structuur en vorm als in dit voorbeeldgesprek:
{example_conversation}

## Kennisboom waar je de student doorheen moet lopen:
{knowledge_tree}

## Huidige gesprek met student:
{conversation}

## Jouw reactie:
"""

        prompt_4 = f"""
Je bent een docent die studenten begeleidt door een kennisboom met verschillende abstractieniveaus. Jouw doel is om de kennis van de student te identificeren en hem op een socratische manier te begeleiden, zodat hij zelf de kennisgaten invult. Je helpt de student om de kennisboom volledig en begripvol door te lopen. Daarbij dien je de volgende richtlijnen te volgen:

1. **Begin op het hoogste abstractieniveau**: Vraag de student wat hij weet over het hoofdonderwerp en welke onderliggende onderwerpen of concepten eronder vallen.
2. **Pas "blurting" toe**: Moedig de student aan om alles te vertellen wat hij weet over het onderwerp voordat je specifieke vragen stelt.
3. **Ga uit van de kennis van de student**: Veronderstel dat de student veel weet, tenzij uit zijn antwoorden blijkt dat er kennisgaten zijn.
4. **Identificeer kennisgaten**: Als de student bepaalde onderliggende concepten niet noemt, stel dan gerichte vragen over die specifieke onderwerpen.
5. **Werk stap voor stap door de kennisboom**: Behandel elk abstractieniveau afzonderlijk en ga pas naar een lager niveau als het hogere niveau is begrepen.
6. **Geef geen informatie zonder te vragen**: Voorzie de student niet van uitleg of antwoorden voordat je hebt gevraagd of hij het al weet.
7. **Introduceer één concept tegelijk**: Leg niet meerdere termen of concepten tegelijk uit. Behandel ze afzonderlijk.
8. **Vraag naar voorkennis**: Als je een nieuw concept introduceert, vraag dan eerst of de student weet wat het betekent voordat je het uitlegt.
9. **Laat de student in eigen woorden uitleggen**: Vraag de student om concepten in zijn eigen woorden te definiëren om begrip te bevorderen.
10. **Vermijd voorzeggen**: Geef de antwoorden niet direct weg. Stimuleer de student om zelf na te denken en het antwoord te vinden.
11. **Herhaal na uitleg**: Als je iets hebt uitgelegd, vraag de student dan om het nogmaals in zijn eigen woorden uit te leggen om te controleren of het is begrepen.
12. **Wees vriendelijk en ondersteunend**: Gebruik uitnodigende taal zoals "Wil je dat ik het uitleg?" of "Zullen we het samen opbreken?".
13. **Vraag door bij misvattingen**: Als de student iets verkeerd begrijpt, vraag dan waarom hij dat denkt om de oorzaak van de verwarring te achterhalen.
14. **Test begrip door vergelijking**: Vraag de student om verschillen of overeenkomsten tussen twee concepten uit te leggen, indien passend.
15. **Wees zorgvuldig met correcties**: Als de student een onvolledig of incorrect antwoord geeft, help hem dan door gerichte vragen te stellen die hem naar het juiste antwoord leiden.
16. **Beperk je tot de kennisboom**: Focus op de onderwerpen en vragen die in de kennisboom staan. Introduceer geen externe informatie die niet relevant is.
17. **Controleer begrip voordat je verder gaat**: Zorg ervoor dat de student het huidige onderwerp volledig begrijpt voordat je naar het volgende gaat.
18. **Pas de volgorde aan op basis van begrip**: Als de student een concept al beheerst, hoef je dit niet opnieuw te behandelen en kun je verdergaan met het volgende relevante onderwerp.
19. **Werk van algemeen naar specifiek**: Begin met brede vragen en ga geleidelijk over naar specifiekere vragen naarmate het gesprek vordert.

Door deze richtlijnen te volgen, help je de student op een gestructureerde en effectieve manier door de kennisboom te navigeren, terwijl je zijn zelfstandige denkvermogen en begrip bevordert.

**Kennisboom:**
{knowledge_tree}

**Gesprek met de student:**
{conversation}
"""
        prompts = [prompt_1, prompt_2, prompt_3, prompt_4]
        prompt = prompts[st.session_state.prompt_number - 1]
        stream = self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": prompt},
                {
                    "role": "system",
                    "content": f"Extra instructions: {st.session_state.extra_instructions_from_user}",
                },
            ],
            stream=True,
        )

        return stream

    def handle_user_input(self):
        # First message
        if st.session_state.messages == []:
            with st.chat_message("teacher", avatar="🔵"):
                response = st.write_stream(self.generate_teacher_response())

        if user_input := st.chat_input("Jouw antwoord"):
            self.add_to_user_responses(user_input)

            with st.chat_message("user", avatar="🔘"):
                st.markdown(f"{user_input}")

            with st.chat_message("teacher", avatar="🔵"):
                st.write("Evaluating student response...")
                self.evaluate_student_response()
                response = st.write_stream(self.generate_teacher_response())

        try:
            self.add_to_assistant_responses(response, None)
        except:
            return

    def run(self):
        self.db_dal = st.session_state.db_dal
        self.db = st.session_state.db
        self.utils = st.session_state.utils
        self.openai_client = st.session_state.openai_client
        self.base_path = st.session_state.base_path
        self.openai_model = st.session_state.openai_model

        self.initialize_session_states()

        self.render_sidebar()

        # self.create_questions_json_from_content_and_topic_json()

        st.title("Socratic Dialogue")

        self.display_chat_messages()

        self.handle_user_input()


if __name__ == "__main__":
    open("student_knowledge.txt", "w").close()
    probleemstelling = SocraticDialogue()
    probleemstelling.run()
