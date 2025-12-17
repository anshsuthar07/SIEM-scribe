from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# Initialize Elasticsearch client
try:
    es = Elasticsearch("http://localhost:9200")
    assert es.ping(), "Elasticsearch is not reachable"
except Exception as e:
    es = None
    print(f"[WARN] Elasticsearch init failed: {e}")

# (Your prompt_template remains the same)
prompt_template = """
You are an expert data analysis assistant. Your job is to convert a user's question into a single, clean JSON object with two parts:
1. "dsl_query": A valid Elasticsearch DSL query to fetch data from the 'security-logs' index.
2. "visualization": An object specifying how to display the data.

The visualization "type" must be one of: 'table', 'bar', 'line', 'pie'.
- If the user asks for a "graph", "chart", "plot", or "visualize", choose 'bar' or 'line'.
- If the user asks to "show", "list", "count", or "find", usually choose 'table'.
- For aggregations, the "title" should summarize the chart (e.g., "Event Counts by Type").

--- TABLE EXAMPLE ---
User's Question: count failed login attempts by user
Your JSON Output:
{{
  "dsl_query": {{
    "size": 0,
    "aggs": {{
      "group_by_user": {{
        "filter": {{ "bool": {{ "must": [{{ "match": {{ "status": "failed" }} }}] }} }},
        "aggs": {{
          "users": {{
            "terms": {{ "field": "user.keyword" }}
          }}
        }}
      }}
    }}
  }},
  "visualization": {{
    "type": "table",
    "title": "Failed Logins by User"
  }}
}}
--- END TABLE EXAMPLE ---

--- BAR CHART EXAMPLE ---
User's Question: create a bar chart of events by type
Your JSON Output:
{{
  "dsl_query": {{
    "size": 0,
    "aggs": {{
      "events_by_type": {{
        "terms": {{ "field": "event_type.keyword" }}
      }}
    }}
  }},
  "visualization": {{
    "type": "bar",
    "title": "Event Counts by Type"
  }}
}}
--- END BAR CHART EXAMPLE ---

User's Question:
{input}

Your JSON Output:
"""

PROMPT = PromptTemplate(input_variables=["input"], template=prompt_template)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0) # Using 1.5-flash as it's often better
chain = PROMPT | llm | StrOutputParser()


@app.get("/")
def index():
    return render_template("index.html")

# --- ✨ NEW HELPER FUNCTION ✨ ---
# This function will reliably find the 'buckets' list inside an aggregation result.
def find_buckets(agg_result):
    if not isinstance(agg_result, dict):
        return None
    if 'buckets' in agg_result and isinstance(agg_result['buckets'], list):
        return agg_result['buckets']
    for value in agg_result.values():
        found = find_buckets(value)
        if found is not None:
            return found
    return None
# --- END OF HELPER FUNCTION ---


@app.post("/query")
def query():
    try:
        if es is None:
            return jsonify({"type": "text", "message": "Elasticsearch is not available."}), 500

        data = request.get_json(force=True) or {}
        question = (data.get("question") or "").strip()
        if not question:
            return jsonify({"type": "text", "message": "Please provide a question."}), 400

        llm_response_str = chain.invoke({"input": question})
        
        if llm_response_str.strip().startswith("```json"):
            llm_response_str = llm_response_str.strip()[7:-4]
        elif llm_response_str.strip().startswith("```"):
             llm_response_str = llm_response_str.strip()[3:-3]

        llm_response_json = json.loads(llm_response_str)
        dsl_query = llm_response_json.get("dsl_query", {})
        viz_info = llm_response_json.get("visualization", {"type": "table"})
        
        result = es.search(index="security-logs", body=dsl_query)

        # --- 👇 UPDATED AGGREGATION LOGIC 👇 ---
        if 'aggregations' in result:
            # Use the new helper function to find the buckets reliably
            buckets = find_buckets(result['aggregations']) or [] # Default to empty list if None

            if viz_info.get("type") in ["bar", "line", "pie"] and buckets:
                labels = [b.get('key') for b in buckets]
                data_points = [b.get('doc_count') for b in buckets]
                
                chart_data = {
                    "type": viz_info["type"],
                    "title": viz_info.get("title", "Chart"),
                    "labels": labels,
                    "data": data_points
                }
                return jsonify({"type": "chart", "chart_data": chart_data})
            
            # Default to table for aggregations if not a chart or if no buckets found
            else:
                rows = [{"value": b.get('key'), "count": b.get('doc_count')} for b in buckets]
                return jsonify({
                    "type": "table",
                    "columns": ["value", "count"],
                    "rows": rows
                })
        # --- END OF UPDATED LOGIC ---

        hits = result.get('hits', {}).get('hits', [])
        if hits:
            sources = [h.get('_source', {}) for h in hits]
            columns = sorted({k for s in sources for k in s.keys()})
            return jsonify({
                "type": "table",
                "columns": columns,
                "rows": sources
            })

        return jsonify({"type": "text", "message": "I found no results matching your query."})

    except json.JSONDecodeError:
        return jsonify({"type": "text", "message": "The AI returned an invalid query. Try rephrasing."}), 400
    except Exception as e:
        # Return the actual error to the frontend for easier debugging
        return jsonify({"type": "text", "message": f"An error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)