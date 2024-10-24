from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi
import streamlit as st
import matplotlib.pyplot as plt
import utils.db_config as db_config
from collections import defaultdict
from matplotlib.ticker import MaxNLocator
from data.data_access_layer import DatabaseAccess


load_dotenv(override=True)


class PlotUsage:
    def __init__(self) -> None:
        st.session_state.modules = []
        self.db_dal = DatabaseAccess()

    def extract_question_dates(self, progress_counter, start_date, end_date):
        dates = []
        for segment_value in progress_counter.values():
            if segment_value is not None and segment_value["type"] == "question":
                entry_dates = [
                    entry_date
                    for entry_date in segment_value["entries"]
                    if entry_date >= start_date and entry_date <= end_date
                ]
                if entry_dates != []:
                    dates.append(
                        entry_dates[0]
                    )  # Only include the first date bc we want to count the unique questions

        return dates

    def calculate_percentage(self, questions_made, total_questions):
        percentage = (len(questions_made) / total_questions) * 100
        return percentage

    def cluster_percentages(self, percentages):
        clusters = defaultdict(int)
        for percent in percentages:
            if 0 <= percent <= 10:
                clusters["0%-10%"] += 1
            elif 11 <= percent <= 20:
                clusters["11%-20%"] += 1
            elif 21 <= percent <= 30:
                clusters["21%-30%"] += 1
            elif 31 <= percent <= 40:
                clusters["31%-40%"] += 1
            elif 41 <= percent <= 50:
                clusters["41%-50%"] += 1
            elif 51 <= percent <= 60:
                clusters["51%-60%"] += 1
            elif 61 <= percent <= 70:
                clusters["61%-70%"] += 1
            elif 71 <= percent <= 80:
                clusters["71%-80%"] += 1
            elif 81 <= percent <= 90:
                clusters["81%-90%"] += 1
            elif 91 <= percent <= 100:
                clusters["91%-100%"] += 1
        return clusters

    def plot_clusters(self, clusters):
        sorted_clusters = dict(
            sorted(
                clusters.items(), key=lambda x: int(x[0].split("%")[0].split("-")[0])
            )
        )
        categories = list(sorted_clusters.keys())
        counts = list(sorted_clusters.values())

        plt.bar(categories, counts, edgecolor="blue")
        plt.xlabel("Percentage gemaakte vragen")
        plt.ylabel("Aantal studenten")
        plt.title("Cluster percentage gemaakte vragen")
        plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))
        st.pyplot(plt.gcf())

    def count_all_questions(self):
        total = 0
        for module in st.session_state.modules:
            st.session_state.page_content = self.db_dal.fetch_module_content(module)
            total += len(
                [
                    segment
                    for segment in st.session_state.page_content["segments"]
                    if segment["type"] == "question"
                ]
            )

        return total

    def collect_all_progress_data(self):
        all_progress_data_per_user = {}
        documents = self.db_dal.fetch_all_documents()
        for user_doc in documents:
            progress_data = []
            for module in st.session_state.modules:
                progress_counter = self.db_dal.fetch_progress_counter(module, user_doc)
                if progress_counter is not None:
                    progress_data.append(progress_counter)

            all_progress_data_per_user[user_doc["username"]] = progress_data
        return all_progress_data_per_user

    def render_plot(self, course_name):
        # st.session_state.modules = self.db_dal.determine_modules(course_name)
        # Hardcoded, want er zijn een aantal modules weggehaald uit de database
        st.session_state.modules = [
            "Introductiecollege",
            "DSM en diermodellen",
            "Dementie",
            "Eetstoornissen (Anorexia en obesitas)",
            "Traumatisch hersenletsel",
            "Genetische ontwikkelingsstoornissen",
            "Genderdysforie",
            "Hersentumoren",
            "Vasculaire cognitieve stoornissen",
            "Autisme en ADHD",
            "Psychofarmacologie",
            "Epilepsie",
            "Migraine",
            "Multiple sclerose",
            "Depressie",
            "Neuropsychiatrie en schizofrenie",
            "Depressie, ECT, TMS, DBS",
            "Huntington- en Parkinson-spectrumstoornissen",
            "Angststoornissen en pijn",
        ]
        numb_of_questions = self.count_all_questions()
        all_progress_data_per_user = self.collect_all_progress_data()
        print("all_progress_data_per_user ", all_progress_data_per_user)
        all_percentages = []
        for user_data_pcs_list in all_progress_data_per_user.values():
            question_dates = []
            for pcs in user_data_pcs_list:
                module_question_dates = self.extract_question_dates(
                    pcs, self.start_date, self.end_date
                )
                question_dates.extend(module_question_dates)

            individual_percentage = self.calculate_percentage(
                question_dates, numb_of_questions
            )
            all_percentages.append(individual_percentage)

        clusters = self.cluster_percentages(all_percentages)
        print("all_percentages: ", all_percentages)
        st.write("Aantal studenten ingelogd: ", str(len(all_percentages)))
        count_above_zero = sum(1 for value in all_percentages if value > 0)

        st.write(
            f"Aantal studenten die een vraag hebben gemaakt: {count_above_zero}",
        )
        self.plot_clusters(clusters)

    def render_date_input(self):
        col_1, col_2 = st.columns(2)
        with col_1:
            start_date = st.date_input("From")
        with col_2:
            end_date = st.date_input("Up to and including")

        self.start_date = start_date.strftime("%Y-%m-%d")
        self.end_date = end_date.strftime("%Y-%m-%d")

    def render_info(self):
        st.title("Plot KPI")
        st.write(
            "Studenten geclusterd op basis van hoeveel procent van alle vragen ze gedurende een periode hebben gemaakt."
        )


if __name__ == "__main__":
    COSMOS_URI = os.getenv("COSMOS_URI")
    st.session_state.db = db_config.connect_db(COSMOS_URI)

    plot_usage = PlotUsage()

    plot_usage.render_info()
    plot_usage.render_date_input()

    course_name = st.text_input(
        "Course name you want to know the stats for",
        "Klinische Neuropsychologie",
        key="course_name",
    )

    if st.button("Render plot", use_container_width=True):
        print("Rendering plot for course: ", course_name)
        plot_usage.render_plot(course_name)
