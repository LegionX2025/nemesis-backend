from pymongo import MongoClient
import sys

uri = "mongodb+srv://nemesis:nemesis2026@nemesisdb.vir5vg2.mongodb.net/?appName=nemesisdb"
client = MongoClient(uri)

try:
    client.admin.command("ping")
    print("MongoDB Connected successfully! The credentials are correct.")
    client.close()
except Exception as e:
    print("The following error occurred: ", e)
    sys.exit(1)
