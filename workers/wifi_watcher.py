from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pprint
from dotenv import load_dotenv
import os
from jetracer_worker.workers.wifi_scanner import connect_to_wifi

load_dotenv(".env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")

# Cache to store last known credentials
last_ssid = None
last_password = None

def on_change(change):
    global last_ssid, last_password

    print("\n--- Change Detected ---")
    pprint.pprint(change)

    # Only act on updates to document with _id == "robot"
    doc_id = change.get("documentKey", {}).get("_id")
    if doc_id != DOCUMENT_ID:
        print(f"⚠️ Ignored update to document _id: {doc_id}")
        return

    if change.get("operationType") == "update":
        updated_fields = change.get("updateDescription", {}).get("updatedFields", {})

        # Check if watched fields are present
        watched_fields = ['wifiName', 'wifiPassword']
        if any(field in updated_fields for field in watched_fields):
            print("🔧 Watched field updated!")
            print("Updated fields:", updated_fields)

            # Update only the changed ones
            if 'wifiName' in updated_fields:
                last_ssid = updated_fields['wifiName']
            if 'wifiPassword' in updated_fields:
                last_password = updated_fields['wifiPassword']

            # Only connect if both are available
            if last_ssid and last_password:
                connect_to_wifi(last_ssid, last_password)
            else:
                print("⚠️ Waiting for both SSID and password to be set.")
        else:
            print("🫥 Update happened, but not in a watched field.")
    else:
        print(f"Detected {change.get('operationType')} operation. Ignored.")

def watch_changes():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    try:
        with collection.watch(full_document='default') as change_stream:
            print("🔍 Listening to changes in robot collection...")
            for change in change_stream:
                on_change(change)

    except PyMongoError as e:
        print("❌ Error watching collection:", e)

if __name__ == "__main__":
    watch_changes()