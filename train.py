import cv2
import numpy as np
from PIL import Image
import os

# Path for training images
path = 'training_images'

# Initialize recognizer and face detector
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def getImagesAndLabels(path):
    # Support for jpg, jpeg, and png
    imagePaths = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]     
    faceSamples = []
    ids = []

    for imagePath in imagePaths:
        # Convert to grayscale
        PIL_img = Image.open(imagePath).convert('L') 
        img_numpy = np.array(PIL_img, 'uint8')

        # Get ID from filename (e.g., "1.joshna.jpeg" -> 1)
        filename = os.path.split(imagePath)[-1]
        try:
            # We take the part before the first dot
            student_id = int(filename.split(".")[0])
        except Exception as e:
            print(f"Skipping {filename}: Filename must start with a number (e.g., 1.name.jpg)")
            continue

        # Detect the face in the training image
        faces = detector.detectMultiScale(img_numpy)

        for (x, y, w, h) in faces:
            faceSamples.append(img_numpy[y:y+h, x:x+w])
            ids.append(student_id)
            print(f"Training ID {student_id} from {filename}")

    return faceSamples, ids

print("\n[INFO] Training faces. This will take a moment...")

faces, ids = getImagesAndLabels(path)

if len(faces) == 0:
    print("\n[ERROR] No faces found! Make sure your photos are clear and named correctly.")
else:
    recognizer.train(faces, np.array(ids))

    # Save the model
    if not os.path.exists('trainer'):
        os.makedirs('trainer')
    recognizer.write('trainer/trainer.yml') 

    print(f"\n[INFO] {len(np.unique(ids))} unique students trained successfully.")
