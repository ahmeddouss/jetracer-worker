from pymongo import MongoClient
from bson import ObjectId
from pymongo.errors import PyMongoError
import pprint
from dotenv import load_dotenv
import os
from workers.wifi_scanner import connect_to_wifi
load_dotenv(".env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")

def on_change(change):
    operation_type = change.get("operationType")

    print("\n--- Change Detected ---")
    pprint.pprint(change)

    if operation_type == 'update':
        updated_fields = change.get("updateDescription", {}).get("updatedFields", {})

        watched_fields = ['wifiName', 'wifiPassword']
        if any(field in updated_fields for field in watched_fields):
            print("🔧 Watched field updated!")
            print("Updated fields:", updated_fields)

            # Extract values (or fall back to None)
            ssid = updated_fields.get("wifiName")
            password = updated_fields.get("wifiPassword")

            if ssid and password:
                connect_to_wifi(ssid, password)
            else:
                print("⚠️ SSID or Password missing in update.")


    elif operation_type in ['insert', 'replace', 'delete']:
        print(f"Detected {operation_type} operation.")

def watch_wifi_changes():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    try:
        pipeline = [{"$match": {"documentKey._id": ObjectId(DOCUMENT_ID)}}]
        with collection.watch(pipeline=pipeline, full_document='updateLookup') as change_stream:
            print("🔍 Listening to changes in specific document...")
            for change in change_stream:
                on_change(change)

    except PyMongoError as e:
        print("❌ Error watching collection:", e)

if __name__ == "__main__":
    watch_wifi_changes()
