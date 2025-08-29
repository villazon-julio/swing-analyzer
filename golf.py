# GOLF SWING INSTANT REPLAY (OFFLINE VOICE CONTROL - SPANISH)
#
# This application uses offline Spanish voice commands to control a capture/replay loop.
# - Say "okay" to start recording a 4-second clip.
# - Say "otra" to repeat the last replay.
# - During replay, say "lento" to slow down or "rápido" to speed up.
# - Say "menu" to toggle an information display.
# - Say "salir" to exit the application.
#
# Created by Gemini
#
# REQUIRES:
# 1. pip install opencv-python vosk pyaudio
# 2. Download the SPANISH Vosk model from:
#    https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
# 3. Unzip the model and place the "vosk-model-small-es-0.42" folder
#    in the same directory as this Python script.
# 4. Place a sound file named "chime.wav" in the same directory as this script.

import cv2
import time
import collections
import threading
import json
import os
import sys
import pyaudio
import wave
from vosk import Model, KaldiRecognizer

# --- Helper function for PyInstaller ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Configuration -----------------------------------------------------------
# The index of your camera. 0 is usually the default built-in webcam.
CAMERA_INDEX = 0
REPLAY_DURATION_SECONDS = 4

# Spanish Voice Commands
TRIGGER_WORD = "okay"           # "record"
REPEAT_TRIGGER_WORD = "otra"    # "repeat"
EXIT_WORD = "salir"             # "exit"
SPEED_UP_WORD = "rapido"        # "fast"
SPEED_DOWN_WORD = "lento"       # "slow"
INFO_TOGGLE_WORD = "menu"       # "menu"

# Path to the Spanish Vosk model folder.
MODEL_PATH = resource_path("vosk-model-small-es-0.42")
CHIME_WAV_PATH = resource_path("chime.wav")
# --- End of Configuration ----------------------------------------------------

# --- Shared State for Threads ---
# Using mutable objects like lists allows threads to safely modify them.
shared_state = {
    "start_record": threading.Event(),
    "repeat_replay": threading.Event(),
    "exit_app": threading.Event(),
    "toggle_info": threading.Event(),
    "replay_speed_factor": [2.0], # Start at half speed (2.0x slower)
    "last_heard_command": [""] # To display the last command
}

def get_camera_name(device_index):
    """Attempts to get the camera's hardware name. Falls back to index."""
    if sys.platform == 'linux' or sys.platform == 'linux2':
        try:
            # On Linux, device info is often available in the /sys/class/video4linux directory
            path = f"/sys/class/video4linux/video{device_index}/name"
            with open(path, 'r') as f:
                name = f.read().strip()
                return name
        except Exception:
            # Fallback if the path doesn't exist or there's a permission issue
            return f"Camera (Index {device_index})"
    # Add other platform checks here if needed (e.g., for Windows or macOS)
    return f"Camera (Index {device_index})"


