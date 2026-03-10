import streamlit as st
import pandas as pd
import json
import os
import uuid
import qrcode
from fpdf import FPDF
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

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
# SESSION STATE
# -----------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "video_done" not in st.session_state:
    st.session_state.video_done = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

if "regno" not in st.session_state:
    st.session_state.regno = ""

if "name" not in st.session_state:
    st.session_state.name = ""

# -----------------------
# LOAD STUDENTS
# -----------------------

students = pd.read_excel(STUDENT_FILE, dtype=str)

students["regno"] = students["regno"].astype(str).str.replace(".0","").str.strip()
students["name"] = students["name"].astype(str).str.strip()

students = students.dropna()

# -----------------------
# LOAD QUIZ
# -----------------------

quiz = pd.read_excel(QUIZ_FILE)

quiz.columns = quiz.columns.str.strip()

# -----------------------
# LOAD PROGRESS
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

def save_progress():

    with open(PROGRESS_FILE,"w") as f:
        json.dump(progress,f,indent=4)

# -----------------------
# CERTIFICATE
# -----------------------

def generate_certificate(name, regno, score, total):

    cert_id = "ML-" + str(uuid.uuid4())[:8]

    qr_text = f"Certificate ID:{cert_id}\nName:{name}\nMarks:{score}/{total}"

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
    pdf.cell(297,10,f"Score: {score}/{total}",align="C")

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
# UI
# -----------------------

st.title("🎓 Microlearning Platform")

# -----------------------
# LOGIN
# -----------------------

if not st.session_state.logged_in:

    regno = st.text_input("Enter Register Number")

    if st.button("Login"):

        student = students[students["regno"] == regno]

        if student.empty:

            st.error("Invalid Register Number")

        else:

            st.session_state.logged_in = True
            st.session_state.regno = regno
            st.session_state.name = student.iloc[0]["name"]

            st.session_state.start_time = datetime.now()

            st.rerun()

# -----------------------
# AFTER LOGIN
# -----------------------

if st.session_state.logged_in:

    regno = st.session_state.regno
    name = st.session_state.name

    st.success(f"Welcome {name}")

    # completed already
    if regno in progress:

        st.success("You already completed this module")

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

    if not st.session_state.video_done:

        st.subheader("Watch Learning Video")

        st.video(VIDEO_URL)

        st_autorefresh(interval=1000,key="timer")

        elapsed = (datetime.now() - st.session_state.start_time).seconds

        remaining = 90 - elapsed

        if remaining > 0:

            st.warning(f"Quiz unlocks in {remaining} seconds")

        else:

            st.success("Video watch completed")

            if st.button("Proceed to Quiz"):

                st.session_state.video_done = True
                st.rerun()

    # -----------------------
    # QUIZ
    # -----------------------

    if st.session_state.video_done:

        st.subheader("Quiz")

        answers = {}

        for i,row in quiz.iterrows():

            options = [
                row["Option A"],
                row["Option B"],
                row["Option C"],
                row["Option D"]
            ]

            answers[i] = st.radio(row["Question"],options,key=i)

        if st.button("Submit Quiz"):

            score = 0
            total = len(quiz)

            for i,row in quiz.iterrows():

                correct = row[f"Option {row['Answer']}"]

                if answers[i] == correct:
                    score += 1

            st.success(f"Your Score: {score}/{total}")

            cert_path = generate_certificate(name,regno,score,total)

            progress[regno] = {
                "score": score,
                "certificate": cert_path
            }

            save_progress()

            with open(cert_path,"rb") as f:

                st.download_button(
                    "Download Certificate",
                    f,
                    file_name="certificate.pdf"
                )
