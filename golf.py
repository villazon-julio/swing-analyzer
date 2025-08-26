# GOLF SWING INSTANT REPLAY (OFFLINE VOICE CONTROL)
#
# This application uses offline voice commands to control a capture/replay loop.
# - Say "ok" to start recording a 15-second clip.
# - During replay, say "ok" again to skip the replay and return to listening.
#
# Created by Gemini
#
# REQUIRES:
# 1. pip install opencv-python vosk pyaudio
# 2. Download a Vosk language model. For English, a small model can be found here:
#    https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
# 3. Unzip the model and place the resulting folder (e.g., "vosk-model-small-en-us-0.15")
#    in the same directory as this Python script.

import cv2
import time
import collections
import threading
import json
import os
import pyaudio
from vosk import Model, KaldiRecognizer

# --- Configuration -----------------------------------------------------------
# You may need to change these values based on your setup.

# The index of your camera. 0 is usually the default built-in webcam.
# Try 1, 2, etc., if 0 doesn't work for your Canon camera.
CAMERA_INDEX = 0

# Duration of the capture and replay in seconds.
REPLAY_DURATION_SECONDS = 5

# Keyword to start recording and skip replay.
TRIGGER_WORD = "okay"

# Path to the Vosk model folder.
# Assumes the model folder is in the same directory as the script.
# UPDATE THIS if you place the model folder elsewhere.
MODEL_PATH = "vosk-model-small-en-us-0.15"

# --- End of Configuration ----------------------------------------------------

# A thread-safe event to signal that the trigger word has been spoken.
trigger_word_event = threading.Event()

def voice_listener():
    """
    Listens for the trigger word in the background using the offline Vosk engine.
    This function runs in a separate thread.
    """
    global trigger_word_event

    if not os.path.exists(MODEL_PATH):
        print(f"Vosk model not found at path: {MODEL_PATH}")
        print("Please download the model, unzip it, and place it in the correct directory.")
        return

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8192)

    print("Voice listener thread started. Listening for the trigger word...")

    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get('text', '')
            if text:
                print(f"Heard: '{text}'")
            if TRIGGER_WORD in text.lower():
                print(f"Trigger word '{TRIGGER_WORD}' detected!")
                trigger_word_event.set() # Signal that the word was heard

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
        frame_delay = 1.0 / fps

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
