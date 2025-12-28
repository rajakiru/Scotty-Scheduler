"""
Scotty Scheduler - CMU Course Recommender Frontend

This Streamlit application provides an interactive interface for students to:
- Input their interests and course preferences
- Upload resumes for automatic interest detection
- Receive AI-powered course recommendations
- Export recommended courses to calendar (.ics format)

Winner - Google Deepmind AI Agents Hackathon 2025 at CMU
"""

import streamlit as st
import requests
from datetime import datetime, timedelta
from uuid import uuid4
import json
import fitz  # PyMuPDF for PDF parsing
import re
import os

# Configuration - Support both Streamlit secrets and environment variables
try:
    # Try Streamlit secrets first (for Streamlit Cloud)
    API_ENDPOINT = st.secrets.get("API_ENDPOINT", "http://127.0.0.1:5000/query")
except (FileNotFoundError, KeyError):
    # Fall back to environment variable (for local/Docker)
    API_ENDPOINT = os.getenv("API_ENDPOINT", "http://127.0.0.1:5000/query")
DEFAULT_PAST_COURSES = [
    "15-319: Cloud Computing",
    "15-351: Algorithms",
    "15-213: Computer Systems"
]

# Page configuration
st.set_page_config(
    page_title="Scotty Scheduler - CMU Course Recommender",
    page_icon="📘",
    layout="wide"
)

st.title("📘 CMU Course Recommender")
st.write("AI-powered course suggestions based on your interests and preferences!")

# Sidebar for filters
with st.sidebar:
    st.header("🎯 Preferences")

    st.markdown("**Time Commitment**")
    hours_per_week = st.slider(
        "Weekly hours",
        min_value=1,
        max_value=20,
        value=(5, 10),
        help="Expected hours of work per week for the course"
    )

    st.markdown("**Course Quality**")
    course_rating = st.slider(
        "Minimum rating",
        min_value=1.0,
        max_value=5.0,
        value=(3.5, 5.0),
        step=0.1,
        help="Filter courses by student ratings"
    )

    st.divider()
    st.markdown("### About")
    st.info(
        "This AI-powered system searches through CMU course syllabi "
        "to find courses that match your interests and preferences."
    )

# Collect user input
auto_interests = ""
st.subheader("💬 Tell us about yourself")
interests = st.text_area("What topics are you interested in?", value=auto_interests)

past_courses = st.multiselect(
    "Courses you've already taken:",
    options=DEFAULT_PAST_COURSES
)

resume = st.file_uploader("📄 Upload your resume (PDF only)", type=['pdf'])

# Resume parsing for automatic interest detection
if resume:
    try:
        # Parse PDF resume and extract text
        doc = fitz.open(stream=resume.read(), filetype="pdf")
        full_text = "\n".join(page.get_text() for page in doc)

        # Extract technical interests using keyword matching
        # TODO: Enhance with NLP/entity extraction for better accuracy
        interest_keywords = (
            r"(cloud computing|machine learning|systems|AI|artificial intelligence|"
            r"networking|security|NLP|natural language processing|databases|"
            r"robotics|computer vision|data science|web development|"
            r"distributed systems|algorithms|cybersecurity)"
        )
        matches = re.findall(interest_keywords, full_text, re.IGNORECASE)
        unique_matches = set(match.lower() for match in matches)

        if unique_matches:
            auto_interests = ", ".join(sorted(unique_matches))
            st.success(f"📌 Interests detected from resume: {auto_interests}")
        else:
            st.info("No technical interests detected. Try describing them manually below.")

    except Exception as e:
        st.error(f"❌ Failed to parse resume: {str(e)}")

