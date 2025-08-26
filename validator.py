import os
import google.generativeai as genai
import requests
import json
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

# --- Configuration ---
load_dotenv()

# Load API Keys from .env
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SEARCH_API_KEY = os.getenv('SEARCH_API_KEY')
SEARCH_ENGINE_ID = os.getenv('SEARCH_ENGINE_ID')
MONGO_URI = os.getenv('ATLAS_URI') # Make sure your Node.js ATLAS_URI is in the .env file

# --- Flask App & DB Setup ---
app = Flask(__name__)
client = MongoClient(MONGO_URI)
db = client.get_database('test') # Or your specific DB name
ideas_collection = db.ideas

# Configure Generative AI Model
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print(f"Error configuring Generative AI: {e}")
    model = None

# --- Helper function to update MongoDB ---
def update_idea_status(idea_id, new_status, data=None):
    """Updates the status and optionally other data for an idea in MongoDB."""
    print(f"Updating ID {idea_id} to status: {new_status}")
    update_payload = {"$set": {"status": new_status}}
    if data:
        for key, value in data.items():
            update_payload["$set"][key] = value
    ideas_collection.update_one({"_id": idea_id}, update_payload)

# --- Analysis Functions ---
def search_competitors_online(query, api_key, cx):
    print(f"-> Searching for competitors with query: '{query}'...")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {'key': api_key, 'cx': cx, 'q': query, 'num': 5}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json()
        if 'items' not in search_results: return []
        return [{'title': item.get('title'), 'snippet': item.get('snippet')} for item in search_results.get('items', [])]
    except Exception as e:
        print(f"Error searching competitors: {e}")
        return []

def search_market_news(tags, api_key, cx):
    print(f"-> Searching for market news for tags: '{tags}'...")
    url = "https://www.googleapis.com/customsearch/v1"
    params = {'key': api_key, 'cx': cx, 'q': f"Latest market news and trends for {tags}", 'sort': 'date', 'num': 5}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        search_results = response.json()
        if 'items' not in search_results: return []
        return [{'title': item.get('title'), 'snippet': item.get('snippet')} for item in search_results.get('items', [])]
    except Exception as e:
        print(f"Error searching market news: {e}")
        return []

# --- Core Agentic AI Function ---
def generate_validation_report(idea_id, idea_data):
    if not model:
        return

    try:
        # Step 1: Market & Competitor Analysis
        update_idea_status(idea_id, 'analyzing_market')
        search_query = f"Competitors for '{idea_data['pitch']}' in {idea_data['tags']}"
        competitors = search_competitors_online(search_query, SEARCH_API_KEY, SEARCH_ENGINE_ID)
        time.sleep(5)

        update_idea_status(idea_id, 'analyzing_competitors')
        news = search_market_news(idea_data['tags'], SEARCH_API_KEY, SEARCH_ENGINE_ID)
        time.sleep(5)

        # Step 2: Feasibility Score Calculation
        update_idea_status(idea_id, 'calculating_score')
        time.sleep(5) # Simulate scoring

        # Step 3: Final Report Generation
        update_idea_status(idea_id, 'generating_summary')
        prompt = f"""
        You are a pragmatic and experienced startup advisor. Your job is to provide a balanced, realistic, and data-driven validation report.
        Avoid extreme optimism or pessimism. Your analysis must be directly tied to the competitor and market data provided.
        Your goal is to identify genuine potential and critical risks, offering a clear-eyed view of the startup's prospects.

        **Startup Idea Details:**
        - **Title:** {idea_data['title']}
        - **Pitch:** {idea_data['pitch']}
        - **Description:** {idea_data['description']}
        - **Tags:** {idea_data['tags']}

        **Collected Intelligence Data:**
        - **Competitor Data:** {json.dumps(competitors, indent=2)}
        - **Recent Market News:** {json.dumps(news, indent=2)}

        **Your Task: Generate a JSON object with the following structure. Use the scoring rubric to provide a fair score based *only* on the provided data.**

        **Scoring Rubric (Provide a realistic assessment):**
        - **1-20 (Significant Flaws):** Major, unaddressed issues in the core concept or market.
        - **21-40 (Needs Rework):** The idea has potential but requires a significant pivot or refinement to be viable.
        - **41-60 (Cautious Optimism):** A solid concept that faces notable, but likely surmountable, challenges.
        - **61-80 (Promising):** A strong idea with a clear value proposition and a favorable market position. Execution is the primary challenge.
        - **81-100 (Exceptional Potential):** A compelling, well-researched idea with clear differentiators and a strong market fit. Reserve this for truly outstanding cases.

        **JSON Output:**
        {{
          "executiveSummary": {{
            "overallScore": <score_out_of_100 based on a balanced view of the rubric>,
            "keyFindings": ["A balanced list of the most important findings, both positive and negative."],
            "recommendation": "<'Re-evaluate Core Concept', 'Proceed with Caution', 'Promising, Validate Further', or 'Strongly Consider Pursuing'>"
          }},
          "swotAnalysis": {{
            "strengths": ["List genuine strengths supported by the data."],
            "weaknesses": ["Identify key weaknesses and areas for improvement."],
            "opportunities": ["Highlight realistic market opportunities based on the news and competitor landscape."],
            "threats": ["List significant external threats like competitors, market shifts, etc."]
          }},
          "nextSteps": ["Provide concrete, actionable next steps for the founder to take."]
        }}
        """
        response = model.generate_content(prompt)
        # Clean up the response to be valid JSON
        report_text = response.text.strip().replace('```json', '').replace('```', '')
        report_json = json.loads(report_text)

        # Final Step: Complete the process
        update_idea_status(idea_id, 'completed', data={"analysisResult": report_json})

    except Exception as e:
        print(f"An error occurred during analysis for ID {idea_id}: {e}")
        update_idea_status(idea_id, 'error')


# --- Flask API Endpoint ---
@app.route('/analyze', methods=['POST'])
def analyze_idea():
    data = request.get_json()
    if not data or 'ideaId' not in data:
        return jsonify({"error": "Missing ideaId in request body"}), 400

    idea_id_str = data['ideaId']
    print(f"Received analysis request for Idea ID: {idea_id_str}")

    try:
        idea_id = ObjectId(idea_id_str)
        idea_document = ideas_collection.find_one({"_id": idea_id})

        if not idea_document:
            return jsonify({"error": f"No idea found with ID {idea_id_str}"}), 404

        # Run the time-consuming analysis in a separate thread
        # so we can return an immediate response to the Node.js server.
        from threading import Thread
        thread = Thread(target=generate_validation_report, args=(idea_id, idea_document))
        thread.start()

        return jsonify({"message": "Analysis started successfully."}), 202

    except Exception as e:
        print(f"An error occurred in /analyze endpoint: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == "__main__":
    # Use 0.0.0.0 to make it accessible from your Node.js container if using Docker
    app.run(host='0.0.0.0', port=5002, debug=True)
