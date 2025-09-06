// server.js

const express = require('express');
const multer = require('multer');
const { createCanvas, Image } = require('canvas');
const faceapi = require('face-api.js');
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = "https://punnqvevnkhsjoytugie.supabase.co";
const supabaseKey = "YOUR_SUPABASE_SERVICE_KEY"; // Use service role key here
const supabase = createClient(supabaseUrl, supabaseKey);

const app = express();
const upload = multer();

async function loadModels() {
  const modelPath = './models';
  await faceapi.nets.tinyFaceDetector.loadFromDisk(modelPath);
  await faceapi.nets.faceLandmark68Net.loadFromDisk(modelPath);
  await faceapi.nets.faceRecognitionNet.loadFromDisk(modelPath);
}

async function getLabeledDescriptors() {
  const { data: students, error } = await supabase.from('students').select('student_id, image_url');
  if (error) throw error;

  const labeledDescriptors = [];

  for (const student of students) {
    const img = await canvasLoadImage(student.image_url);
    const detection = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();
    if (detection) {
      labeledDescriptors.push(
        new faceapi.LabeledFaceDescriptors(student.student_id, [detection.descriptor])
      );
    }
  }
  return labeledDescriptors;
}

async function canvasLoadImage(url) {
  const response = await fetch(url);
  const buffer = await response.arrayBuffer();
  const img = new Image();
  img.src = Buffer.from(buffer);
  return img;
}

app.post('/mark_attendance', upload.single('image'), async (req, res) => {
  try {
    const imageBuffer = req.file.buffer;
    const img = await canvasLoadImageBuffer(imageBuffer);
    const detection = await faceapi.detectSingleFace(img).withFaceLandmarks().withFaceDescriptor();

    if (!detection) {
      return res.json({ error: 'No face detected' });
    }

    const labeledDescriptors = await getLabeledDescriptors();
    const faceMatcher = new faceapi.FaceMatcher(labeledDescriptors, 0.6);

    const bestMatch = faceMatcher.findBestMatch(detection.descriptor);

    if (bestMatch.label === 'unknown') {
      return res.json({ error: 'Face not recognized' });
    }

    // Mark attendance in Supabase
    const studentId = bestMatch.label;
    const today = new Date().toISOString().slice(0, 10);

    // Check if attendance already marked today
    const { data: existing, error: checkError } = await supabase
      .from('attendance')
      .select('*')
      .eq('student_id', studentId)
      .eq('date', today);

    if (checkError) throw checkError;
    if (existing.length > 0) {
      return res.json({ message: 'Attendance already marked for today.' });
    }

    // Insert attendance
    const { error: insertError } = await supabase
      .from('attendance')
      .insert([{ student_id: studentId, date: today }]);

    if (insertError) throw insertError;

    res.json({ message: `Attendance marked for student ID: ${studentId}` });
  } catch (error) {
    res.json({ error: error.message });
  }
});

async function canvasLoadImageBuffer(buffer) {
  const img = new Image();
  img.src = buffer;
  return img;
}

const PORT = 5000;
loadModels().then(() => {
  app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
});
