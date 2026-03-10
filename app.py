import streamlit as st
import pandas as pd
import json
import os
import uuid
import qrcode
from fpdf import FPDF
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------

VIDEO_URL = "https://youtu.be/e-mCCdx6vjk"

STUDENT_FILE = "students.xlsx"
QUIZ_FILE = "quiz.xlsx"
PROGRESS_FILE = "progress.json"

CERT_FOLDER = "certificates"

os.makedirs(CERT_FOLDER, exist_ok=True)

# -----------------------
# LOAD STUDENTS
# -----------------------

students = pd.read_excel(STUDENT_FILE, dtype=str)

students["regno"] = students["regno"].astype(str).str.strip()
students["name"] = students["name"].astype(str).str.strip()

# -----------------------
# LOAD QUIZ
# -----------------------

quiz = pd.read_excel(QUIZ_FILE)

# -----------------------
# LOAD PROGRESS SAFE
# -----------------------

def load_progress():

    if not os.path.exists(PROGRESS_FILE):
        return {}

    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except:
        return {}

progress = load_progress()

# -----------------------
# SAVE PROGRESS
# -----------------------

def save_progress():

    with open(PROGRESS_FILE,"w") as f:
        json.dump(progress,f,indent=4)

# -----------------------
# CERTIFICATE GENERATOR
# -----------------------

def generate_certificate(name, regno, score, total):

    cert_id = "ML-" + str(uuid.uuid4())[:8]

    qr_text = f"Certificate ID: {cert_id}\nName:{name}\nMarks:{score}/{total}"

    qr = qrcode.make(qr_text)

    qr_path = f"{CERT_FOLDER}/{regno}_qr.png"

    qr.save(qr_path)

    pdf = FPDF('L','mm','A4')

    pdf.add_page()

    pdf.image("certificate_bg.png",0,0,297,210)

    pdf.set_font("Arial","B",28)

    pdf.set_xy(0,90)

    pdf.cell(297,10,name,align="C")

    pdf.set_font("Arial","",16)

    pdf.set_xy(0,110)

    pdf.cell(297,10,f"Register Number: {regno}",align="C")

    pdf.set_xy(0,125)

    pdf.cell(297,10,f"Score: {score} / {total}",align="C")

    pdf.set_xy(0,140)

    pdf.cell(297,10,f"Certificate ID: {cert_id}",align="C")

    date = datetime.today().strftime("%d-%m-%Y")

    pdf.set_xy(0,155)

    pdf.cell(297,10,f"Date: {date}",align="C")

    pdf.image(qr_path,240,140,30)

    cert_path = f"{CERT_FOLDER}/{regno}_certificate.pdf"

    pdf.output(cert_path)

    return cert_path

# -----------------------
# STREAMLIT UI
# -----------------------

st.title("🎓 Microlearning Platform")

regno = st.text_input("Enter Register Number").strip()

if st.button("Login"):

    student = students[students["regno"] == regno]

    if student.empty:

        st.error("Invalid Register Number")

        st.stop()

    name = student.iloc[0]["name"]

    st.success(f"Welcome {name}")

    # -----------------------
    # CHECK COMPLETED
    # -----------------------

    if regno in progress:

        st.success("You have already completed this module")

        cert_path = progress[regno]["certificate"]

        if os.path.exists(cert_path):

            with open(cert_path,"rb") as f:

                st.download_button(
                    "Download Certificate",
                    f,
                    file_name="certificate.pdf"
                )

        st.stop()

    # -----------------------
    # VIDEO
    # -----------------------

    st.subheader("Watch Learning Video")

    st.video(VIDEO_URL)

    if st.button("I Completed Watching"):

        st.session_state.video_done = True

# -----------------------
# QUIZ
# -----------------------

if st.session_state.get("video_done"):

    st.subheader("Quiz")

    answers = {}

    for i,row in quiz.iterrows():

        options = [
            row["OptionA"],
            row["OptionB"],
            row["OptionC"],
            row["OptionD"]
        ]

        selected = st.radio(row["Question"],options,key=i)

        answers[i] = selected

    if st.button("Submit Quiz"):

        score = 0

        total = quiz["Marks"].sum()

        for i,row in quiz.iterrows():

            correct = row[f"Option{row['Answer']}"]

            if answers[i] == correct:

                score += row["Marks"]

        st.success(f"Your Score: {score} / {total}")

        student = students[students["regno"] == regno]

        name = student.iloc[0]["name"]

        cert_path = generate_certificate(name,regno,score,total)

        progress[regno] = {
            "score": score,
            "certificate": cert_path
        }

        save_progress()

        st.success("Certificate Generated Successfully")

        with open(cert_path,"rb") as f:

            st.download_button(
                "Download Certificate",
                f,
                file_name="certificate.pdf"
            )
