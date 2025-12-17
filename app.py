# app.py
import streamlit as st
from dotenv import load_dotenv
import os
import json
import pandas as pd
from elasticsearch import Elasticsearch
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain


load_dotenv()
st.set_page_config(page_title="Conversational SIEM", layout="centered")

try:
    es = Elasticsearch("http://localhost:9200")
    if not es.ping():
        st.error("Could not connect to Elasticsearch. Please ensure it's running locally.")
        st.stop()
except Exception as e:
    st.error(f"Could not connect to Elasticsearch. Please ensure it is running. Error: {e}")
    st.stop()

# This new prompt now includes a high-quality example for aggregations.
prompt_template = """
You are an expert Elasticsearch query generation assistant. Your ONLY job is to convert a user's question into a valid Elasticsearch DSL query in a JSON format.
DO NOT provide any conversational text or explanations. ONLY output the raw JSON query.

The user is querying an index named 'security-logs'.
The available fields are: 'timestamp', 'event_type', 'user', 'status', 'source_ip', 'signature', 'action'.

--- SEARCH EXAMPLE ---
User's Question: find failed logins from ip 198.51.100.14
Elasticsearch DSL Query:
{{
  "query": {{
    "bool": {{
      "must": [
        {{ "match": {{ "event_type": "login_attempt" }} }},
        {{ "match": {{ "status": "failed" }} }},
        {{ "match": {{ "source_ip": "198.51.100.14" }} }}
      ]
    }}
  }}
}}
--- END SEARCH EXAMPLE ---

--- AGGREGATION (COUNT) EXAMPLE ---
User's Question: count the number of events by status
Elasticsearch DSL Query:
{{
  "size": 0,
  "aggs": {{
    "counts_by_status": {{
      "terms": {{ "field": "status.keyword" }}
    }}
  }}
}}
--- END AGGREGATION EXAMPLE ---

User's Question:
{input}

Elasticsearch DSL Query:
"""

PROMPT = PromptTemplate(input_variables=["input"], template=prompt_template)

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
chain = LLMChain(llm=llm, prompt=PROMPT, verbose=True)

# --- 3. STREAMLIT UI ---
st.title("🗣️ Conversational SIEM Assistant")
st.markdown("Ask questions about your security logs, like _\"Show me all failed logins\"_ or _\"Count events by status\"_")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        # Check if content is a dataframe before rendering
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"], use_container_width=True)
        else:
            st.markdown(message["content"])

user_input = st.chat_input("Your question:")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🧠 Thinking..."):
            try:
                llm_response_str = chain.predict(input=user_input)

                if llm_response_str.strip().startswith("```json"):
                    llm_response_str = llm_response_str.strip()[7:-4]

                dsl_query = json.loads(llm_response_str)

                with st.expander("Generated Elasticsearch Query"):
                    st.json(dsl_query)

                result = es.search(index="security-logs", body=dsl_query)
                response_content = ""

                # --- NEW LOGIC TO HANDLE BOTH SEARCH AND AGGREGATION RESULTS ---
                if 'aggregations' in result:
                    # It's a count/summary query
                    agg_key = list(result['aggregations'].keys())[0]
                    buckets = result['aggregations'][agg_key]['buckets']
                    if buckets:
                        agg_data = [{"value": item['key'], "count": item['doc_count']} for item in buckets]
                        df = pd.DataFrame(agg_data)
                        st.dataframe(df, use_container_width=True)
                        response_content = df # Store dataframe for history
                    else:
                        response_content = "No results to aggregate."
                        st.write(response_content)
                elif 'hits' in result and result['hits']['hits']:
                    # It's a search query with results
                    data = [hit['_source'] for hit in result['hits']['hits']]
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                    response_content = df # Store dataframe for history
                else:
                    # It's a search query with no results
                    response_content = "I found no results matching your query."
                    st.write(response_content)

                st.session_state.chat_history.append({"role": "assistant", "content": response_content})

            except json.JSONDecodeError:
                error_msg = "The AI returned an invalid query. Please try rephrasing."
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"An error occurred: {e}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})


