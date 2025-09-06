# app.py
import os
from flask import Flask, request, jsonify
import face_recognition
import requests
from io import BytesIO

app = Flask(__name__)

supabase_url = "https://punnqvevnkhsjoytugie.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InB1bm5xdmV2bmtoc2pveXR1Z2llIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5OTUwOTQsImV4cCI6MjA3MjU3MTA5NH0.i-cH0GYuaFlpkxs3hGhdPbitNyYkj_4WnklxoaoLBgM"

supabase: Client = create_client(supabase_url, supabase_key)

# This endpoint receives attendance photo and tries to match with registered students
@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    attendance_file = request.files["image"]
    attendance_img = face_recognition.load_image_file(attendance_file)

    # Get face encodings from attendance photo
    attendance_encodings = face_recognition.face_encodings(attendance_img)
    if not attendance_encodings:
        return jsonify({"error": "No face detected in the attendance photo"}), 400
    attendance_encoding = attendance_encodings[0]

    # For demo: Fetch list of students from your Supabase table (implement your own logic)
    # Here, we'll mock it with a couple of students with image URLs
    students = [
        {
            "name": "John Doe",
            "student_id": "123",
            "image_url": f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/student_123.jpg"
        },
        {
            "name": "Jane Smith",
            "student_id": "456",
            "image_url": f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/student_456.jpg"
        }
    ]

    for student in students:
        # Download student's registered image
        try:
            response = requests.get(student["image_url"])
            if response.status_code != 200:
                continue
            student_img = face_recognition.load_image_file(BytesIO(response.content))
            student_encodings = face_recognition.face_encodings(student_img)
            if not student_encodings:
                continue
            student_encoding = student_encodings[0]

            # Compare faces
            results = face_recognition.compare_faces([student_encoding], attendance_encoding, tolerance=0.5)
            if results[0]:
                # Match found
                # Here you can log attendance in DB or do whatever
                return jsonify({"message": f"Attendance marked for {student['name']} (ID: {student['student_id']})"})
        except Exception as e:
            continue

    return jsonify({"error": "No matching student found"}), 404


if __name__ == "__main__":
    # Bind to PORT environment variable or default to 5000 (Render requires this)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
