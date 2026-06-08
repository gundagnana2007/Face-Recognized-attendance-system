<html>
<p>SmartAttend is a contactless, automated attendance management solution that leverages Computer Vision and Deep Learning to streamline identity verification. By utilizing a Convolutional Neural Network (CNN) architecture, the system recognizes registered faces in real-time and logs attendance data into an automated database, eliminating manual roll calls and proxy attendance.</P>

<h1> 🚀 Key Features <h1>
<ul><li>
Real-Time Detection: Instant face localization and recognition using live webcam feeds.

High Accuracy: Powered by a CNN-based feature extraction model designed to handle variations in lighting and head poses.

Automated Logging: Seamlessly records Student ID, Name, Date, and Timestamp into a CSV/Excel backend.

Anti-Proxy Logic: Ensures unique identification through biometric landmarks, preventing students from marking attendance for others.

Admin Dashboard: A lightweight Flask web interface for faculty to manage student rosters and export attendance reports.
</li></ul>
<h1>🛠️ Tech Stack</h1>
<ul><li>
Language: Python 3.12

AI/Deep Learning: TensorFlow, Keras (CNN Architecture)

Computer Vision: OpenCV (Image Pre-processing & Live Streaming)

Web Framework: Flask (Backend & Dashboard)

Data Handling: NumPy & Pandas (Matrix operations & CSV management)
</li></ul>