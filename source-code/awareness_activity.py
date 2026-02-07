import random
import time
import serial
import cv2
import pygame
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(BASE_DIR, "..", "sounds")

# Constants
TIMEOUT_LIMIT = 3.0  # seconds to react
SERIAL_BUFFER_THRESHOLD = 10  # bytes to clear old data
HEADER_RECT = (20, 20, 400, 150)
REACT_TEXT_POS = (40, 70)
TIME_TEXT_POS = (40, 120)
FONT_SCALE_REACT = 1.0
FONT_SCALE_TIME = 0.8
FONT_THICKNESS = 2


class AwarenessActivity:
    def __init__(self, port='COM3', baudrate=9600):
        self.is_active = False
        self.required_move = None
        self.start_time = 0
        self.timeout_limit = TIMEOUT_LIMIT
        
        # Initialize Serial for Arduino
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.1)
        except:
            print("Warning: Arduino not connected. Activity will run in 'Debug Mode'.")
            self.ser = None

        # Initialize Audio
        pygame.mixer.init()
        try:
            self.sound_alert = pygame.mixer.Sound(os.path.join(SOUND_DIR, "activity_start.wav"))
            self.sound_success = pygame.mixer.Sound(os.path.join(SOUND_DIR, "activity_success.wav"))
            self.sound_alarm = pygame.mixer.Sound(os.path.join(SOUND_DIR, "activity_failure.wav"))
        except:
            print("Audio files not found. Continuing without sound.")
            self.sound_alert = self.sound_success = self.sound_alarm = None

    def start_new_activity(self):
        """
        Start a new awareness activity by selecting a random move and initializing timers.
        """
        self.required_move = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
        self.start_time = time.time()
        self.is_active = True
        if self.sound_alert:
            self.sound_alert.play()
        print(f"DEBUG: Awareness Activity Started! Move: {self.required_move}")

    def update(self, frame):
        """
        Update the activity state, draw UI, check for input, and handle timeout.
        
        Args:
            frame: The video frame to draw on.
        
        Returns:
            tuple: (True, elapsed) if success, (False, elapsed) if failure/timeout, None if ongoing.
        """
        if not self.is_active:
            return None

        elapsed = time.time() - self.start_time
        remaining = max(0, self.timeout_limit - elapsed)

        # Draw a sleek, semi-transparent-look header
        cv2.rectangle(frame, HEADER_RECT[:2], HEADER_RECT[2:], (0, 0, 0), -1)

        # REACT text
        cv2.putText(frame, f"REACT: {self.required_move}", REACT_TEXT_POS, 
                    cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE_REACT, (0, 255, 255), FONT_THICKNESS)

        # TIME text
        cv2.putText(frame, f"TIME: {remaining:.1f}s", TIME_TEXT_POS, 
                    cv2.FONT_HERSHEY_SIMPLEX, FONT_SCALE_TIME, (255, 255, 255), FONT_THICKNESS)

        # Check for Serial Input
        if self.ser and self.ser.in_waiting > 0:
            # Clear old data so we only react to the freshest input
            while self.ser.in_waiting > SERIAL_BUFFER_THRESHOLD: 
                self.ser.read() 
                
            response = self.ser.readline().decode('utf-8').strip()
            if response == self.required_move:
                self.is_active = False
                if self.sound_success:
                    self.sound_success.play()
                return True, elapsed  # Return status AND time taken

        # Check for Timeout
        if elapsed > self.timeout_limit:
            self.is_active = False
            if self.sound_alarm:
                self.sound_alarm.play(loops=-1)
            return False, elapsed  # Return status AND the full timeout duration

        return None  # Activity still in progress