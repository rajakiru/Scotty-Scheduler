"""
Scotty Scheduler - Backend API Server

Flask-based API server that provides course recommendations using:
- LlamaIndex for retrieval-augmented generation (RAG)
- GPT-4o for intelligent course matching
- HuggingFace embeddings for vector search
- Pre-indexed CMU course syllabi database

Winner - Google Deepmind AI Agents Hackathon 2025 at CMU
"""

from flask import Flask, request, jsonify
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.settings import Settings
from dotenv import load_dotenv
import os
import sys

# Configuration
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://cmu.litellm.ai/v1")
INDEX_DIR = os.getenv("INDEX_DIR", "./index_data")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384-dimensional embeddings

# Validate required environment variables
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY not found in environment variables.")
    print("Please create a .env file with your API key.")
    print("See .env.example for reference.")
    sys.exit(1)

print("Initializing Scotty Scheduler backend...")

# Initialize LLM for final answer generation
try:
    llm = OpenAI(
        model="gpt-4o",
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_API_BASE
    )
    Settings.llm = llm
    print("✓ LLM initialized successfully")
except Exception as e:
    print(f"ERROR: Failed to initialize LLM: {e}")
    sys.exit(1)

# Initialize embedding model for vector search
try:
    embed_model = HuggingFaceEmbedding(model_name=EMBEDDING_MODEL)
    print(f"✓ Embedding model loaded: {EMBEDDING_MODEL}")
except Exception as e:
    print(f"ERROR: Failed to load embedding model: {e}")
    sys.exit(1)

# Load pre-built vector index from disk
try:
    if not os.path.exists(INDEX_DIR):
        print(f"ERROR: Index directory not found: {INDEX_DIR}")
        print("Please extract stored_index.zip to create the index_data directory.")
        sys.exit(1)

    storage_context = StorageContext.from_defaults(persist_dir=INDEX_DIR)
    index = load_index_from_storage(storage_context, embed_model=embed_model)
    print(f"✓ Vector index loaded from {INDEX_DIR}")
except Exception as e:
    print(f"ERROR: Failed to load vector index: {e}")
    sys.exit(1)

# Initialize Flask application
app = Flask(__name__)
print("✓ Flask app initialized\n")

@app.route('/query', methods=['POST'])
def query_index():
    """
    Handle POST requests for course recommendations.

    Expected JSON payload:
    {
        "query": "I'm interested in... I've taken... I prefer..."
    }

    Returns JSON:
    {
        "response": "{\"courses\": [...]}"
    }
    """
    # Validate index is loaded
    if index is None:
        return jsonify({"error": "Vector index not loaded"}), 500

    # Parse request data
    data = request.json
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field in request"}), 400

    query_text = data.get("query")
    print(f"\n🟡 Received query: {query_text}\n")

    try:
        # Configure query engine with RAG parameters
        query_engine = index.as_query_engine(
            llm=llm,
            response_mode="compact",
            system_prompt=(
                "You are an academic advisor at CMU. Given the student’s interest, past courses, and preferences "
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
                "    },\n"
                "    ...\n"
                "  ]\n"
                "}\n\n"
                "Respond with ONLY this JSON object — no explanation, no commentary."
            )
        )

        # Execute query against the indexed syllabi
        response = query_engine.query(query_text)
        print(f"\n🟢 Response generated: {response}\n")

        return jsonify({"response": str(response.response)})

    except Exception as e:
        # Log detailed error for debugging
        import traceback
        print("\n❌ Error processing query:")
        traceback.print_exc()
        return jsonify({
            "error": "Failed to process query",
            "details": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify the API is running."""
    return jsonify({
        "status": "healthy",
        "index_loaded": index is not None,
        "model": "gpt-4o"
    }), 200

if __name__ == "__main__":
    # Render provides PORT env variable, fallback to FLASK_PORT or 5000
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", 5000)))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    print("=" * 60)
    print("Scotty Scheduler API Server")
    print("=" * 60)
    print(f"Server running on: http://0.0.0.0:{port}")
    print(f"Debug mode: {debug}")
    print(f"Endpoints:")
    print(f"  POST /query  - Get course recommendations")
    print(f"  GET  /health - Health check")
    print("=" * 60)
    print("\nPress CTRL+C to stop the server\n")

    app.run(port=port, debug=debug, host='0.0.0.0')