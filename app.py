import streamlit as st
import pandas as pd
import json
import os
import uuid
import qrcode
from fpdf import FPDF
from datetime import datetime

VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
PASS_MARK = 4

# -----------------------------
# Load Data
# -----------------------------

students = pd.read_excel("students.xlsx")
quiz = pd.read_excel("quiz.xlsx")

if os.path.exists("progress.json"):
    with open("progress.json") as f:
        progress = json.load(f)
else:
    progress = {}

# -----------------------------
# Save Progress
# -----------------------------

def save_progress():
    with open("progress.json", "w") as f:
        json.dump(progress, f)

# -----------------------------
# Generate Certificate
# -----------------------------

def generate_certificate(name, regno, score, total):

    cert_id = "ML-" + str(uuid.uuid4())[:8]

    qr_data = f"Certificate ID: {cert_id}\nName:{name}\nMarks:{score}/{total}"

    qr = qrcode.make(qr_data)
    qr_path = f"qr_{regno}.png"
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

    cert_path = f"certificates/{regno}_certificate.pdf"

    pdf.output(cert_path)

    return cert_path

# -----------------------------
# UI
# -----------------------------

st.title("🎓 Microlearning Platform")

regno = st.text_input("Enter Register Number")

if st.button("Login"):

    student = students[students["regno"]==regno]

    if student.empty:
        st.error("Invalid Register Number")
        st.stop()

    name = student.iloc[0]["name"]

    st.success(f"Welcome {name}")

    # Already completed
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

    # --------------------------
    # VIDEO
    # --------------------------

    st.subheader("Watch the Learning Video")

    st.video(VIDEO_URL)

    if st.button("I have completed watching the video"):

        st.session_state.video_done = True

    # --------------------------
    # QUIZ
    # --------------------------

    if st.session_state.get("video_done"):

        st.subheader("Quiz")

        answers = {}

        for i,row in quiz.iterrows():

            q = row["Question"]

            options = [
                row["OptionA"],
                row["OptionB"],
                row["OptionC"],
                row["OptionD"]
            ]

            ans = st.radio(q,options,key=i)

            answers[i] = ans

        if st.button("Submit Quiz"):

            score = 0
            total = quiz["Marks"].sum()

            for i,row in quiz.iterrows():

                correct = row["Answer"]
                marks = row["Marks"]

                selected = answers[i]

                if selected == row[f"Option{correct}"]:
                    score += marks

            st.write(f"Score: {score}/{total}")

            cert_path = generate_certificate(name,regno,score,total)

            progress[regno] = {
                "score":score,
                "certificate":cert_path
            }

            save_progress()

            st.success("Certificate Generated!")

            with open(cert_path,"rb") as f:
                st.download_button(
                    "Download Certificate",
                    f,
                    file_name="certificate.pdf"
                )