def create_ics(title, course_id, day, start, end, location, reason):
    """
    Generate an iCalendar (.ics) file for a course.

    Args:
        title: Course title
        course_id: Course ID (e.g., "18-709")
        day: Day of the week (e.g., "Monday")
        start: Start time in HH:MM format (e.g., "10:00")
        end: End time in HH:MM format (e.g., "11:20")
        location: Room/building location
        reason: Description/notes for the event

    Returns:
        String containing iCalendar format data
    """
    days = {
        "Monday": "MO",
        "Tuesday": "TU",
        "Wednesday": "WE",
        "Thursday": "TH",
        "Friday": "FR"
    }

    if day not in days:
        return "Invalid day"

    # Calculate next occurrence of the specified day
    today = datetime.today()
    diff = (list(days.keys()).index(day) - today.weekday() + 7) % 7
    event_date = today + timedelta(days=diff)

    # Parse start and end times
    start_dt = datetime.strptime(f"{event_date.date()} {start}", "%Y-%m-%d %H:%M")
    end_dt = datetime.strptime(f"{event_date.date()} {end}", "%Y-%m-%d %H:%M")
    uid = uuid4()

    # Generate iCalendar format with weekly recurrence for a semester (15 weeks)
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CMU Scotty Scheduler//EN
BEGIN:VEVENT
UID:{uid}@cmu.edu
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}
DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}
SUMMARY:{title} ({course_id})
LOCATION:{location}
DESCRIPTION:{reason}
RRULE:FREQ=WEEKLY;COUNT=15;BYDAY={days[day]}
END:VEVENT
END:VCALENDAR"""

def query_llm(interests, past_courses, hours, rating):
    """
    Query the LlamaIndex backend API for course recommendations.

    Args:
        interests: String describing user's academic/career interests
        past_courses: List of courses already completed
        hours: Tuple of (min_hours, max_hours) per week
        rating: Tuple of (min_rating, max_rating) on 1-5 scale

    Returns:
        String containing the API response (JSON format expected)
    """
    query = f"""I'm interested in {interests}.
I've already taken: {', '.join(past_courses) if past_courses else 'no courses yet'}.
I prefer courses that take {hours[0]}–{hours[1]} hours/week and have ratings between {rating[0]}–{rating[1]}.
Based on CMU's course catalog, what do you recommend?"""

    try:
        res = requests.post(API_ENDPOINT, json={"query": query}, timeout=30)
        res.raise_for_status()
        return res.json().get("response", "Sorry, no response received.")
    except requests.exceptions.ConnectionError:
        return "Error: Unable to connect to the backend. Make sure inference.py is running on port 5000."
    except requests.exceptions.Timeout:
        return "Error: Request timed out. The AI model might be taking longer than expected."
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

def extract_course_info_from_json(response_text):
    """
    Parse course information from JSON response.

    Args:
        response_text: String containing JSON data (may have markdown code blocks)

    Returns:
        List of course dictionaries, or empty list if parsing fails
    """
    try:
        # Remove markdown code block formatting if present
        cleaned = response_text.strip().strip("`").strip("json").strip()
        data = json.loads(cleaned)
        return data.get("courses", [])
    except json.JSONDecodeError:
        return []
    except Exception:
        return []


# Validation before querying
if not interests.strip():
    st.warning("⚠️ Please describe your interests to get personalized recommendations!")

# Button to trigger recommendation
if st.button("✨ Recommend Courses", type="primary", disabled=not interests.strip()):
    with st.spinner("🔍 Analyzing your profile and finding the best matches..."):
        response = query_llm(interests, past_courses, hours_per_week, course_rating)

        # Display response in a nice format
        st.divider()
        st.subheader("📚 Recommended Courses")

        # Check for errors first
        if response.startswith("Error:"):
            st.error(response)
        else:
            with st.chat_message("assistant"):
                st.markdown(response)

            # Extract course info (basic)
            courses = extract_course_info_from_json(response)
            if not courses:
                # Try fallback — extract quoted course name
                fallback_match = re.search(r'"([^"]+)"', response)
                if fallback_match:
                    course_title = fallback_match.group(1)
                    course_id = "Unknown-ID"
                    day = "Monday"
                    start = "10:00"
                    end = "11:20"
                    location = "TBD"
                    reason = "Suggested by advisor based on your resume and interests."

                    st.markdown(f"**{course_title}**")

                    ics_content = create_ics(
                        course_title, course_id, day, start, end, location, reason
                    )

                    st.download_button(
                        label=f"📅 Add to Calendar",
                        data=ics_content,
                        file_name=f"{course_title.replace(' ', '_')}.ics",
                        mime="text/calendar"
                    )
                else:
                    st.info("💡 Tip: The response above contains course suggestions, but calendar export isn't available for this format.")

# Add footer with information
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p><strong>Scotty Scheduler</strong> - Winner of Google Deepmind AI Agents Hackathon 2025 at CMU</p>
    <p>Powered by LlamaIndex & GPT-4o</p>
</div>
""", unsafe_allow_html=True)
