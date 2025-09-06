
from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import tempfile
import os
import requests
from supabase import create_client, Client
from datetime import datetime
# Supabase setup
supabase_url = "https://punnqvevnkhsjoytugie.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1bm5xdmV2bmtoc2pveXR1Z2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5OTUwOTQsImV4cCI6MjA3MjU3MTA5NH0.i-cH0GYuaFlpkxs3hGhdPbitNyYkj_4WnklxoaoLBgM"

supabase: Client = create_client(supabase_url, supabase_key)

from flask import Flask, request, jsonify
from flask_cors import CORS
import face_recognition
import numpy as np
import tempfile
import os
import requests
from supabase import create_client, Client
from datetime import datetime



app = Flask(__name__)
CORS(app)

# ---------------- Helper Functions ----------------

def load_registered_faces():
    """Fetch all registered students with their image encodings"""
    students = supabase.table("students").select("*").execute().data
    encodings = []
    student_ids = []

    for s in students:
        try:
            img_url = s["image_url"]
            resp = requests.get(img_url)
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.write(resp.content)
            tmp.close()

            image = face_recognition.load_image_file(tmp.name)
            faces = face_recognition.face_encodings(image)

            if faces:
                encodings.append(faces[0])
                student_ids.append(s["student_id"])
            
            os.unlink(tmp.name)
        except Exception as e:
            print("Error processing", s["student_id"], e)

    return encodings, student_ids


# ---------------- API Routes ----------------

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    file = request.files["image"]
    tmp = tempfile.NamedTemporaryFile(delete=False)
    file.save(tmp.name)

    unknown_image = face_recognition.load_image_file(tmp.name)
    unknown_encodings = face_recognition.face_encodings(unknown_image)

    if not unknown_encodings:
        return jsonify({"error": "No face detected"}), 400

    unknown_encoding = unknown_encodings[0]

    # Load registered students
    known_encodings, student_ids = load_registered_faces()

    if not known_encodings:
        return jsonify({"error": "No registered students found"}), 400

    results = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=0.5)
    matches = np.where(results)[0]

    if len(matches) > 0:
        matched_id = student_ids[matches[0]]

        # ✅ Save attendance record
        supabase.table("attendance").insert({
            "student_id": matched_id,
            "timestamp": datetime.utcnow().isoformat()
        }).execute()

        return jsonify({"message": f"Attendance marked for {matched_id}"})
    else:
        return jsonify({"error": "No match found. Please register."})

# ---------------- Run Server ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
