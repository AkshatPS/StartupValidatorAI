# Startalyze AI Agent (Flask Microservice)

This repository contains the AI-powered analysis agent for the Startalyze web application. It functions as a standalone microservice responsible for receiving startup idea data, performing a comprehensive analysis, and returning a structured report.

---

## Relation to the Main Project

This Flask service is a core backend component of the **Startalyze** MERN stack application. It is designed to be called by the main Node.js server to handle all computationally intensive analysis tasks. By isolating this functionality, the main application remains responsive while the AI agent processes validation requests asynchronously.

---

## API Endpoint

The primary endpoint for this service is used to trigger the idea analysis.

### `POST /analyze`

Accepts a startup idea and returns a comprehensive analysis report.

* **Request Body (JSON):**

    ```json
    {
      "title": "A subscription box for artisanal coffee",
      "description": "A monthly subscription service that delivers curated, single-origin coffee beans from around the world to customers' doors. Focuses on ethical sourcing and providing detailed tasting notes.",
      "industry": "E-commerce, Food & Beverage",
      "targetAudience": "Coffee enthusiasts, home baristas, people interested in ethical consumption."
    }
    ```

* **Success Response (JSON):**

    ```json
    {
      "executiveSummary": {
        "overallScore": 82,
        "recommendation": "High Potential. Recommended for further development.",
        "keyFindings": [
          "Strong market demand for specialty coffee.",
          "Subscription model provides recurring revenue.",
          "Low initial capital investment required."
        ]
      },
      "swotAnalysis": {
        "strengths": ["High-quality product", "Recurring revenue model"],
        "weaknesses": ["Logistics and shipping complexities"],
        "opportunities": ["Partnerships with coffee growers", "Community building"],
        "threats": ["High competition from established players"]
      },
      "nextSteps": [
        "Develop a prototype box and gather feedback.",
        "Research and establish relationships with coffee suppliers.",
        "Build a simple e-commerce website for pre-orders."
      ]
    }
    ```

---

## Tech Stack

* **Framework:** Flask
* **Production Server:** Gunicorn
* **Core Libraries:** `python-dotenv`, `requests`

---

## Local Setup and Installation

To run this service locally, you will need Python 3 installed.

### 1. Clone the Repository
```bash
git clone https://github.com/AkshatPS/StartupValidatorAI.git
cd StartupValidatorAI
```

### 2. Create and Activate Virtual Environment
```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
# .\venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate
```

### 3. Install Dependencies
Install all required packages from the requirements.txt file.
```bash
pip install -r requirements.txt
```

### 4. Create Environment File
Create a .env file in the root of this project. Add any necessary API keys or configuration variables here.
```bash
# .env
# Example: OPENAI_API_KEY=YOUR_API_KEY_HERE
```

### 5. Run the Development Server
Use the Flask CLI to run the local development server.
```bash
flask run
```
The service will now be running, typically at http://127.0.0.1:5000.

## Deployment
This service is deployed on Render as a Web Service. It is configured to run using the Gunicorn production server with the start command: gunicorn main:app.

