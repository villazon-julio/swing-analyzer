# GOLF SWING INSTANT REPLAY
#
# This application captures a 15-second clip from a USB-connected camera
# and then immediately plays it back in a loop. It's designed for analyzing
# repetitive motions like a golf swing.
#
# Created by Gemini
#

import cv2
import time
import collections
import numpy as np

# --- Configuration -----------------------------------------------------------
# You may need to change these values based on your setup.

# The index of your camera. 0 is usually the default built-in webcam.
# Try 1, 2, etc., if 0 doesn't work for your Canon camera.
CAMERA_INDEX = 0

# Duration of the capture and replay in seconds.
REPLAY_DURATION_SECONDS = 6

# --- End of Configuration ----------------------------------------------------


def put_text_on_frame(frame, text, color):
    """Utility function to draw styled text on a video frame."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.2
    thickness = 3
    # Get text size to position it at the top center
    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = text_size[1] + 20

    # Add a semi-transparent background rectangle for better readability
    overlay = frame.copy()
    cv2.rectangle(overlay, (text_x - 10, text_y - text_size[1] - 10),
                  (text_x + text_size[0] + 10, text_y + 10), (0, 0, 0), -1)
    alpha = 0.6
    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

    # Put the text on the frame
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)
    return frame


def main():
    """Main function to run the capture-replay loop."""
    print("Starting Instant Replay application...")
    print("Press 'q' in the video window to quit.")

    # Initialize video capture from the specified camera
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print(f"Error: Could not open camera at index {CAMERA_INDEX}.")
        print("Please ensure your camera is connected and the correct CAMERA_INDEX is set.")
        print("If using a Canon camera, make sure the EOS Webcam Utility is installed and running.")
        return

    # Get camera properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    # If FPS is not reported by the camera, default to 30
    if fps == 0:
        print("Warning: Camera did not report FPS. Defaulting to 30.")
        fps = 30.0

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera feed opened successfully at {width}x{height}, {fps:.2f} FPS.")

    window_name = 'Instant Replay'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    # Resize window for better viewing on larger screens
    cv2.resizeWindow(window_name, 1280, 720)


    # Main application loop
    while True:
        # -----------------------------------------------------------------
        # 1. CAPTURE PHASE
        # -----------------------------------------------------------------
        print(f"\nStarting {REPLAY_DURATION_SECONDS}-second capture phase...")
        capture_buffer = collections.deque()
        start_time = time.time()

        while time.time() - start_time < REPLAY_DURATION_SECONDS:
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to grab frame from camera.")
                break

            # Add the frame to our buffer
            capture_buffer.append(frame)

            # Display the live feed with a "RECORDING" indicator
            display_frame = frame.copy()
            elapsed_time = time.time() - start_time
            countdown = REPLAY_DURATION_SECONDS - elapsed_time
            rec_text = f"RECORDING... ({countdown:.1f}s)"
            display_frame = put_text_on_frame(display_frame, rec_text, (0, 0, 255)) # Red color

            cv2.imshow(window_name, display_frame)

            # Check for quit key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                print("Application terminated by user.")
                return

        if not capture_buffer:
            print("Capture buffer is empty. Exiting.")
            break

        # -----------------------------------------------------------------
        # 2. REPLAY PHASE
        # -----------------------------------------------------------------
        print(f"Starting {REPLAY_DURATION_SECONDS}-second replay phase...")
        
        # Calculate the delay needed between frames for accurate playback speed
        frame_delay = 0.5 / fps

        for frame in list(capture_buffer):
            replay_start_time = time.time()
            
            # Display the buffered frame with a "REPLAY" indicator
            display_frame = frame.copy()
            display_frame = put_text_on_frame(display_frame, "REPLAY", (0, 255, 0)) # Green color

            cv2.imshow(window_name, display_frame)

            # Wait for the calculated delay, minus processing time, to maintain FPS
            # This ensures the replay lasts for the correct duration
            processing_time = time.time() - replay_start_time
            wait_time = max(1, int((frame_delay - processing_time) * 1000))
            
            if cv2.waitKey(wait_time) & 0xFF == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                print("Application terminated by user.")
                return

    # Clean up resources
    print("Exiting application.")
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
