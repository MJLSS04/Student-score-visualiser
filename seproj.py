import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from fpdf import FPDF

# Set Streamlit page configuration
st.set_page_config(page_title="Student Score Analysis and Prediction Tool", layout='wide')

motivational_quotes = [
    "The only way to do great work is to love what you do. - Steve Jobs",
    "Success is not final, failure is not fatal: It is the courage to continue that counts. - Winston Churchill",
    "Believe you can and you're halfway there. - Theodore Roosevelt",
    "The only limit to our realization of tomorrow will be our doubts of today. - Franklin D. Roosevelt",
    "The only person you should try to be better than is the person you were yesterday. - Unknown"
]

st.sidebar.subheader("**Motivational Quote:**")
st.sidebar.write("**" + random.choice(motivational_quotes) + "**")

# Custom CSS for background color and font style
st.markdown(
    """
    <style>
    .reportview-container, .main, .block-container {
        background-color: #DAF0F7;
    }
    .stSidebar .sidebar-content, .stSidebar .sidebar-content .stHeader {
        color: #ffffff; /* Change sidebar content and header color to white */
    }
    .stMarkdown, .stSelectbox, .stTextInput, .stNumberInput, .stSlider .horizontal {
        font-family: 'Helvetica', sans-serif;
        color: #3B3B3B;
    }
    .stButton>button {
        font-family: 'Helvetica', sans-serif;
        color: #ffffff;
        background-color: #3B3B3B;
        border-color: #3B3B3B;
    }
    .stButton>button:hover {
        background-color: #757575;
        border-color: #757575;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        font-family: serif;
        color: black; /* Added to ensure titles are black */
    }
    .stTitle {
        color: black; /* Added to ensure titles are black */
    }
    .card {
        background-color: #FFE5B4;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Define subject weightages and their splits
subject_weightages = {
    "BD": {"M1": 15, "M2": 15, "EndSem": 30, "Others": 40},
    "HPC": {"M1": 10, "M2": 10, "EndSem": 40, "Others": 40},
    "SE": {"M1": 10, "M2": 10, "EndSem": 30, "Others": 50},
    "CN": {"M1": 15, "M2": 15, "EndSem": 30, "Others": 40},
    "CB": {"M1": 10, "M2": 30, "EndSem": 40, "Others": 20}
}

# Define total marks for each component
total_marks = {
    "BD": {"M1": 30, "M2": 30, "EndSem": 100, "Others": 40},
    "HPC": {"M1": 0, "M2": 100, "EndSem": 100, "Others": 40},
    "SE": {"M1": 30, "M2": 30, "EndSem": 100, "Others": 50},
    "CN": {"M1": 40, "M2": 50, "EndSem": 100, "Others": 40},
    "CB": {"M1": 10, "M2": 30, "EndSem": 100, "Others": 20}
}

# Adjusted credits for each course
course_credits = {"BD": 3, "HPC": 3, "SE": 3, "CN": 4, "CB": 3}

# Function to calculate required marks
def calculate_required_marks(target_sgpa, total_marks, subject_weightages):
    required_marks = {}
    total_credits = sum(course_credits.values())
    for subject, components in subject_weightages.items():
        required_marks[subject] = {}
        subject_credit = course_credits[subject]

        for component, weightage in components.items():
            max_marks_for_component = total_marks[subject][component]
            required_marks[subject][component] = min(
                (target_sgpa * total_credits * max_marks_for_component * weightage) / (10 * subject_credit * 100),
                max_marks_for_component
            )

    return required_marks

# Function to adjust marks based on completed exams and obtained marks
def adjust_marks(target_sgpa, current_marks, required_marks, completed_exams):
    adjusted_marks = {subject: components.copy() for subject, components in required_marks.items()}
    
    for subject, components in current_marks.items():
        for component, marks in components.items():
            if component in completed_exams[subject]:
                adjusted_marks[subject][component] = marks
    
    for subject, components in adjusted_marks.items():
        total_weight = sum(subject_weightages[subject].values())
        remaining_weight = total_weight - sum(
            weight for comp, weight in subject_weightages[subject].items() if comp in completed_exams[subject]
        )
        if remaining_weight > 0:
            remaining_diff = sum(
                (required_marks[subject][comp] - current_marks[subject][comp]) 
                for comp in subject_weightages[subject] if comp in completed_exams[subject]
            )
            for comp in subject_weightages[subject]:
                if comp not in completed_exams[subject]:
                    adjusted_marks[subject][comp] = required_marks[subject][comp] + remaining_diff * (subject_weightages[subject][comp] / remaining_weight)
                    adjusted_marks[subject][comp] = min(adjusted_marks[subject][comp], total_marks[subject][comp])

    return adjusted_marks

# Function to check if it's feasible to achieve the target SGPA
def is_feasible(target_sgpa, current_marks, adjusted_marks):
    for subject, components in current_marks.items():
        for component, marks in components.items():
            if component in adjusted_marks[subject] and marks > adjusted_marks[subject][component]:
                return False
    return True

# Function to generate PDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Gradesheet', 0, 1, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def generate_pdf(current_marks, adjusted_marks, target_sgpa):
    pdf = PDF()
    pdf.add_page()

    pdf.chapter_title("Target SGPA: {:.2f}".format(target_sgpa))
    pdf.chapter_title("Current Marks and Required Marks")
    
    for subject, components in current_marks.items():
        pdf.chapter_title(f"\n{subject}")
        for component, marks in components.items():
            required = adjusted_marks[subject][component]
            pdf.chapter_body(f"{component} marks: {marks} | Required: {required:.2f}")
    
    return pdf.output(dest='S').encode('latin1')

# Initialize Streamlit app
st.title("🎓 Welcome to the Student Score Analysis and Prediction Tool")
st.write("This tool helps you analyze your current marks and predict the required marks to achieve your target SGPA.")

# Input marks achieved so far
current_marks = {}
st.sidebar.header("Enter Your Marks")
for subject in subject_weightages.keys():
    with st.sidebar.expander(f"Marks for {subject}", expanded=False):
        current_marks[subject] = {}
        for component in subject_weightages[subject].keys():
            current_marks[subject][component] = st.number_input(
                f"{component} marks for {subject}:", min_value=0, max_value=total_marks[subject][component], step=1, key=f"{subject}_{component}"
            )

# Input completed exams
completed_exams = {}
st.sidebar.header("Enter Completed Exams")
for subject in subject_weightages.keys():
    with st.sidebar.expander(f"Exams completed for {subject}", expanded=False):
        completed_exams[subject] = st.multiselect(
            f"Exams completed for {subject}:",
            subject_weightages[subject].keys(),
            key=f"{subject}_completed_exams"
        )

# Input target SGPA
target_sgpa = st.sidebar.number_input(
    "Enter your target SGPA for the semester:", min_value=0.0, max_value=10.0, step=0.1
)

# Calculate required marks
required_marks = calculate_required_marks(target_sgpa, total_marks, subject_weightages)

# Adjust marks based on completed exams and marks obtained
adjusted_marks = adjust_marks(target_sgpa, current_marks, required_marks, completed_exams)

# Check if it's feasible to achieve the target SGPA
feasible = is_feasible(target_sgpa, current_marks, adjusted_marks)

if feasible:
    st.subheader("📊 Required Marks to Achieve Target SGPA")
    cols = st.columns(len(subject_weightages))
    for idx, (subject, components) in enumerate(adjusted_marks.items()):
        with cols[idx]:
            st.markdown(f"<div class='card'><h4>{subject}</h4>", unsafe_allow_html=True)
            for component, marks in components.items():
                st.write(f"{component}: {marks:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.error("It is not possible to achieve the target SGPA with the current marks.")

# Visualization options
st.subheader("📈 Visualize Your Marks")
visualization_type = st.selectbox("Select the type of visualization you want to see:", ["Histogram", "Heatmap", "Line Graph", "Scatter Plot", "Pie Chart"])

# Visualize the marks based on the selected visualization type
if visualization_type == "Histogram":
    st.subheader("📊 Histogram of Current Marks")
    fig, ax = plt.subplots(figsize=(12, 6))
    for subject, components in current_marks.items():
        marks = [components[comp] if components[comp] is not None else 0 for comp in subject_weightages[subject].keys()]
        ax.hist(marks, bins=10, alpha=0.5, label=subject)
    ax.set_xlabel("Marks")
    ax.set_ylabel("Frequency")
    ax.legend(title="Subjects")
    st.pyplot(fig)

elif visualization_type == "Heatmap":
    st.subheader("📊 Heatmap of Current Marks")
    data = []
    for subject, components in current_marks.items():
        marks = [components[comp] if components[comp] is not None else 0 for comp in subject_weightages[subject].keys()]
        data.append(marks)
    df = pd.DataFrame(data, index=subject_weightages.keys(), columns=subject_weightages["BD"].keys())
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(df, annot=True, cmap="YlGnBu", fmt=".1f", linewidths=0.5, cbar=False, ax=ax)
    st.pyplot(fig)

elif visualization_type == "Line Graph":
    st.subheader("📊 Line Graph of Current Marks")
    fig, ax = plt.subplots(figsize=(12, 6))
    for subject, components in current_marks.items():
        marks = [components[comp] if components[comp] is not None else 0 for comp in subject_weightages[subject].keys()]
        ax.plot(subject_weightages[subject].keys(), marks, marker='o', label=subject)
    ax.set_xlabel("Components")
    ax.set_ylabel("Marks")
    ax.legend(title="Subjects")
    st.pyplot(fig)

elif visualization_type == "Scatter Plot":
    st.subheader("📊 Scatter Plot of Current Marks")
    fig, ax = plt.subplots(figsize=(12, 6))
    for subject, components in current_marks.items():
        marks = [components[comp] if components[comp] is not None else 0 for comp in subject_weightages[subject].keys()]
        ax.scatter(subject_weightages[subject].keys(), marks, label=subject)
    ax.set_xlabel("Components")
    ax.set_ylabel("Marks")
    ax.legend(title="Subjects")
    st.pyplot(fig)

elif visualization_type == "Pie Chart":
    st.subheader("📊 Pie Chart of Course Credits")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.pie(course_credits.values(), labels=course_credits.keys(), autopct='%1.1f%%', startangle=90)
    ax.axis('equal')
    st.pyplot(fig)


# Additional features
st.sidebar.header("**Additional Features**")

# Overall analysis
if st.sidebar.checkbox("**Overall Analysis**"):
    overall_analysis = pd.DataFrame(current_marks)
    st.subheader("**Overall Analysis:**")
    st.write(overall_analysis.describe())

# Highest, least, average subject-wise scores
if st.sidebar.checkbox("**Subject-wise Scores**"):
    st.subheader("**Subject-wise Scores:**")
    
    # Define highest, least, and average scores for each subject and exam type
    subject_scores = {
        "BD": {"M1": {"highest": 30, "least": 0, "avg": 15.5},
               "M2": {"highest": 30, "least": 0, "avg": 15.5},
               "EndSem": {"highest": 95, "least": 0, "avg": 45.5}},
        "HPC": {"M2": {"highest": 60, "least": 15, "avg": 20},
                "EndSem": {"highest": 80, "least": 0, "avg": 40}},
        "SE": {"M1": {"highest": 249, "least": 0, "avg": 125},
               "M2": {"highest": 249, "least": 0, "avg": 125},
               "EndSem": {"highest": 90, "least": 0, "avg": 50}},
        "CN": {"M1": {"highest": 32, "least": 12, "avg": 22},
               "M2": {"highest": 32, "least": 12, "avg": 22},
               "EndSem": {"highest": 85, "least": 0, "avg": 35}},
        "CB": {"M1": {"highest": 8, "least": 0, "avg": 6},
               "M2": {"highest": 29, "least": 0, "avg": 15},
               "EndSem": {"highest": 90, "least": 0, "avg": 60}}
    }
    
    # Display scores for each subject and exam type side by side
    cols = st.columns(len(subject_scores))
    for i, (subject, scores) in enumerate(subject_scores.items()):
        with cols[i]:
            st.markdown(f"<style>.stCheckbox>div {{background-color: #DAF0F7;}}</style>", unsafe_allow_html=True)
            st.subheader(f"**{subject} Scores:**")
            for exam, details in scores.items():
                st.write(f"#### **{exam}:**")
                st.markdown(f"<div class='card'>", unsafe_allow_html=True)
                st.write(f"**Highest score:** {details['highest']}")
                st.write(f"**Least score:** {details['least']}")
                st.write(f"**Average score:** {details['avg']}")
                st.markdown("</div>", unsafe_allow_html=True)

# Upcoming exams, assignment deadlines schedule (calendar)
if st.sidebar.checkbox("**Upcoming Schedule**"):
    st.subheader("**Upcoming Schedule:**")
    schedule = {
        "27th May 2023 (Monday)": "BD",
        "28th May 2023 (Tuesday)": "HPC",
        "29th May 2023 (Wednesday)": "CN",
        "30th May 2023 (Thursday)": "SE",
        "5th June 2023 (Wednesday)": "CB",
    }
    for date, subject in schedule.items():
        st.write(f"**{date}** - {subject}")

# Faculty comments
if st.sidebar.checkbox("**Chatbot**"):
    st.subheader("**Chatbot:**")
    chatbot_response = st.text_area("Enter comments or questions here:")
    if chatbot_response:
        # Here, you can integrate with a chatbot API or provide predefined responses.
        st.write(f"Response to '{chatbot_response}': This is a placeholder response from the chatbot.")

# Emotion button
if st.sidebar.checkbox("**Emotion Button**"):
    st.subheader("**Emotion Button:**")

    # Custom CSS for larger emojis
    st.markdown(
        """
        <style>
        .large-emoji {
            font-size: 32px; /* Adjust the size as needed */
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    cols = st.columns(len(current_marks))
    for i, (subject, components) in enumerate(current_marks.items()):
        with cols[i]:
            st.subheader(f"**{subject}**")
            for component, marks in components.items():
                required = required_marks[subject][component]
                if marks >= required:
                    st.write(f"{component}: {marks} <span class='large-emoji'>😊</span>", unsafe_allow_html=True)
                else:
                    st.write(f"{component}: {marks} <span class='large-emoji'>😢</span>", unsafe_allow_html=True)


# Add a download button for the gradesheet as PDF
st.subheader("📥 Download Your Gradesheet")
if st.button("Download Gradesheet as PDF"):
    pdf_content = generate_pdf(current_marks, adjusted_marks, target_sgpa)
    st.download_button(label="Download Gradesheet as PDF", data=pdf_content, file_name="gradesheet.pdf", mime='application/pdf')