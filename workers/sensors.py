#!/usr/bin/env python3
import time
import random
from datetime import datetime
import pymongo
from pymongo.errors import PyMongoError
import os
from dotenv import load_dotenv


print("Mode simulation activé - GPIO désactivé")
load_dotenv(".env")

# Configuration MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")
DOCUMENT_ID = os.getenv("DOCUMENT_ID")

class SensorSystem:
    def __init__(self):
        self.simulation_mode = True  # Mode simulation forcé
        
        # Connexion MongoDB seulement
        try:
            self.client = pymongo.MongoClient(
                MONGO_URI,
                tls=True,
                tlsAllowInvalidCertificates=True,
                connectTimeoutMS=5000
            )
            self.db = self.client[DB_NAME]
            self.collection = self.db[COLLECTION_NAME]
            self.client.admin.command('ping')
            print("Connexion MongoDB réussie")
        except Exception as e:
            print(f"Erreur MongoDB : {e}")
            raise

    def read_sensors(self):
        """Simulation des capteurs"""
        temp = round(25.0 + (random.random() * 2 - 1), 1)  # 24-26°C
        hum = round(50.0 + (random.random() * 10 - 5), 1)   # 45-55%
        alert = random.random() > 0.9  # 10% chance d'alerte
        
        gas_data = {
            'status': 'normal' if not alert else 'alert',
            'percentage': round(random.uniform(0.01, 0.05) if not alert else random.uniform(0.5, 1.0), 2)
        }
        
        return temp, hum, gas_data

    def update_database(self, temp, hum, gas_data):
        """Met à jour la base de données avec la structure exacte"""
        document = {
            "temperature": temp,
            "humidity": hum,
            "gas_detection": gas_data,
            "last_update": datetime.utcnow(),
            "sensors": ["DHT11", "MQ-2"],
            "location": "Warehouse A"
        }

        try:
            result = self.collection.update_one(
                {"_id": DOCUMENT_ID},
                {"$set": document},
                upsert=True
            )
            return result.acknowledged
        except PyMongoError as e:
            print(f"Erreur base de données: {e}")
            return False

    def run(self):
        """Boucle principale"""
        print("Système de surveillance activé")
        try:
            while True:
                temp, hum, gas_data = self.read_sensors()
                
                if self.update_database(temp, hum, gas_data):
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Temp: {temp}°C | Hum: {hum}% | "
                          f"Gaz: {gas_data['status']} ({gas_data['percentage']*100:.2f}%)")
                else:
                    print("Erreur lors de la mise à jour de la base de données")
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\nArrêt demandé...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoyage des ressources"""
        if hasattr(self, 'client'):
            self.client.close()
        print("Ressources libérées")

if __name__ == "__main__":
    try:
        system = SensorSystem()
        system.run()
    except Exception as e:
        print(f"Erreur initialisation: {e}")
        exit(1)