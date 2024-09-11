import streamlit as st
import pandas as pd

# Initialize session state to store the list of activities
if "activities" not in st.session_state:
    st.session_state.activities = [
        {
            "week": "Week 1",
            "activities": [
                {
                    "text": "Voorbereiding HC",
                    "color": "#A8D5BA",
                    "link": "https://learnloop.nl",
                },
                {
                    "text": "HC:X",
                    "color": "#686D73",
                    "link": "https://example.com/page2",
                },
                {
                    "text": "Diag toets",
                    "color": "#A8D5BA",
                    "link": "https://example.com/page3",
                },
                {
                    "text": "Study hard topics",
                    "color": "#A8D5BA",
                    "link": "https://example.com/page4",
                },
            ],
        },
        {
            "week": "Week 2",
            "activities": [
                {"text": "HC", "color": "#686D73", "link": "https://example.com/page5"},
                {
                    "text": "Voorb HC",
                    "color": "#EB5757",
                    "link": "https://example.com/page6",
                },
                {
                    "text": "WGK live feedback",
                    "color": "#F2994A",
                    "link": "https://example.com/page7",
                },
                {
                    "text": "Study hard",
                    "color": "#A8D5BA",
                    "link": "https://example.com/page8",
                },
            ],
        },
    ]


# Function to add a new activity block
def add_new_activity():
    st.session_state.activities.append(
        {"week": f"Week {len(st.session_state.activities) + 1}", "activities": []}
    )


# Function to create clickable containers
def create_clickable_container(text, color, link):
    st.markdown(
        f"""
        <a href="{link}" target="_blank">
            <div style="border-radius: 10px; border: 1px solid black; padding: 10px; background-color: {color}; text-align: center;">
                {text}
            </div>
        </a>
    """,
        unsafe_allow_html=True,
    )


# Render activities
for week in st.session_state.activities:
    st.markdown(f"### {week['week']}")
    cols = st.columns(
        len(week["activities"]) + 1
    )  # Add extra column for new activity button
    for i, activity in enumerate(week["activities"]):
        with cols[i]:
            create_clickable_container(
                activity["text"], activity["color"], activity["link"]
            )  # Correct key is 'text', not 'activity'

    # Add button to add a new activity in the respective week
    with cols[-1]:
        if st.button("+", key=f"add_{week['week']}"):
            week["activities"].append(
                {
                    "text": "New Activity",
                    "color": "#D3D3D3",
                    "link": "https://example.com/new",
                }
            )

# Button to add a new week
if st.button("Add New Week"):
    add_new_activity()


# Set the layout with two columns for the chat interfaces
col1, col2 = st.columns(2)

# Left Column: "Segment Theorie" Interface (With images, text, MCQs)
with col1:
    st.subheader("Segment Theorie")

    # Display some text and multiple-choice questions
    st.markdown("""
    **Theorie over Segmenten:**
    
    Hier komt de tekst van de theorie met betrekking tot het onderwerp.
    
    **Vraag 1:** Wat is het belangrijkste element van de segment theorie?
    """)

    # Multiple-choice question
    options = ["Optie 1", "Optie 2", "Optie 3", "Optie 4"]
    answer = st.radio("Kies het juiste antwoord:", options)

    # Feedback mechanism for MCQ
    if answer == "Optie 3":
        st.success("Correct!")
    elif answer:
        st.error("Fout, probeer opnieuw.")

    # Example of displaying an image
    st.image("https://via.placeholder.com/150", caption="Afbeelding over segmenten")

    # Chat input
    st.text_input("Jouw antwoord of vraag", key="segment_theory_input")
    st.button("Verstuur", key="send_segment_theory")

# Right Column: Q&A Interface for References
with col2:
    st.subheader("Q&A Studiedocumenten")

    # Display references and questions
    st.markdown("""
    **Vraag 1:** Hoe werkt deze theorie in praktijk?  
    _Referentie: [Link naar document 1](#)_
    
    **Vraag 2:** Zijn er meer toepassingen bekend?  
    _Referentie: [Link naar document 2](#)_
    """)

    # Chat input
    st.text_input("Zoek meer informatie of stel een vraag", key="qa_input")
    st.button("Verstuur", key="send_qa")

# Display a note to the user that copy-pasting is not allowed
st.write(
    "**Opmerking:** Copy-pasten is niet toegestaan. Extra informatie opzoeken zonder dat het antwoord wordt voorgezegd."
)


st.write("\n\n")
st.write("\n\n")
st.write("\n\n")

# Initialize session state for timeline progress
if "timeline_index" not in st.session_state:
    st.session_state["timeline_index"] = 0

