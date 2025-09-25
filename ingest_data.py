# ingest_data.py
from elasticsearch import Elasticsearch # type: ignore

try:
    es = Elasticsearch("http://localhost:9200")
    if not es.ping():
        raise ConnectionError("Could not connect to Elasticsearch.")

    index_name = "security-logs"

    sample_logs = [
        {"timestamp": "2025-09-22T10:00:00Z", "event_type": "login_attempt", "user": "admin", "status": "failed", "source_ip": "198.51.100.14"},
        {"timestamp": "2025-09-22T10:01:00Z", "event_type": "login_attempt", "user": "alice", "status": "success", "source_ip": "203.0.113.25"},
        {"timestamp": "2025-09-22T10:05:00Z", "event_type": "file_access", "user": "bob", "file": "/etc/shadow", "status": "denied"},
        {"timestamp": "2025-09-22T10:15:00Z", "event_type": "malware_detected", "user": "charlie", "signature": "Trojan.GenericKD.31422", "action": "quarantined"},
        {"timestamp": "2025-09-22T11:00:00Z", "event_type": "vpn_connect", "user": "alice", "source_ip": "203.0.113.25"},
        {"timestamp": "2025-09-22T12:30:00Z", "event_type": "login_attempt", "user": "admin", "status": "failed", "source_ip": "198.51.100.15"},
    ]

    if es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Deleting for a fresh start.")
        es.indices.delete(index=index_name)

    print(f"Creating index '{index_name}'.")
    es.indices.create(index=index_name)

    print("Ingesting sample logs...")
    for i, log in enumerate(sample_logs):
        es.index(index=index_name, id=i, document=log)

    print("✅ Data ingestion complete!")

except ConnectionError as e:
    print(f"Error: {e}")
    print("Please ensure your local Elasticsearch instance is running.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")