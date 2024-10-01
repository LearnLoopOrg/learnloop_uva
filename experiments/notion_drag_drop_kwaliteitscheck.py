# Adjusting the code for the latest version of `streamlit-sortables`

import streamlit as st
from streamlit_sortables import sortables
import uuid

# Initialize session state to store text blocks
if "text_blocks" not in st.session_state:
    st.session_state.text_blocks = [
        {"id": str(uuid.uuid4()), "text": "Start typing here..."}
    ]


# Function to handle reordering of text blocks
def reorder_blocks():
    ordered_ids = st.session_state.sorted_blocks
    new_order = [
        block
        for block_id in ordered_ids
        for block in st.session_state.text_blocks
        if block["id"] == block_id
    ]
    st.session_state.text_blocks = new_order


# Create a sortable container for text blocks
sorted_ids = sortables(
    ids=[block["id"] for block in st.session_state.text_blocks],
    direction="vertical",
    key="sorted_blocks",
)

# Update text blocks based on reordering
for i, block_id in enumerate(sorted_ids):
    block = next(
        (block for block in st.session_state.text_blocks if block["id"] == block_id),
        None,
    )
    if block:
        block["text"] = st.text_area(
            f"Block {block['id']}", block["text"], key=block["id"]
        )

# Reorder blocks based on user interaction
reorder_blocks()

# Button to add a new text block
if st.button("Add new block"):
    st.session_state.text_blocks.append(
        {"id": str(uuid.uuid4()), "text": "New block..."}
    )

# Display final block order and content
st.write("Current block order and content:", st.session_state.text_blocks)
# Adjusting the code for the latest version of `streamlit-sortables`

import streamlit as st
from streamlit_sortables import sortables
import uuid

# Initialize session state to store text blocks
if "text_blocks" not in st.session_state:
    st.session_state.text_blocks = [
        {"id": str(uuid.uuid4()), "text": "Start typing here..."}
    ]


# Function to handle reordering of text blocks
def reorder_blocks():
    ordered_ids = st.session_state.sorted_blocks
    new_order = [
        block
        for block_id in ordered_ids
        for block in st.session_state.text_blocks
        if block["id"] == block_id
    ]
    st.session_state.text_blocks = new_order


# Create a sortable container for text blocks
sorted_ids = sortables(
    ids=[block["id"] for block in st.session_state.text_blocks],
    direction="vertical",
    key="sorted_blocks",
)

# Update text blocks based on reordering
for i, block_id in enumerate(sorted_ids):
    block = next(
        (block for block in st.session_state.text_blocks if block["id"] == block_id),
        None,
    )
    if block:
        block["text"] = st.text_area(
            f"Block {block['id']}", block["text"], key=block["id"]
        )

# Reorder blocks based on user interaction
reorder_blocks()

# Button to add a new text block
if st.button("Add new block"):
    st.session_state.text_blocks.append(
        {"id": str(uuid.uuid4()), "text": "New block..."}
    )

# Display final block order and content
st.write("Current block order and content:", st.session_state.text_blocks)
