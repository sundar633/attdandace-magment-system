from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from datetime import datetime
from supabase import create_client, Client

# Supabase setup
supabase_url = "https://punnqvevnkhsjoytugie.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1bm5xdmV2bmtoc2pveXR1Z2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5OTUwOTQsImV4cCI6MjA3MjU3MTA5NH0.i-cH0GYuaFlpkxs3hGhdPbitNyYkj_4WnklxoaoLBgM"

supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)

# Load and encode all student faces from Supabase
def load_known_faces():
    known_encodings = []
    known_ids = []

    students = supabase.table("students").select("*").execute()
    for student in students.data:
        image_url = student['image_url']
        student_id = student['student_id']

        try:
            response = requests.get(image_url)
            img = face_recognition.load_image_file(BytesIO(response.content))
            encodings = face_recognition.face_encodings(img)

            if encodings:
                known_encodings.append(encodings[0])
                known_ids.append(student_id)
            else:
                print(f"No face found in image for {student_id}")

        except Exception as e:
            print(f"Error loading image for {student_id}: {e}")

    return known_encodings, known_ids


@app.route("/")
def home():
    return "✅ Flask Server is Running!"

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    image = face_recognition.load_image_file(image_file)
    unknown_encodings = face_recognition.face_encodings(image)

    if not unknown_encodings:
        return jsonify({"error": "No face found in uploaded image"}), 400

    unknown_encoding = unknown_encodings[0]

    known_encodings, known_ids = load_known_faces()

    if not known_encodings:
        return jsonify({"error": "No known student faces loaded"}), 500

    matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.5)
    if True in matches:
        match_index = matches.index(True)
        student_id = known_ids[match_index]

        # Mark attendance
        data = {
            "student_id": student_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        response = supabase.table("attendance").insert(data).execute()

        return jsonify({"message": f"✅ Attendance marked for {student_id}"}), 200

    return jsonify({"message": "❌ Face not recognized"}), 401

if __name__ == "__main__":
    app.run(debug=True)