def play_chime():
    """Plays a .wav file as an audible confirmation."""
    if not os.path.exists(CHIME_WAV_PATH):
        print(f"Chime file not found: {CHIME_WAV_PATH}")
        return
    try:
        wf = wave.open(CHIME_WAV_PATH, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        stream.stop_stream()
        stream.close()
        p.terminate()
        wf.close()
    except Exception as e:
        print(f"Error playing chime: {e}")

def voice_listener():
    """Listens for trigger words and updates the shared state."""
    if not os.path.exists(MODEL_PATH):
        print(f"Vosk model not found at path: {MODEL_PATH}")
        return

    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    print("Voice listener thread started. Listening for trigger words...")

    while not shared_state["exit_app"].is_set():
        data = stream.read(4096, exception_on_overflow=False)
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get('text', '')
            if text:
                print(f"Heard: '{text}'")
                # Sanitize text for display by removing special characters
                sanitized_text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                shared_state["last_heard_command"][0] = sanitized_text
            
            # Normalize text for command matching
            text_lower = text.lower().replace('á', 'a').replace('ú', 'u')

            if EXIT_WORD in text_lower:
                print(f"Exit word '{EXIT_WORD}' detected!")
                shared_state["exit_app"].set()
            elif TRIGGER_WORD in text_lower:
                print(f"Trigger word '{TRIGGER_WORD}' detected!")
                play_chime()
                shared_state["start_record"].set()
            elif REPEAT_TRIGGER_WORD in text_lower:
                print(f"Repeat trigger word '{REPEAT_TRIGGER_WORD}' detected!")
                play_chime()
                shared_state["repeat_replay"].set()
            elif INFO_TOGGLE_WORD in text_lower:
                print(f"Info toggle word '{INFO_TOGGLE_WORD}' detected!")
                play_chime()
                shared_state["toggle_info"].set()
            elif SPEED_DOWN_WORD in text_lower:
                print(f"Speed down word '{SPEED_DOWN_WORD}' detected!")
                shared_state["replay_speed_factor"][0] *= 1.25 # Slow down by 25%
                print(f"New replay speed: {1/shared_state['replay_speed_factor'][0]:.2f}x")
                play_chime()
            elif SPEED_UP_WORD in text_lower:
                print(f"Speed up word '{SPEED_UP_WORD}' detected!")
                shared_state["replay_speed_factor"][0] /= 1.25 # Speed up by 25%
                print(f"New replay speed: {1/shared_state['replay_speed_factor'][0]:.2f}x")
                play_chime()
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Voice listener thread stopped.")


def put_text_on_frame(frame, text, pos, color=(255, 255, 255), bg_color=(0,0,0), font_scale=1.0, thickness=2):
    """Utility function to draw styled text with a background on a video frame."""
    text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    text_w, text_h = text_size
    x, y = pos
    
    # Adjust position for background rectangle
    bg_x1, bg_y1 = x - 5, y - text_h - 5
    bg_x2, bg_y2 = x + text_w + 5, y + 5
    
    overlay = frame.copy()
    cv2.rectangle(overlay, (bg_x1, bg_y1), (bg_x2, bg_y2), bg_color, -1)
    alpha = 0.6
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)
    return frame

