import base64
import streamlit as st


class Login:
    def __init__(self) -> None:
        self.surf_test_env = True

    def convert_image_base64(self, image_path):
        """Converts image in working dir to base64 format so it is
        compatible with html."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    def set_selected_phase(self, phase):
        print(f"Setting phase: {phase}")
        st.session_state.selected_phase = phase
        self.db_dal.update_last_phase(phase)

    def fetch_nonce_from_query(self):
        return st.query_params.get("nonce", None)

    def render_page(self):
        """This is the first page the user sees when visiting the website and
        prompts the user to login via SURFconext."""
        columns = st.columns([1, 0.9, 1])
        with columns[1]:
            welcome_title = "Klinische Neuropsychologie"
            logo_base64 = self.convert_image_base64("src/data/content/images/logo.png")
            if self.surf_test_env:
                href = "http://localhost:3000/"
            else:
                href = "https://learnloop.datanose.nl/"

            html_content = f"""
            <div style='text-align: center; margin: 20px;'>
                <img src='data:image/png;base64,{logo_base64}' alt='Logo' style='max-width: 25%; height: auto; margin-bottom: 40px'>
                <h2 style='color: #333; margin-bottom: 20px'>{welcome_title}</h2>
                <a href={href} target="_self" style="text-decoration: none;">
                    <button style='font-size:20px; border: none; color: white; padding: 10px 20px; \
                    text-align: center; text-decoration: none; display: block; width: 100%; margin: \
                    4px 0px; cursor: pointer; background-color: #4CAF50; border-radius: 12px;'>UvA Login</button>
                </a>
            </div>"""

            st.markdown(html_content, unsafe_allow_html=True)

    def run(self):
        self.render_page()
