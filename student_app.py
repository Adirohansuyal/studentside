import streamlit as st
import cv2
import time
import numpy as np
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime
from supabase_client import supabase
import pytz
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim

# Function to get user's timezone
def get_user_timezone():
    try:
        # Use system timezone
        import time
        return time.tzname[0]
    except:
        return "Asia/Kolkata"  # Default to IST

# OpenCV QR detector (works on Streamlit Cloud)
qr_detector = cv2.QRCodeDetector()

st.set_page_config(page_title="Student Portal", page_icon="🎓", layout="wide")

# Session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "student_name" not in st.session_state:
    st.session_state.student_name = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chatbot_visible" not in st.session_state:
    st.session_state.chatbot_visible = False

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
.login-card, .scan-card, .info-card {
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 10px;
    border: 1px solid #e9ecef;
    margin: 1rem 0;
    color: #333;
}
.info-card h4 {
    color: #495057;
    margin-bottom: 1rem;
}
.info-card p {
    color: #6c757d;
    line-height: 1.6;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <h1>🎓 Student Portal - FaceMark Pro</h1>
    <p>Your Personal Attendance Dashboard</p>
</div>
""", unsafe_allow_html=True)

def get_student_attendance_data(student_name):
    """Get attendance data for specific student"""
    try:
        response = supabase.table("Attendance").select("*").eq("Name", student_name.upper()).execute()
        return response.data
    except:
        return []

def calculate_student_percentage(student_name):
    """Calculate attendance percentage for specific student"""
    try:
        # Get all attendance records to find total classes
        all_attendance = supabase.table("Attendance").select("*").execute()
        if not all_attendance.data:
            return 0, 0, 0
        
        total_classes = len(pd.DataFrame(all_attendance.data)["Date"].unique())
        
        # Get student's attendance
        student_attendance = get_student_attendance_data(student_name)
        attended_classes = len(pd.DataFrame(student_attendance)["Date"].unique()) if student_attendance else 0
        
        percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0
        
        return attended_classes, total_classes, round(percentage, 2)
    except:
        return 0, 0, 0

def create_attendance_graph(student_name):
    """Create daily attendance line graph for student"""
    try:
        # Get all attendance dates
        all_attendance = supabase.table("Attendance").select("*").execute()
        if not all_attendance.data:
            return None
        
        all_dates = sorted(pd.DataFrame(all_attendance.data)["Date"].unique())
        
        # Get student's attendance
        student_records = get_student_attendance_data(student_name)
        student_dates = [record["Date"] for record in student_records]
        
        # Create daily attendance data
        attendance_data = []
        for date in all_dates:
            attendance_data.append({
                "Date": date,
                "Present": 1 if date in student_dates else 0
            })
        
        df = pd.DataFrame(attendance_data)
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Create line graph
        fig = px.line(df, x="Date", y="Present", 
                     title=f"Daily Attendance Pattern - {student_name}",
                     labels={"Present": "Attendance (1=Present, 0=Absent)", "Date": "Date"})
        
        fig.update_traces(mode='lines', line=dict(width=3, color='blue'))
        fig.update_layout(height=400, yaxis=dict(tickvals=[0, 1], ticktext=["Absent", "Present"]))
        
        return fig
    except:
        return None

def generate_student_insights(student_name):
    """Generate AI insights for specific student"""
    try:
        attended, total, percentage = calculate_student_percentage(student_name)
        
        # Simple rule-based insights (replace with actual AI API if available)
        if percentage >= 90:
            return f"Excellent attendance! You're attending {percentage}% of classes. Keep up the great work!"
        elif percentage >= 75:
            return f"Good attendance at {percentage}%. Try to maintain consistency to stay above 75%."
        else:
            return f"Attendance is {percentage}%, below the 75% requirement. Consider improving attendance to avoid academic issues."
            
    except:
        return "Unable to generate insights at this time."

    """Generate AI insights for specific student"""
    try:
        attended, total, percentage = calculate_student_percentage(student_name)
        
        prompt = f"""
        Analyze attendance for student {student_name}:
        - Attended: {attended} classes
        - Total: {total} classes  
        - Percentage: {percentage}%
        
        Provide personalized insights and recommendations in 2-3 sentences.
        """
        
        # Simple rule-based insights (replace with actual AI API if available)
        if percentage >= 90:
            return f"Excellent attendance! You're attending {percentage}% of classes. Keep up the great work!"
        elif percentage >= 75:
            return f"Good attendance at {percentage}%. Try to maintain consistency to stay above 75%."
        else:
            return f"Attendance is {percentage}%, below the 75% requirement. Consider improving attendance to avoid academic issues."
            
    except:
        return "Unable to generate insights at this time."

def student_chatbot_response(user_query, student_name):
    """Enhanced chatbot for comprehensive student queries"""
    query_lower = user_query.lower()
    
    # Personal information queries
    if "name" in query_lower or "who am i" in query_lower:
        return f"Your name is {student_name}. You are logged into the FaceMark Pro student portal."
    
    # Attendance queries
    elif "attendance" in query_lower or "percentage" in query_lower:
        attended, total, percentage = calculate_student_percentage(student_name)
        return f"Your attendance: {attended}/{total} classes ({percentage}%). {'✅ Above 75% requirement!' if percentage >= 75 else '⚠️ Below 75% requirement.'}"
    
    elif "records" in query_lower or "history" in query_lower:
        records = get_student_attendance_data(student_name)
        if records:
            recent = records[-1] if records else None
            return f"You have {len(records)} attendance records. Last marked: {recent['Date']} at {recent['Time']} via {recent['Method']}." if recent else f"You have {len(records)} attendance records."
        return "No attendance records found."
    
    # Status and performance queries
    elif "status" in query_lower or "performance" in query_lower:
        attended, total, percentage = calculate_student_percentage(student_name)
        if percentage >= 90:
            return f"Excellent performance! {percentage}% attendance. You're among the top performers."
        elif percentage >= 75:
            return f"Good performance! {percentage}% attendance. Keep maintaining this level."
        else:
            return f"Needs improvement! {percentage}% attendance. Focus on regular attendance to meet the 75% requirement."
    
    # Today's attendance
    elif "today" in query_lower:
        today = datetime.now().strftime("%Y-%m-%d")
        records = get_student_attendance_data(student_name)
        today_record = [r for r in records if r['Date'] == today]
        if today_record:
            return f"✅ Yes, you marked attendance today at {today_record[0]['Time']} via {today_record[0]['Method']}."
        return "❌ No, you haven't marked attendance today yet."
    
    # Help and capabilities
    elif "help" in query_lower or "what can you do" in query_lower:
        return "I can help with: your name, attendance percentage, attendance records, today's status, performance analysis, insights, and general questions about your attendance data."
    
    # Greetings
    elif any(word in query_lower for word in ["hello", "hi", "hey"]):
        return f"Hello {student_name}! How can I help you with your attendance today?"
    
    # Default response with suggestions
    else:
        return f"Hi {student_name}! I can help you with questions like: 'What is my name?', 'What's my attendance percentage?', 'Did I attend today?', 'Show my records', or 'How is my performance?'"


def validate_session_qr(qr_data, session_id):
    """SESSION:ClassID:TeacherID:Timestamp"""
    try:
        parts = qr_data.split(":")
        if parts[0] == "SESSION" and parts[1] == session_id:
            timestamp = int(parts[3])
            return abs(int(time.time()) - timestamp) <= 10
    except:
        pass
    return False


def mark_attendance(student_name):
    """Insert new attendance if not exists - using local timezone"""
    # Use local timezone directly
    now = datetime.now()
    dateString = now.strftime('%Y-%m-%d')
    timeString = now.strftime('%H:%M:%S')
    
    # Debug: Show what date is being used
    st.write(f"Debug: Current date being used: {dateString}")
    st.write(f"Debug: Current time being used: {timeString}")
    st.write(f"Debug: Raw datetime object: {now}")

    # Check if attendance for this student is already marked today in Supabase
    try:
        response = supabase.table("Attendance").select("*").eq("Name", student_name.upper()).eq("Date", dateString).execute()
        if response.data:
            return False  # Already marked today
        
        # Insert new attendance record
        entry = {
            "Name": student_name.upper(),
            "Date": dateString,
            "Time": timeString,
            "Method": "Student App"
        }
        
        supabase.table("Attendance").insert(entry).execute()
        return True
        
    except Exception as e:
        st.error(f"Error marking attendance: {e}")
        return False


def login_interface():
    st.subheader("🔐 Student Login")

    name = st.text_input("Full Name")
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
                st.success(f"✅ Welcome, {name}!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        else:
            st.warning("⚠️ Fill all fields")


def scan_interface():
    col1, col2 = st.columns([2, 1])
    
    with col2:
        if st.button("Logout", type="secondary"):
            st.session_state.logged_in = False
            st.session_state.student_name = None
            st.rerun()
    
    st.markdown(f"### 👋 Welcome, {st.session_state.student_name}")
    
    # Main screen navigation using tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📱 Mark Attendance", 
        "📈 My Attendance", 
        "📋 My Records", 
        "🎯 My Insights",
        "💬 Chatbot"
    ])
    
    with tab1:
        st.subheader("📱 Mark Your Attendance")
        
        session_id = st.text_input("Session ID (ask teacher):")
        img = st.camera_input("Point camera at QR Code")
        
        if img is not None and session_id:
            file_bytes = np.asarray(bytearray(img.getvalue()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, 1)
            qr_text, bbox, _ = qr_detector.detectAndDecode(frame)
            
            if not qr_text:
                st.warning("❌ No QR detected!")
                return
            
            if validate_session_qr(qr_text, session_id):
                if mark_attendance(st.session_state.student_name):
                    st.success("✅ Attendance Marked Successfully!")
                    st.balloons()
                else:
                    st.warning("⚠️ Already marked today!")
            else:
                st.error("❌ Invalid or Expired QR")
    
    with tab2:
        attended, total, percentage = calculate_student_percentage(st.session_state.student_name)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{attended}</h3>
                <p>Classes Attended</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{total}</h3>
                <p>Total Classes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            color = "green" if percentage >= 75 else "red"
            st.markdown(f"""
            <div class="metric-card" style="background: {color};">
                <h3>{percentage}%</h3>
                <p>Attendance Rate</p>
            </div>
            """, unsafe_allow_html=True)
        
        if percentage >= 75:
            st.success(f"✅ Great! Your attendance is {percentage}% (Above required 75%)")
        else:
            st.error(f"⚠️ Warning: Your attendance is {percentage}% (Below required 75%)")
    
    with tab3:
        st.subheader("📋 Your Attendance Records")
        records = get_student_attendance_data(st.session_state.student_name)
        
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df[['Date', 'Time', 'Method']], use_container_width=True)
        else:
            st.info("No attendance records found.")
    
    with tab4:
        st.subheader("🎯 AI Attendance Insights")
        insights = generate_student_insights(st.session_state.student_name)
        
        st.markdown(f"""
        <div class="info-card">
            <h4>📊 Your Attendance Analysis</h4>
            <p>{insights}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Add attendance graph
        st.subheader("📈 Daily Attendance Pattern")
        graph = create_attendance_graph(st.session_state.student_name)
        if graph:
            st.plotly_chart(graph, use_container_width=True)
        else:
            st.info("No attendance data available for graph.")
    
    with tab5:
        st.subheader("💬 Attendance Assistant")
        
        st.markdown("""
        <div class="info-card">
            <h4>🤖 Ask me about your attendance!</h4>
            <p>I can help with attendance percentage, records, and insights.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if user_input := st.chat_input("Ask about your attendance..."):
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                response = student_chatbot_response(user_input, st.session_state.student_name)
                st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})



# Main Controller
if not st.session_state.logged_in:
    login_interface()
else:
    scan_interface()
