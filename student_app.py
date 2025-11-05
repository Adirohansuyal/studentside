import streamlit as st
import cv2
import time
import numpy as np
from datetime import datetime
from pyzbar.pyzbar import decode
from supabase_client import supabase

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

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_name" not in st.session_state:
    st.session_state.student_name = None

def validate_session_qr(qr_data):
    """Validate any session QR code"""
    try:
        parts = qr_data.split(":")
        if len(parts) >= 4 and parts[0] == "SESSION":
            qr_timestamp = int(parts[3])
            current_time = int(time.time())
            return abs(current_time - qr_timestamp) <= 8
    except:
        pass
    return False

def mark_attendance(student_name):
    """Mark attendance in database"""
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')
    timeString = now.strftime('%H:%M:%S')
    
    # Check if already marked
    response = supabase.table("Attendance").select("*").eq("Name", student_name).eq("Date", dateString).execute()
    if response.data:
        return False
    
    new_entry = {
        "Name": student_name,
        "Date": dateString,
        "Time": timeString,
        "Method": "Student App"
    }
    supabase.table("Attendance").insert(new_entry).execute()
    return True

def login_interface():
    """Student login interface"""
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.subheader("🔐 Student Login")
    
    name = st.text_input("Enter your full name:", key="login_name")
    email = st.text_input("Enter parent's Gmail:", key="login_email")
    
    if st.button("Login", key="login_btn"):
        if name and email:
            response = supabase.table("students_data").select("*").eq("Name", name).eq("Parent_Gmail", email).execute()
            
            if response.data:
                st.session_state.logged_in = True
                st.session_state.student_name = name.upper()
                st.success(f"✅ Welcome, {name}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Check your name and parent's email.")
        else:
            st.warning("⚠️ Please fill in both fields")
    
    st.markdown('</div>', unsafe_allow_html=True)

def scan_interface():
    """QR scanning interface"""
    st.markdown('<div class="scan-card">', unsafe_allow_html=True)
    st.subheader(f"📱 Welcome, {st.session_state.student_name}")
    
    if st.button("Logout", key="logout_btn"):
        st.session_state.logged_in = False
        st.session_state.student_name = None
        st.rerun()
    
    st.write("Scan any classroom QR code for attendance:")
    
    if st.button("Start QR Scanner", key="start_scan"):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("❌ Could not access camera")
            return
        
        st.write("📷 Point camera at QR code...")
        image_placeholder = st.empty()
        stop_button = st.button("Stop Scanner", key="stop_scan")
        
        while True:
            success, frame = cap.read()
            if not success:
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image_placeholder.image(frame_rgb, channels="RGB")
            
            # Decode QR codes
            decoded_objects = decode(frame)
            for obj in decoded_objects:
                qr_data = obj.data.decode("utf-8")
                
                if validate_session_qr(qr_data):
                    cap.release()
                    cv2.destroyAllWindows()
                    
                    # Mark attendance automatically
                    if mark_attendance(st.session_state.student_name):
                        st.success(f"✅ Attendance marked for {st.session_state.student_name}!")
                        st.balloons()
                    else:
                        st.error("❌ Attendance already marked today")
                    return
                else:
                    st.error("❌ Invalid or expired QR code")
            
            if stop_button:
                break
        
        cap.release()
        cv2.destroyAllWindows()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Main controller
if not st.session_state.logged_in:
    login_interface()
else:
    scan_interface()
