"""
Scotty Scheduler - CMU Course Recommender

All-in-one Streamlit application with integrated LlamaIndex backend.
No separate Flask server needed!

Winner - Google Deepmind AI Agents Hackathon 2025 at CMU
"""

import streamlit as st
import os
from datetime import datetime, timedelta
from uuid import uuid4
import json
import fitz  # PyMuPDF for PDF parsing
import re

# LlamaIndex imports
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings

# Page configuration
st.set_page_config(
    page_title="Scotty Scheduler - CMU Course Recommender",
    page_icon="📘",
    layout="wide"
)

# Configuration
DEFAULT_PAST_COURSES = [
    "15-319: Cloud Computing",
    "15-351: Algorithms",
    "15-213: Computer Systems"
]

# Get API key from Streamlit secrets or environment
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    OPENAI_API_BASE = st.secrets.get("OPENAI_API_BASE", "https://api.openai.com/v1")
except (FileNotFoundError, KeyError):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

if not OPENAI_API_KEY:
    st.error("⚠️ OPENAI_API_KEY not found! Please add it to Streamlit secrets.")
    st.stop()


@st.cache_resource(show_spinner="Loading AI models and course database...")
def load_llama_index():
    """
    Load the LlamaIndex system with vector store and LLM.
    This is cached so it only loads once when the app starts.
    """
    try:
        # Initialize LLM
        llm = OpenAI(
            model="gpt-4o",
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        Settings.llm = llm

        # Initialize embedding model
        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Load vector index
        INDEX_DIR = "./index_data"
        if not os.path.exists(INDEX_DIR):
            st.error(f"❌ Index directory not found: {INDEX_DIR}")
            st.info("Make sure the index_data/ folder is in your repository.")
            st.stop()

        storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
        index = load_index_from_storage(storage_context, embed_model=embed_model)

        return index, llm

    except Exception as e:
        st.error(f"❌ Error loading AI system: {str(e)}")
        st.stop()


def query_courses(query_text, index, llm):
    """
    Query the course database using LlamaIndex.

    Args:
        query_text: User's query about courses
        index: LlamaIndex vector store
        llm: Language model

    Returns:
        Response from the AI system
    """
    try:
        query_engine = index.as_query_engine(
            llm=llm,
            response_mode="compact",
            system_prompt=(
                "You are an academic advisor at CMU. Given the student's interest, past courses, and preferences "
                "(e.g., time commitment and rating), recommend 1–2 specific CMU courses. "
                "Return ONLY a valid JSON object with this format:\n\n"
                "{\n"
                "  \"courses\": [\n"
                "    {\n"
                "      \"id\": \"18-709\",\n"
                "      \"title\": \"Advanced Cloud Computing\",\n"
                "      \"description\": \"Project-based course on scalable distributed systems.\",\n"
                "      \"day\": \"Monday\",\n"
                "      \"start_time\": \"16:00\",\n"
                "      \"end_time\": \"17:50\",\n"
                "      \"location\": \"DH 2315\"\n"
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Respond with ONLY this JSON object — no explanation, no commentary."
            )
        )

        response = query_engine.query(query_text)
        return str(response.response)

    except Exception as e:
        return f"Error generating recommendations: {str(e)}"


def create_ics(title, course_id, day, start, end, location, reason):
    """
    Generate an iCalendar (.ics) file for a course.
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


def extract_course_info_from_json(response_text):
    """
    Parse course information from JSON response.
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


# ========== MAIN APP ==========

st.title("📘 CMU Course Recommender")
st.write("AI-powered course suggestions based on your interests and preferences!")

# Load the LlamaIndex system (cached, only loads once)
index, llm = load_llama_index()

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

# Validation before querying
if not interests.strip():
    st.warning("⚠️ Please describe your interests to get personalized recommendations!")

# Button to trigger recommendation
if st.button("✨ Recommend Courses", type="primary", disabled=not interests.strip()):
    with st.spinner("🔍 Analyzing your profile and finding the best matches..."):
        # Build query
        query = f"""I'm interested in {interests}.
I've already taken: {', '.join(past_courses) if past_courses else 'no courses yet'}.
I prefer courses that take {hours_per_week[0]}–{hours_per_week[1]} hours/week and have ratings between {course_rating[0]}–{course_rating[1]}.
Based on CMU's course catalog, what do you recommend?"""

        # Query the AI system
        response = query_courses(query, index, llm)

        # Display response in a nice format
        st.divider()
        st.subheader("📚 Recommended Courses")

        # Check for errors first
        if response.startswith("Error"):
            st.error(response)
        else:
            with st.chat_message("assistant"):
                st.markdown(response)

            # Extract course info for calendar export
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
