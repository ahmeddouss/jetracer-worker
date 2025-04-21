from pymongo import MongoClient
from pymongo.errors import PyMongoError
import pprint
from dotenv import load_dotenv
import os
import subprocess

load_dotenv(".env")

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")

# Cache to store last known credentials
last_ssid = None
last_password = None

def connect_to_wifi(ssid, password):
    try:
        print(f"Connecting to Wi-Fi SSID: {ssid}")
        subprocess.run(["nmcli", "dev", "wifi", "connect", ssid, "password", password], check=True)

    except subprocess.CalledProcessError as e:
        print(f"Error connecting to Wi-Fi: {e}")
        subprocess.run(["aplay","jetracer_worker/sounds/error.wav"])


def on_change(change):
    global last_ssid, last_password

    print("\n--- Change Detected ---")
    pprint.pprint(change)

    # Only act on updates to document with _id == "robot"
    doc_id = change.get("documentKey", {}).get("_id")
    if doc_id != DOCUMENT_ID:
        print(f"   ^z         ^o Ignored update to document _id: {doc_id}")
        return

    if change.get("operationType") == "update":
        updated_fields = change.get("updateDescription", {}).get("updatedFields", {})


        # Check if watched fields are present
        watched_fields = ['wifiName', 'wifiPassword']
        if any(field in updated_fields for field in watched_fields):
            print("   ^=^t    Watched field updated!")
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
                print("   ^z         ^o Waiting for both SSID and password to be set.")
        else:
            print("   ^=       Update happened, but not in a watched field.")
    else:
        print(f"Detected {change.get('operationType')} operation. Ignored.")

def watch_wifi_changes():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]

    try:
        with collection.watch(full_document='default') as change_stream:
            print("   ^=^t^m Listening to changes in robot collection...")
            for change in change_stream:
                on_change(change)

    except PyMongoError as e:
        print("   ^}^l Error watching collection:", e)

