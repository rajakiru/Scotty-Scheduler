# Scotty Scheduler

**Winner - Google Deepmind AI Agents Hackathon 2025 at CMU**

An intelligent course recommendation system that helps CMU students find the perfect courses based on their interests, past experience, and preferences. Powered by AI agents using LlamaIndex and GPT-4o.

## Features

- **AI-Powered Recommendations**: Uses GPT-4o through LlamaIndex to provide personalized course suggestions
- **Resume Analysis**: Upload your resume to automatically detect your interests and skills
- **Flexible Filtering**: Filter courses by weekly hours commitment and course ratings
- **Calendar Integration**: Export recommended courses directly to your calendar (.ics format)
- **Rich Course Database**: Comprehensive syllabus data from CMU ECE courses (Fall 2024 & Spring 2025)

## Architecture

The system consists of three main components:

1. **Frontend (Streamlit)** - `home.py`
   - Interactive web interface for user inputs and preferences
   - Resume upload and parsing with PyMuPDF
   - Course recommendation display and calendar export

2. **Backend API (Flask)** - `inference.py`
   - RESTful API endpoint for course queries
   - LlamaIndex integration for RAG (Retrieval-Augmented Generation)
   - Vector search over course syllabi using HuggingFace embeddings

3. **Data Collection** - `syllabus_scraper.py`
   - Automated web scraper for CMU Canvas syllabi
   - Selenium-based PDF downloader

## Technology Stack

- **AI/ML**: LlamaIndex, OpenAI GPT-4o, HuggingFace Embeddings
- **Frontend**: Streamlit
- **Backend**: Flask
- **PDF Processing**: PyMuPDF (fitz)
- **Web Scraping**: Selenium
- **Data Processing**: Pandas

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (or CMU LiteLLM access)
- Chrome/Chromium browser (for syllabus scraper)

### Quick Setup (Automated)

For an automated setup, use the provided setup script:

```bash
git clone https://github.com/PRITH-S07/Scotty-Scheduler.git
cd Scotty-Scheduler
chmod +x setup.sh
./setup.sh
```

Then edit `.env` to add your API key:
```bash
nano .env  # or use your preferred editor
```

### Manual Installation

1. **Clone the repository**
```bash
git clone https://github.com/PRITH-S07/Scotty-Scheduler.git
cd Scotty-Scheduler
```

2. **Create a virtual environment (recommended)**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

5. **Extract data files**
```bash
# Extract the pre-processed vector index
unzip stored_index.zip

# Optional: Extract syllabus PDFs for data exploration
unzip syllabi_pdfs_fall2024ECE.zip
unzip syllabi_pdfs_spring2025ECE.zip
```

### Running the Application

#### Option 1: Quick Start (with tmux)

```bash
./run.sh
```
This automatically starts both the backend and frontend in a split-pane tmux session.

#### Option 2: Manual Start

The application requires two processes running simultaneously:

**Terminal 1 - Start the Flask backend**
```bash
source venv/bin/activate  # If not already activated
python inference.py
```
This starts the API server on `http://localhost:5000`

**Terminal 2 - Start the Streamlit frontend**
```bash
source venv/bin/activate  # If not already activated
streamlit run home.py
```
This opens the web interface (usually at `http://localhost:8501`)

## Usage Guide

1. **Set Your Preferences**
   - Use the sidebar to set your desired weekly hours commitment
   - Adjust the minimum course rating filter

2. **Provide Your Information**
   - Describe your interests in the text area
   - Select courses you've already taken
   - Optionally upload your resume (PDF) for automatic interest detection

3. **Get Recommendations**
   - Click "Recommend Courses" button
   - Review the AI-generated course suggestions
   - Download calendar events for recommended courses

## Project Structure

```
Scotty-Scheduler/
├── home.py                    # Streamlit frontend
├── inference.py               # Flask API backend
├── syllabus_scraper.py        # Canvas syllabus scraper
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variables template
├── render.yaml                # Render.com deployment config
├── packages.txt               # System dependencies for Streamlit Cloud
├── setup.sh                   # Automated setup script
├── run.sh                     # Quick start script
├── data/                      # Raw course data (CSV/Excel)
├── cleaned_data/              # Processed syllabus text files
├── index_data/                # LlamaIndex vector store (18MB)
└── .streamlit/                # Streamlit configuration
```

## Data Resources

- `syllabi_pdfs_fall2024ECE.zip`: Fall 2024 ECE course syllabi (40MB)
- `syllabi_pdfs_spring2025ECE.zip`: Spring 2025 ECE course syllabi (93MB)
- `stored_index.zip`: Pre-built vector index for fast queries (7MB)
- `cleaned_data/`: Extracted text from syllabus PDFs for indexing

## Extending the System

### Collecting New Syllabi

To scrape additional course syllabi from CMU Canvas:

1. Update the `COURSE_URL` in `syllabus_scraper.py` to target different courses/semesters
2. Run the scraper:
```bash
python syllabus_scraper.py
```
3. Follow the prompts to log in to Canvas
4. PDFs will be downloaded to the configured directory

### Rebuilding the Vector Index

After adding new syllabi, you'll need to rebuild the vector index:

1. Place cleaned syllabus text files in `cleaned_data/`
2. Run the index builder (see `Starter_inference_script.ipynb` for the process)
3. The new index will be saved to `index_data/`
4. Restart the backend to use the updated index

**Note:** The index uses HuggingFace's `all-MiniLM-L6-v2` embedding model to convert course syllabi into 384-dimensional semantic vectors for fast similarity search.

## Deployment

This app can be deployed to:
- **Backend**: Render.com, Railway, AWS, or any Python hosting
- **Frontend**: Streamlit Cloud (free tier available)

See `render.yaml` for Render.com configuration.

## API Reference

### POST /query

Query the course recommendation system.

**Request:**
```json
{
  "query": "I'm interested in machine learning and cloud computing. I prefer courses with 5-10 hours/week commitment and ratings above 4.0."
}
```

**Response:**
```json
{
  "response": "{\"courses\": [{\"id\": \"18-709\", \"title\": \"Advanced Cloud Computing\", ...}]}"
}
```

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Google Deepmind for sponsoring the AI Agents Hackathon
- Carnegie Mellon University
- LlamaIndex team for the excellent RAG framework
- OpenAI for GPT-4o access through CMU LiteLLM

## Contact

For questions or feedback about this project, please open an issue on GitHub.
