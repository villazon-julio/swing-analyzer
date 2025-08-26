# GOLF SWING INSTANT REPLAY (VOICE CONTROLLED)
#
# This application uses voice commands to control a capture/replay loop.
# - Say "ok" to start recording a 15-second clip.
# - During replay, say "ok" again to skip the replay and return to listening.
#
# Created by Gemini
#
# REQUIRES:
# pip install opencv-python SpeechRecognition PyAudio
#
# NOTE: This uses the Google Speech Recognition API and requires an
#       active internet connection to function.

import cv2
import time
import collections
import numpy as np
import speech_recognition as sr
import threading

# --- Configuration -----------------------------------------------------------
# You may need to change these values based on your setup.

# The index of your camera. 0 is usually the default built-in webcam.
# Try 1, 2, etc., if 0 doesn't work for your Canon camera.
CAMERA_INDEX = 0

# Duration of the capture and replay in seconds.
REPLAY_DURATION_SECONDS = 5

# Keyword to start recording and skip replay.
TRIGGER_WORD = "go"

# --- End of Configuration ----------------------------------------------------

# A thread-safe event to signal that the trigger word has been spoken.
trigger_word_event = threading.Event()

def voice_listener():
    """
    Listens for the trigger word in the background and sets an event flag.
    This function runs in a separate thread.
    """
    global trigger_word_event
    r = sr.Recognizer()
    mic = sr.Microphone()

    print("Voice listener thread started. Calibrating microphone...")
    with mic as source:
        # Adjust for ambient noise for better recognition
        r.adjust_for_ambient_noise(source, duration=1)
    print("Microphone calibrated. Listening for the trigger word...")

    while True:
        with mic as source:
            try:
                # Listen for audio input from the microphone
                audio = r.listen(source, phrase_time_limit=2)
                # Recognize speech using Google's online service
                text = r.recognize_google(audio)
                print(f"Heard: '{text}'")
                if TRIGGER_WORD in text.lower():
                    print(f"Trigger word '{TRIGGER_WORD}' detected!")
                    trigger_word_event.set() # Signal that the word was heard
            except sr.UnknownValueError:
                # This error means the recognizer couldn't understand the audio
                pass
            except sr.RequestError as e:
                # This error means there's an issue with the API request
                print(f"Could not request results from Google Speech Recognition service; {e}")
            except Exception as e:
                print(f"An error occurred in the voice listener: {e}")


def put_text_on_frame(frame, text, color):
    """Utility function to draw styled text on a video frame."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.2
    thickness = 3
    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = text_size[1] + 20

    overlay = frame.copy()
    cv2.rectangle(overlay, (text_x - 10, text_y - text_size[1] - 10),
                  (text_x + text_size[0] + 10, text_y + 10), (0, 0, 0), -1)
    alpha = 0.6
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)
    return frame


def main():
    """Main function to run the capture-replay loop with voice control."""
    print("Starting Instant Replay application...")
    print("Press 'q' in the video window to quit.")

    # Start the voice listener in a background daemon thread
    listener_thread = threading.Thread(target=voice_listener, daemon=True)
    listener_thread.start()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Could not open camera at index {CAMERA_INDEX}.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera feed opened successfully at {width}x{height}, {fps:.2f} FPS.")

    window_name = 'Instant Replay'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1280, 720)

    # Main application loop - State machine: LISTENING -> RECORDING -> REPLAYING
    while True:
        # -----------------------------------------------------------------
        # 1. LISTENING PHASE
        # -----------------------------------------------------------------
        print(f"\nListening for trigger word '{TRIGGER_WORD}'...")
        trigger_word_event.clear() # Ensure event is clear before listening
        while not trigger_word_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break
            
            display_frame = frame.copy()
            text = f"SAY '{TRIGGER_WORD.upper()}' TO RECORD"
            display_frame = put_text_on_frame(display_frame, text, (255, 255, 0)) # Cyan
            cv2.imshow(window_name, display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return

        # -----------------------------------------------------------------
        # 2. CAPTURE PHASE
        # -----------------------------------------------------------------
        print(f"\nStarting {REPLAY_DURATION_SECONDS}-second capture phase...")
        capture_buffer = collections.deque()
        start_time = time.time()

        while time.time() - start_time < REPLAY_DURATION_SECONDS:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break
            capture_buffer.append(frame)

            display_frame = frame.copy()
            countdown = REPLAY_DURATION_SECONDS - (time.time() - start_time)
            rec_text = f"RECORDING... ({countdown:.1f}s)"
            display_frame = put_text_on_frame(display_frame, rec_text, (0, 0, 255)) # Red
            cv2.imshow(window_name, display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return

        if not capture_buffer:
            print("Capture buffer is empty. Returning to listening mode.")
            continue

        # -----------------------------------------------------------------
        # 3. REPLAY PHASE
        # -----------------------------------------------------------------
        print(f"Starting {REPLAY_DURATION_SECONDS}-second replay phase...")
        trigger_word_event.clear() # Clear event before starting replay
        frame_delay = 0.5 / fps

        for frame in list(capture_buffer):
            # Check if the trigger word was spoken to skip the replay
            if trigger_word_event.is_set():
                print("Trigger word detected. Skipping replay.")
                break

            replay_start_time = time.time()
            display_frame = frame.copy()
            display_frame = put_text_on_frame(display_frame, "REPLAY", (0, 255, 0)) # Green
            cv2.imshow(window_name, display_frame)

            processing_time = time.time() - replay_start_time
            wait_time = max(1, int((frame_delay - processing_time) * 1000))
            
            if cv2.waitKey(wait_time) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return

    print("Exiting application.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