# Define the timeline events
timeline_events = [
    "Begin met Segment Theorie",
    "Vraag 1 over Segment Theorie",
    "Feedback op Vraag 1",
    "Segment Theorie Deel 2",
    "Vraag 2 over Segment Theorie",
    "Einde van de les",
]

# Create columns for the main content
col1, col2 = st.columns([3, 6])  # Adjust column widths as needed

# Left column: Timeline
with col1:
    st.title("Tijdlijn")
    for idx, event in enumerate(timeline_events):
        if idx <= st.session_state["timeline_index"]:
            st.markdown(f"● **{event}**")
        else:
            st.markdown("○ " + event)

# Right column: Chat Interface
with col2:
    st.title("Chat Interface")

    # Display content based on the current timeline step
    if st.session_state["timeline_index"] == 0:
        st.subheader("Segment Theorie")
        st.markdown("Hier begint de uitleg van de segment theorie.")
        if st.button("Verder"):
            st.session_state["timeline_index"] += 1

    elif st.session_state["timeline_index"] == 1:
        st.subheader("Vraag 1")
        st.markdown("Wat is een segment?")
        options = ["A", "B", "C", "D"]
        answer = st.radio("Kies een antwoord:", options)
        if st.button("Verstuur Antwoord"):
            st.session_state["timeline_index"] += 1

    elif st.session_state["timeline_index"] == 2:
        st.subheader("Feedback Vraag 1")
        st.markdown("Correct! Het juiste antwoord is B.")
        if st.button("Volgende"):
            st.session_state["timeline_index"] += 1

    elif st.session_state["timeline_index"] == 3:
        st.subheader("Segment Theorie Deel 2")
        st.markdown("Hier wordt het tweede deel van de theorie uitgelegd.")
        if st.button("Verder"):
            st.session_state["timeline_index"] += 1

    elif st.session_state["timeline_index"] == 4:
        st.subheader("Vraag 2")
        st.markdown("Wat is een ander kenmerk van een segment?")
        options = ["X", "Y", "Z", "W"]
        answer = st.radio("Kies een antwoord:", options)
        if st.button("Verstuur Antwoord"):
            st.session_state["timeline_index"] += 1

    elif st.session_state["timeline_index"] == 5:
        st.subheader("Einde van de les")
        st.markdown("Gefeliciteerd! Je hebt het einde van de les bereikt.")


st.write("\n\n")
st.write("\n\n")
st.write("\n\n")

# Set up the layout
st.title("Feedback Inzicht (Klassikaal)")
st.subheader("Meest gemaakte fout")

# Highlight box for most common mistake
st.markdown(
    """
    <div style="background-color: #f9f5c4; padding: 10px; border-radius: 5px;">
        <b>Eiwitten zijn de <span style="color: #b8860b;">boodschappers</span> in de transductie route.</b>
    </div>
    """,
    unsafe_allow_html=True,
)

# Explanation text
st.markdown(
    """
    1) **Perceptie** van het signaal.  
    2) **Transductie** van het signaal binnen de cel.  
    3) De uiteindelijke **respons**.  

    Eiwitten functioneren als boodschappers in de transductie route.
    """
)

# Data for the feedback percentages
feedback_data = {
    "Opties": [
        "Perceptie van het signaal.",
        "Transductie van het signaal binnen de cel.",
        "De uiteindelijke respons.",
    ],
    "Fout": ["26%", "31%", "26%"],
    "Correct": ["57%", "32%", "57%"],
    "Geen Antwoord": ["17%", "34%", "17%"],
}

# Create a dataframe for better display
df = pd.DataFrame(feedback_data)

# Display the feedback percentages as a table
st.table(df)

st.write("\n\n")
st.write("\n\n")
st.write("\n\n")

# Layout for the interface based on the provided sketch
st.title("Studie Informatie")

# Readers section
st.subheader("Readers")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.checkbox("Naar Reader 1", key="reader1")

with col2:
    st.checkbox("Naar Reader 2", key="reader2")

with col3:
    st.checkbox("Kennis Clip 1", key="clip1")

with col4:
    st.checkbox("Kennis Clip 2", key="clip2")

# Books or Upload a document
st.subheader("Boek")
col5, col6 = st.columns(2)

with col5:
    st.file_uploader("Upload Document", type=["pdf", "docx", "txt"])

with col6:
    st.markdown("Boek placeholder")

# Colleges section
st.subheader("Colleges")
col7, col8 = st.columns(2)

with col7:
    st.checkbox("Kijk College 1", key="college1")

with col8:
    st.checkbox("Kijk College 2", key="college2")

