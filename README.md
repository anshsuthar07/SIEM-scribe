# Conversational SIEM Assistant

A **Flask-based AI-powered Conversational SIEM Assistant** that enables security analysts to query Elasticsearch SIEM logs using **natural language** instead of complex query languages.

---

## 🔍 Problem Overview

Security analysts often spend significant time writing and refining complex SIEM queries to investigate threats.  
This slows down incident response, increases human error, and creates a steep learning curve for junior analysts.

This project solves that problem by introducing a **conversational interface** that translates natural language questions into **Elasticsearch queries using Generative AI**.

---

## 🚀 Key Features

### 🗣️ Natural Language SIEM Queries
- Ask security questions in plain English
- No need to learn Elasticsearch DSL

**Example Queries:**
- "Count failed login attempts by user"
- "Show top IP addresses with denied connections"
- "List recent failed authentication events"

---

### 🤖 AI-Driven Query Generation
- Uses **Google Gemini** with **LangChain**
- Converts user questions into valid **Elasticsearch DSL**
- Reduces manual query writing errors

---

### 🔌 Elasticsearch Integration
- Queries are executed on the `security-logs` index
- Returns structured, readable results

---

## 🧠 How It Works

1. User enters a security-related question in plain English  
2. Flask backend receives the request  
3. LangChain + Gemini convert the question into an Elasticsearch DSL query  
4. The query is executed on Elasticsearch  
5. Results are returned and displayed in the UI  

---

## 🏗️ Tech Stack

- **Frontend:** HTML5, CSS3, JavaScript  
- **Backend:** Python, Flask  
- **AI / NLP:** LangChain, Google Gemini  
- **Database (SIEM):** Elasticsearch  
- **Utilities:** Pandas, python-dotenv, Git, GitHub, VS Code  

---

## 📁 Project Structure

```text
demo/
│
├── web.py                 # Flask application
├── app.py                 # Streamlit prototype (optional)
├── requirements.txt       # Python dependencies
├── .gitignore
│
├── templates/
│   └── index.html         # Frontend UI
│
├── static/
│   └── style.css          # UI styling
│
├── screenshots/           # Application screenshots
│
├── venv/                  # Virtual environment (not committed)
└── .env                   # Environment variables (not committed)
```
---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository
```bash
git clone <your-repo-url>
cd demo
```

### 2️⃣ Create & Activate Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```
### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
### 4️⃣ Configure Environment Variables
Create a .env file in the root directory:
```bash
GOOGLE_API_KEY=your_gemini_api_key
```
## ▶️ Running the Application
### 1️⃣ Open Command Prompt and navigate to your Elasticsearch installation directory, then run:
```bash
.\bin\elasticsearch.bat
```
### 2️⃣ Ensure Elasticsearch is Running
```bash
http://localhost:9200
```
### 3️⃣ Start the Flask Server
```bash
python web.py
```
### 4️⃣ Open in Browser
```bash
http://localhost:5000
```






 


