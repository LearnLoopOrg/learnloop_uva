import streamlit as st
import json
import base64
import concurrent.futures


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

    def display_chat_messages(self):
        """
        Display chat messages (text or image) in the Streamlit app.
        """
        for message in st.session_state.messages:
            with st.chat_message(
                message["role"],
                avatar="🔵" if message["role"] == "assistant" else "🔘",
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
                            "role": "assistant",
                            "content": response,
                            "image": image_path,
                        }
                    )
            else:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
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

    def handle_user_input(self):
        if user_input := st.chat_input("Jouw antwoord"):
            self.add_to_user_responses(user_input)

            # Display the user input in the chat
            with st.chat_message("user", avatar="🔘"):
                st.markdown(f"{user_input}")

            # Generate assistant response based on current topic
            with st.chat_message("assistant", avatar="🔵"):
                # Render image if available
                if image_path := self.get_next_question_with_image():
                    st.image(image_path)

                json_response, text_response = self.generate_responses()
                print(f"JSON response: {json_response}")
                print(f"Text response: {text_response}")

                if json_response:
                    image_path = None
                    self.update_question_data(json_response)
                    self.add_to_assistant_responses(text_response, image_path)
                    self.update_current_topic()
                else:
                    st.write("Geen JSON-reactie ontvangen van OpenAI.")

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
        # with concurrent.futures.ThreadPoolExecutor() as executor:
        # Schedule both tasks to run concurrently
        # future_text = st.write_stream(
        #     executor.submit(
        #         self.generate_text_response,
        #         topic,
        #         messages,
        #         openai_client,
        #         openai_model,
        #     )
        # )  # Pass arguments if required
        # future_json = executor.submit(
        #     self.generate_json_response,
        #     topic,
        #     messages,
        #     openai_client,
        #     openai_model,
        # )  # Pass arguments if required

        # # Now wait for both to complete and get results
        # text_response, image_path = future_text.result()
        # json_response = future_json.result()

        text_response = st.write_stream(
            self.generate_text_response(topic, messages, openai_client, openai_model)
        )
        json_response = self.generate_json_response(
            topic, messages, openai_client, openai_model
        )

        return json_response, text_response

    def render_sidebar(self):
        with st.sidebar:
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
                    # f'<h3 style="color:{color}; margin-bottom: 0.4em;">{topic} - {completion_percentage}%</h3>',
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

                st.write("\n")
                st.markdown(
                    "<hr style='border-top: 1px solid #bbb; width: 98%; margin: auto;'>",
                    unsafe_allow_html=True,
                )
                st.write("\n")

    def run(self):
        self.db_dal = st.session_state.db_dal
        self.db = st.session_state.db
        self.utils = st.session_state.utils
        self.openai_client = st.session_state.openai_client
        self.base_path = st.session_state.base_path

        self.initialize_session_states()

        # self.create_questions_json_from_content_and_topic_json()

        st.title("Samenvatten in dialoog")

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Zullen we beginnen? Wat weet je over {st.session_state.current_topic}?",
            }
        )

        self.display_chat_messages()

        self.handle_user_input()

        self.render_sidebar()


if __name__ == "__main__":
    open("student_knowledge.txt", "w").close()
    probleemstelling = SocraticDialogue()
    probleemstelling.run()
