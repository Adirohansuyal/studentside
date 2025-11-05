import streamlit as st
import cv2
import time
import numpy as np
from datetime import datetime
from pyzbar.pyzbar import decode
from supabase_client import supabase

# Streamlit UI config
st.set_page_config(page_title="Student Attendance", page_icon="🎓", layout="centered")

# CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
}
.login-card, .scan-card {
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 10px;
    border: 1px solid #e9ecef;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🎓 Student Attendance Portal</h1>
    <p>Login and scan QR code for attendance</p>
</div>
""", unsafe_allow_html=True)

# Session variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_name" not in st.session_state:
    st.session_state.student_name = None

def validate_session_qr(qr_data, session_id):
    try:
        parts = qr_data.split(":")
        if parts[0] == "SESSION" and parts[1] == session_id:
            qr_timestamp = int(parts[3])
            # QR valid for 10 seconds
            return abs(int(time.time()) - qr_timestamp) <= 10
    except:
        pass
    return False

def mark_attendance(student_name):
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')
    timeString = now.strftime('%H:%M:%S')

    check = supabase.table("Attendance") \
        .select("*") \
        .eq("Name", student_name) \
        .eq("Date", dateString) \
        .execute()

    if check.data:
        return False

    entry = {
        "Name": student_name,
        "Date": dateString,
        "Time": timeString,
        "Method": "Student App"
    }

    result = supabase.table("Attendance").insert(entry).execute()

    return True

def login_interface():
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("🔐 Student Login")

    name = st.text_input("Full name")
    email = st.text_input("Parent Gmail")

    if st.button("Login"):
        if name and email:
            resp = supabase.table("students_data") \
                .select("*") \
                .eq("Name", name) \
                .eq("Parent_Gmail", email) \
                .execute()

            if resp.data:
                st.session_state.logged_in = True
                st.session_state.student_name = name.upper()
                st.success(f"✅ Welcome {name}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        else:
            st.warning("Enter all fields")

    st.markdown("</div>", unsafe_allow_html=True)

def scan_interface():
    st.markdown('<div class="scan-card">', unsafe_allow_html=True)

    st.subheader(f"📱 Hello {st.session_state.student_name}")
    st.write("⚠️ If camera doesn't open, click the 🔒 lock icon in browser → Allow Camera")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.student_name = None
        st.rerun()

    session_id = st.text_input("Session ID:")

    img = st.camera_input("Scan QR Code")

    if img is not None and session_id:
        file = np.asarray(bytearray(img.getvalue()), dtype=np.uint8)
        frame = cv2.imdecode(file, 1)

        decoded = decode(frame)

        if not decoded:
            st.warning("❌ No QR detected! Try moving closer or increasing light.")
            return

        qr_data = decoded[0].data.decode("utf-8")

        if validate_session_qr(qr_data, session_id):
            if mark_attendance(st.session_state.student_name):
                st.success("✅ Attendance Marked!")
                st.balloons()
            else:
                st.error("Already marked today")
        else:
            st.error("Invalid or expired QR")

    st.markdown("</div>", unsafe_allow_html=True)

# Controller
if not st.session_state.logged_in:
    login_interface()
else:
    scan_interface()