# Topics that students find difficult
st.subheader("Onderwerpen die studenten moeilijk vinden")

topic1 = st.text_input("Onderwerp 1", key="topic1")
topic2 = st.text_input("Onderwerp 2", key="topic2")
topic3 = st.text_input("Onderwerp 3", key="topic3")

# Select topic button
if st.button("Selecteer Stof"):
    st.success(f"Geselecteerde onderwerpen: {topic1}, {topic2}, {topic3}")

st.write("\n\n")
st.write("\n\n")
st.write("\n\n")

from streamlit_player import st_player

# Display video player
st.title("Selecteer een Deel van de Lecture")

# Using streamlit_player without 'start_time' argument
st_player(
    "https://www.youtube.com/watch?v=0RqlP4B39i4&pp=ygUMbHVpc2RhIGZpbG1z",
    playing=False,
    controls=True,
)

# Double-ended slider for selecting start and end times
st.subheader("Selecteer de tijdsduur")
start_time, end_time = st.slider(
    "Selecteer start- en eindtijd (in seconden)", 0, 100, (10, 50)
)

# Confirm selection
if st.button("Selecteer deze delen"):
    st.success(f"Geselecteerde deel: van {start_time} seconden tot {end_time} seconden")


st.write("\n\n")
st.write("\n\n")
st.write("\n\n")
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import io


# Function to load and render PDF as images from a file-like object
def load_pdf_as_images(pdf_file):
    pdf_file_bytes = io.BytesIO(pdf_file.read())  # Convert UploadedFile to BytesIO
    pdf_document = fitz.open(
        stream=pdf_file_bytes, filetype="pdf"
    )  # Open the PDF using BytesIO stream
    images = []
    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    return images, pdf_document  # Return the images and the PDF document


# Function to extract text from selected regions
def extract_text_from_selected_areas(pdf_document, page_num, selected_areas):
    page = pdf_document.load_page(page_num)  # Get the specified page
    extracted_texts = []
    for area in selected_areas:
        rect = fitz.Rect(
            area["left"],
            area["top"],
            area["left"] + area["width"],
            area["top"] + area["height"],
        )
        text = page.get_text("text", clip=rect)
        extracted_texts.append((rect, text))
    return extracted_texts


# Streamlit Interface
st.title("Visual PDF Text Selector")

# Upload PDF file
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file is not None:
    # Load PDF and render pages as images
    pdf_images, pdf_document = load_pdf_as_images(uploaded_file)
    st.success(f"Loaded {len(pdf_images)} pages from the PDF.")

    # Select a page to view
    selected_page_num = st.selectbox(
        "Select the page to annotate:", options=list(range(1, len(pdf_images) + 1))
    )

    # Display the selected page as an image
    selected_page = pdf_images[selected_page_num - 1]
    st.image(selected_page, caption=f"Page {selected_page_num}")

    # Create a drawable canvas over the PDF image
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Rectangle fill color
        stroke_width=2,
        background_image=selected_page,
        height=selected_page.height,
        width=selected_page.width,
        drawing_mode="rect",  # Drawing rectangles to select text areas
        key="canvas",
    )

    # Extract and show the text when the user presses the button
    if st.button("Extract Text"):
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if objects:
                selected_areas = []
                for obj in objects:
                    selected_areas.append(
                        {
                            "left": obj["left"],
                            "top": obj["top"],
                            "width": obj["width"],
                            "height": obj["height"],
                        }
                    )

                # Extract text from selected areas
                extracted_texts = extract_text_from_selected_areas(
                    pdf_document, selected_page_num - 1, selected_areas
                )

                st.subheader("Extracted Text")
                for rect, text in extracted_texts:
                    st.text(f"Text from region {rect}:")
                    st.write(text if text else "No text found in this area.")
            else:
                st.warning(
                    "No areas selected yet. Draw a rectangle to select a portion of the page."
                )
        else:
            st.error("Please select areas before extracting text.")

    # Show extracted images from selected areas
    if st.button("Show Cropped Areas"):
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data["objects"]
            if objects:
                st.subheader("Cropped Images")
                for obj in objects:
                    left = obj["left"]
                    top = obj["top"]
                    width = obj["width"]
                    height = obj["height"]

                    # Crop the selected region
                    cropped_image = selected_page.crop(
                        (left, top, left + width, top + height)
                    )
                    st.image(
                        cropped_image,
                        caption=f"Cropped area: {left}, {top}, {width}, {height}",
                    )
            else:
                st.warning(
                    "No areas selected yet. Draw a rectangle to crop a portion of the page."
                )
