import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
from scipy.spatial import distance as dist
from awareness_activity import AwarenessActivity
import os
import csv
from datetime import datetime
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define relative paths
VIDEO_PATH = os.path.join(BASE_DIR, "..", "control-data", "fatigue-test-video-1.mp4")
MODEL_PATH = os.path.join(BASE_DIR, "face_landmarker.task")
LOG_PATH = os.path.join(BASE_DIR, "..", "outputs", "fatigue_results.csv")

# Constants
EAR_DROWSY_THRESHOLD = 0.20
EAR_RECOVERY_THRESHOLD = 0.25
MIN_CLOSURE_LOG = 1.0  # seconds, minimum closure time to log recovery
DROWSY_TIME_LIMIT = 2.5  # seconds

ear_history = []
activity = AwarenessActivity(port='COM3')
drowsy_start_time = None

def calculate_ear(eye_landmarks):
    """
    Calculate the Eye Aspect Ratio (EAR) for the given eye landmarks.
    
    Args:
        eye_landmarks (list): List of (x, y) coordinates for the eye landmarks.
    
    Returns:
        float: The calculated EAR value.
    """
    # Vertical distances for average
    v1 = dist.euclidean(eye_landmarks[1], eye_landmarks[5])
    v2 = dist.euclidean(eye_landmarks[2], eye_landmarks[4])
    # Horizontal distance
    h = dist.euclidean(eye_landmarks[0], eye_landmarks[3])
    return (v1 + v2) / (2.0 * h)

def log_event(event_type, ear_val, reaction_time=0, duration=0):
    """
    Log an event to the CSV file.
    
    Args:
        event_type (str): Type of event (e.g., "SUCCESS", "TIMEOUT", "RECOVERY").
        ear_val (float): Current EAR value.
        reaction_time (float): Time taken to react (default 0).
        duration (float): Duration of the event (incident or closure time).
    """
    log_dir = os.path.dirname(LOG_PATH)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)  # This creates the outputs directory automatically
    
    file_exists = os.path.isfile(LOG_PATH)
    with open(LOG_PATH, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Event", "EAR", "Reaction_Time", "Duration"])
        
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            event_type, 
            round(ear_val, 3), 
            round(reaction_time, 2),
            round(duration, 2)
        ])

# Initialize MediaPipe Face Landmarker
BaseOptions = python.BaseOptions
FaceLandmarker = vision.FaceLandmarker
FaceLandmarkerOptions = vision.FaceLandmarkerOptions
VisionRunningMode = vision.RunningMode

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=VisionRunningMode.IMAGE,
    num_faces=1
)

face_landmarker = FaceLandmarker.create_from_options(options)

# Indices for the eyes as per MediaPipe Face Mesh
LEFT_EYE_INDEX = [362, 385, 387, 263, 373, 380] 
RIGHT_EYE_INDEX = [33, 160, 158, 133, 153, 144]

# Start Live Video Capture
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# For testing with a video file instead of webcam
# cap = cv2.VideoCapture(VIDEO_PATH)
print(f"Video opened: {cap.isOpened()}")

cv2.namedWindow('Fatigue Monitor', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Fatigue Monitor', 800, 600)
                       
smoothed_ear = 0.0  # Default value to prevent crash if face is lost

while cap.isOpened():
    success, frame = cap.read()
    frame = cv2.flip(frame, 1)
    if not success: break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    results = face_landmarker.detect(mp_image)

    if results.face_landmarks:
        landmarks = results.face_landmarks[0]
        ih, iw, _ = frame.shape
        
        left_points = [(int(landmarks[i].x * iw), int(landmarks[i].y * ih)) for i in LEFT_EYE_INDEX]
        right_points = [(int(landmarks[i].x * iw), int(landmarks[i].y * ih)) for i in RIGHT_EYE_INDEX]

        # Draw points
        for (x, y) in left_points + right_points:
            cv2.circle(frame, (x, y), 2, (0, 255, 255), -1)
        
        current_ear = calculate_ear(left_points)
        ear_history.append(current_ear)
        if len(ear_history) > 5: ear_history.pop(0)
        smoothed_ear = sum(ear_history) / len(ear_history)    

    # --- LOGIC & ALARMS ---
    if smoothed_ear < EAR_DROWSY_THRESHOLD and smoothed_ear > 0:
        if drowsy_start_time is None:
            drowsy_start_time = time.time()  # Start the clock
        
        # Calculate how long eyes have been closed
        drowsy_duration = time.time() - drowsy_start_time
        color = (0, 0, 255) # Red
    else:

        if drowsy_start_time is not None and not activity.is_active:
            # This logs a "Safe Recovery" if they blinked long but woke up before the alarm
            total_closed = time.time() - drowsy_start_time
            if total_closed > MIN_CLOSURE_LOG:  # Only log significant closures
                log_event("RECOVERY", smoothed_ear, 0, total_closed)
        drowsy_start_time = None  # Reset the clock if eyes open
        drowsy_duration = 0
        color = (0, 255, 0) # Green
        if smoothed_ear > EAR_RECOVERY_THRESHOLD:
            pygame.mixer.stop()

    # Trigger Activity if duration exceeds limit
    if drowsy_duration >= DROWSY_TIME_LIMIT:
        if not activity.is_active and not pygame.mixer.get_busy():
            activity.start_new_activity()

    if activity.is_active:
        result = activity.update(frame)
        if result is not None:
            status, reaction_time = result
            # Calculate total incident time from first closure to end of activity
            total_incident_time = time.time() - activity.start_time + DROWSY_TIME_LIMIT
            
            if status is True:
                log_event("SUCCESS", smoothed_ear, reaction_time, total_incident_time)
            else:
                log_event("TIMEOUT", smoothed_ear, reaction_time, total_incident_time)
    
    # --- DISPLAY EAR ---
    # Moved to (50, 50) and scaled down to 1.5 for professional look
    cv2.putText(frame, f"EAR: {smoothed_ear:.2f}", (50, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)

    cv2.imshow('Fatigue Monitor', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

face_landmarker.close()
cap.release()
cv2.destroyAllWindows()                  