# GOLF SWING INSTANT REPLAY (OFFLINE VOICE CONTROL)
#
# This application uses offline voice commands to control a capture/replay loop.
# - Say "okay" to start recording a 5-second clip.
# - Say "again" to repeat the last replay.
# - During replay, say "okay" to skip the replay and return to listening.
#
# Created by Gemini
#
# REQUIRES:
# 1. pip install opencv-python vosk pyaudio
# 2. Download a Vosk language model. For English, a small model can be found here:
#    https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
# 3. Unzip the model and place the resulting folder (e.g., "vosk-model-small-en-us-0.15")
#    in the same directory as this Python script.
# 4. Place a sound file named "chime.wav" in the same directory as this script.

import cv2
import time
import collections
import threading
import json
import os
import pyaudio
import wave
from vosk import Model, KaldiRecognizer

# --- Configuration -----------------------------------------------------------
# You may need to change these values based on your setup.

# The index of your camera. 0 is usually the default built-in webcam.
# Try 1, 2, etc., if 0 doesn't work for your Canon camera.
CAMERA_INDEX = 0

# Duration of the capture and replay in seconds.
REPLAY_DURATION_SECONDS = 4

# Keyword to start recording and skip replay.
TRIGGER_WORD = "okay"

# Keyword to repeat the last replay.
REPEAT_TRIGGER_WORD = "otra"

# Path to the Vosk model folder.
# Assumes the model folder is in the same directory as the script.
# UPDATE THIS if you place the model folder elsewhere.
# English
# MODEL_PATH = "vosk-model-small-en-us-0.15"
# Spanish
MODEL_PATH = "vosk-model-small-es-0.42"

# Path to the confirmation chime sound file.
CHIME_WAV_PATH = "chime.wav"

# --- End of Configuration ----------------------------------------------------

# Thread-safe events to signal which command was heard.
start_record_event = threading.Event()
repeat_replay_event = threading.Event()

def play_chime():
    """Plays a .wav file as an audible confirmation."""
    if not os.path.exists(CHIME_WAV_PATH):
        print(f"Chime file not found: {CHIME_WAV_PATH}")
        return

    try:
        # Open the wave file
        wf = wave.open(CHIME_WAV_PATH, 'rb')
        p = pyaudio.PyAudio()

        # Open a stream
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)

        # Read and play data in chunks
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)

        # Clean up
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
    except Exception as e:
        print(f"Error playing chime: {e}")


def voice_listener():
    """
    Listens for trigger words in the background and sets the appropriate event.
    """
    global start_record_event, repeat_replay_event

    if not os.path.exists(MODEL_PATH):
        print(f"Vosk model not found at path: {MODEL_PATH}")
        return

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)

    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=8192)

    print("Voice listener thread started. Listening for trigger words...")

    while True:
        data = stream.read(4096, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get('text', '')
            if text:
                print(f"Heard: '{text}'")
            
            text_lower = text.lower()
            if TRIGGER_WORD in text_lower:
                print(f"Trigger word '{TRIGGER_WORD}' detected!")
                play_chime()
                start_record_event.set()
            elif REPEAT_TRIGGER_WORD in text_lower:
                print(f"Repeat trigger word '{REPEAT_TRIGGER_WORD}' detected!")
                play_chime()
                repeat_replay_event.set()

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

def run_replay(capture_buffer, fps, window_name):
    """Handles the replay phase logic."""
    print(f"Starting {REPLAY_DURATION_SECONDS}-second replay phase...")
    start_record_event.clear() # Clear event before starting replay
    frame_delay = 0.5 / fps

    for frame in list(capture_buffer):
        # Check if the trigger word was spoken to skip the replay
        if start_record_event.is_set():
            print("Trigger word detected. Skipping replay.")
            break

        replay_start_time = time.time()
        display_frame = frame.copy()
        display_frame = put_text_on_frame(display_frame, "REPLAY", (0, 255, 0)) # Green
        cv2.imshow(window_name, display_frame)

        processing_time = time.time() - replay_start_time
        wait_time = max(1, int((frame_delay - processing_time) * 1000))

        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            return False # Signal to quit
    return True # Signal to continue

def main():
    """Main function to run the capture-replay loop with voice control."""
    print("Starting Instant Replay application...")
    print("Press 'q' in the video window to quit.")

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

    last_capture_buffer = None

    while True:
        # -----------------------------------------------------------------
        # 1. LISTENING PHASE
        # -----------------------------------------------------------------
        print(f"\nListening for '{TRIGGER_WORD}' or '{REPEAT_TRIGGER_WORD}'...")
        start_record_event.clear()
        repeat_replay_event.clear()
        
        while not start_record_event.is_set() and not repeat_replay_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame.")
                break

            display_frame = frame.copy()
            text = f"SAY '{TRIGGER_WORD.upper()}' TO RECORD OR '{REPEAT_TRIGGER_WORD.upper()}' TO REPEAT"
            display_frame = put_text_on_frame(display_frame, text, (255, 255, 0)) # Cyan
            cv2.imshow(window_name, display_frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return
        
        # Check which command was received
        if start_record_event.is_set():
            # -----------------------------------------------------------------
            # 2. CAPTURE PHASE
            # -----------------------------------------------------------------
            print(f"\nStarting {REPLAY_DURATION_SECONDS}-second capture phase...")
            current_capture_buffer = collections.deque()
            start_time = time.time()

            while time.time() - start_time < REPLAY_DURATION_SECONDS:
                ret, frame = cap.read()
                if not ret:
                    print("Error: Failed to grab frame.")
                    break
                current_capture_buffer.append(frame)

                display_frame = frame.copy()
                countdown = REPLAY_DURATION_SECONDS - (time.time() - start_time)
                rec_text = f"RECORDING... ({countdown:.1f}s)"
                display_frame = put_text_on_frame(display_frame, rec_text, (0, 0, 255)) # Red
                cv2.imshow(window_name, display_frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cap.release()
                    cv2.destroyAllWindows()
                    return

            if not current_capture_buffer:
                print("Capture buffer is empty. Returning to listening mode.")
                continue
            
            last_capture_buffer = current_capture_buffer
            if not run_replay(last_capture_buffer, fps, window_name):
                break # Quit if 'q' was pressed during replay

        elif repeat_replay_event.is_set():
            if last_capture_buffer:
                if not run_replay(last_capture_buffer, fps, window_name):
                    break # Quit if 'q' was pressed during replay
            else:
                print("No replay available to repeat.")
                time.sleep(1) # Brief pause to prevent spamming the console

    print("Exiting application.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