def run_replay(capture_buffer, fps, window_name, width):
    """Handles the replay phase logic, including variable speed."""
    print(f"Starting {REPLAY_DURATION_SECONDS}-second replay phase...")
    shared_state["start_record"].clear()

    for frame in list(capture_buffer):
        if shared_state["start_record"].is_set() or shared_state["exit_app"].is_set():
            print("Command detected. Skipping replay.")
            break

        replay_start_time = time.time()
        
        display_frame = frame.copy()
        
        # Add the replay label with current speed
        speed_percent = (1 / shared_state["replay_speed_factor"][0]) * 100
        replay_text = f"REPLAY ({int(speed_percent)}%)"
        
        # Center the replay text
        text_size, _ = cv2.getTextSize(replay_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        text_x = (width - text_size[0]) // 2
        display_frame = put_text_on_frame(display_frame, replay_text, (text_x, 50), color=(0, 255, 0), font_scale=1.2, thickness=3)

        # Calculate the delay based on the speed factor
        base_frame_delay = 1.0 / fps
        adjusted_delay = base_frame_delay * shared_state["replay_speed_factor"][0]

        cv2.imshow(window_name, display_frame)

        processing_time = time.time() - replay_start_time
        wait_time = max(1, int((adjusted_delay - processing_time) * 1000))

        if cv2.waitKey(wait_time) & 0xFF == ord('q'):
            shared_state["exit_app"].set()
            return False
    return True

def main():
    """Main function to run the capture-replay loop with voice control."""
    print("Starting Instant Replay application...")

    listener_thread = threading.Thread(target=voice_listener, daemon=True)
    listener_thread.start()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Could not open camera at index {CAMERA_INDEX}.")
        return

    # Set camera properties as requested
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Swap width and height for text positioning on rotated frame
    width, height = height, width

    camera_name = get_camera_name(CAMERA_INDEX)
    print(f"Camera feed opened successfully at {width}x{height}, {fps:.2f} FPS.")

    # Get system info for the popup
    p_audio = pyaudio.PyAudio()
    mic_name = p_audio.get_default_input_device_info()['name']
    p_audio.terminate()
    info_text_lines = [
        f"Mic: {mic_name}",
        f"Camera: {camera_name}",
        f"FPS: {fps:.2f}"
    ]

    window_name = 'Instant Replay'
    cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    last_capture_buffer = None
    swing_count = 0
    show_info = False
    
    while not shared_state["exit_app"].is_set():
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break
        
        # Rotate the frame 90 degrees clockwise
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # --- Handle State Changes ---
        if shared_state["toggle_info"].is_set():
            show_info = not show_info
            shared_state["toggle_info"].clear()

        # --- Handle Voice Commands ---
        if shared_state["start_record"].is_set():
            swing_count += 1
            # --- CAPTURE PHASE ---
            print(f"\nStarting {REPLAY_DURATION_SECONDS}-second capture phase...")
            current_capture_buffer = collections.deque()
            start_time = time.time()
            while time.time() - start_time < REPLAY_DURATION_SECONDS:
                ret_cap, frame_cap = cap.read()
                if not ret_cap: break
                
                # Rotate the captured frame as well
                frame_cap = cv2.rotate(frame_cap, cv2.ROTATE_90_COUNTERCLOCKWISE)
                current_capture_buffer.append(frame_cap)
                
                # Draw overlays during capture
                countdown = REPLAY_DURATION_SECONDS - (time.time() - start_time)
                rec_text = f"GRABANDO... ({countdown:.1f}s)"
                
                # Center the recording text
                text_size, _ = cv2.getTextSize(rec_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
                text_x = (width - text_size[0]) // 2
                
                display_frame = put_text_on_frame(frame_cap.copy(), rec_text, (text_x, 50), color=(0,0,255), font_scale=1.2, thickness=3)
                display_frame = put_text_on_frame(display_frame, f"Swing Count: {swing_count}", (20, 50))
                cv2.imshow(window_name, display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    shared_state["exit_app"].set()
                    break
            
            if current_capture_buffer:
                last_capture_buffer = current_capture_buffer
                run_replay(last_capture_buffer, fps, window_name, width)

            # Reset for next listening phase
            shared_state["start_record"].clear()

        elif shared_state["repeat_replay"].is_set():
            if last_capture_buffer:
                run_replay(last_capture_buffer, fps, window_name, width)
            else:
                print("No replay available to repeat.")
                time.sleep(1)
            shared_state["repeat_replay"].clear()

        # --- DRAW OVERLAYS for LISTENING PHASE ---
        display_frame = frame.copy()
        
        # Main instruction text (centered)
        listen_text = f"DIGA '{TRIGGER_WORD.upper()}' U '{REPEAT_TRIGGER_WORD.upper()}'"
        text_size, _ = cv2.getTextSize(listen_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)
        text_x = (width - text_size[0]) // 2
        display_frame = put_text_on_frame(display_frame, listen_text, (text_x, 50), color=(255, 255, 0), font_scale=1.2, thickness=3)
        
        # Swing count
        display_frame = put_text_on_frame(display_frame, f"Swing Count: {swing_count}", (20, 50))
        
        # Last heard command
        last_command = shared_state["last_heard_command"][0]
        if last_command:
            display_frame = put_text_on_frame(display_frame, f"Comando: {last_command}", (20, height - 40), font_scale=0.8)

        # Info popup
        if show_info:
            # Dynamically calculate the position for right-alignment
            font_scale_info = 0.7
            thickness_info = 2
            max_line_width = 0
            for line in info_text_lines:
                line_width, _ = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, font_scale_info, thickness_info)[0]
                if line_width > max_line_width:
                    max_line_width = line_width
            
            # Position menu with a 20px margin from the right edge
            menu_x = width - max_line_width - 30 # 20px margin + 10px padding
            
            for i, line in enumerate(info_text_lines):
                display_frame = put_text_on_frame(display_frame, line, (menu_x, 50 + i * 40), font_scale=font_scale_info, thickness=thickness_info)

        cv2.imshow(window_name, display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            shared_state["exit_app"].set()

    print("Exiting application.")
    cap.release()
    cv2.destroyAllWindows()
    # Wait for the listener thread to finish
    listener_thread.join(timeout=1.0)

if __name__ == '__main__':
    main()
