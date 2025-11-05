import streamlit as st
import cv2
import time
import numpy as np
from datetime import datetime
from pyzxing import BarCodeReader
from supabase_client import supabase

# Initialize reader
reader = BarCodeReader()

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

# Session
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_name" not in st.session_state:
    st.session_state.student_name = None

# ✅ FIX 1: Add debug logger
def notify_error(msg):
    st.error(msg)
    st.stop()

def validate_session_qr(qr_data, session_id):
    try:
        parts = qr_data.split(":")
        if parts[0] == "SESSION" and parts[1] == session_id:
            qr_timestamp = int(parts[3])
            return abs(int(time.time()) - qr_timestamp) <= 10
    except:
        pass
    return False

def mark_attendance(student_name):
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')
    timeString = now.strftime('%H:%M:%S')

    # ✅ FIX 2: Ensure matching field names
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

    # ✅ FIX 3: Capture response to detect failure
    result = supabase.table("Attendance").insert(entry).execute()

    if result.error:
        notify_error("Database insert failed, check table columns")

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

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.student_name = None
        st.rerun()

    session_id = st.text_input("Session ID:")

    img = st.camera_input("Scan QR Code")

    # ✅ FIX 4: Prevent constant reruns
    if img is not None and session_id:
        file = np.asarray(bytearray(img.getvalue()), dtype=np.uint8)
        frame = cv2.imdecode(file, 1)

        results = reader.decode_array(frame)

        if not results:
            st.warning("No QR detected!")
            return

        qr_data = results[0].get("parsed")

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
