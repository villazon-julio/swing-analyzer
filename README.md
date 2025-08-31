Golf Swing Instant Replay
A voice-controlled instant replay application designed for analyzing activities like a golf swing. The application runs offline on a Raspberry Pi 5, using a connected USB camera and microphone to provide immediate visual feedback.

The video feed is displayed in fullscreen and rotated 90 degrees for a vertical orientation, ideal for capturing a full swing.

Features
Offline Voice Control: Uses the Vosk speech recognition engine to run completely offline. All commands are in Spanish.

Instant Replay: Capture a short video clip with a voice command and watch it back immediately.

Variable Speed Playback: Slow down or speed up the replay in real-time to analyze movement in detail.

Persistent Speed: The selected replay speed is remembered for subsequent replays.

On-Screen Information: A toggleable menu displays details about the connected camera, microphone, and current FPS.

Swing Counter: Keep track of the number of swings recorded during a session.

Audible Feedback: A chime sound confirms when a voice command has been successfully recognized.

Fullscreen & Rotated View: The application starts in fullscreen with a 90-degree rotated view for a better vertical perspective.

Voice Commands
okay: Starts a new 4-second recording.

otra: Replays the last recorded swing.

lento: Slows down the current or next replay.

rápido: Speeds up the current or next replay.

menu: Toggles the visibility of the information panel.

salir: Exits the application.

Hardware Requirements
Raspberry Pi 5

A microSD card (16GB+) with Raspberry Pi OS (64-bit)

USB Webcam (e.g., Canon R6 Mark II)

USB Microphone

Power supply and display for the Raspberry Pi

Setup and Installation on Raspberry Pi
Update System: Open a terminal and ensure your Raspberry Pi is up to date:

sudo apt update
sudo apt upgrade -y

Install All Dependencies: Run this single command to install the required system libraries and Python packages:

sudo apt install -y python3-pyaudio portaudio19-dev libopenjp2-7 && pip install opencv-python vosk

Download the Project Files: Place the golf.py script and the chime.wav sound file into a folder on your Pi, for example, /home/pi/swing-analyzer/.

Download the Vosk Spanish Model:

Download the model from here.

Unzip the file.

Place the resulting vosk-model-small-es-0.42 folder inside your project directory (/home/pi/swing-analyzer/).

Your final folder structure should look like this:

/home/pi/swing-analyzer/
├── golf.py
├── chime.wav
└── vosk-model-small-es-0.42/

Usage
You can run the application directly from the terminal or create a convenient desktop shortcut.

Running from Terminal

Navigate to your project directory:

cd /home/pi/swing-analyzer

Run the script:

python golf.py

Creating a Desktop Shortcut (Recommended)

Open a terminal and create a new shortcut file with the nano editor:

nano /home/pi/Desktop/SwingReplay.desktop

Paste the following configuration into the editor:

[Desktop Entry]
Version=1.0
Name=Swing Replay
Comment=Instant replay for golf swing analysis
Exec=python /home/pi/swing-analyzer/golf.py
Icon=/usr/share/icons/Adwaita/48x48/apps/camera-web.png
Terminal=false
Type=Application

Save and exit by pressing Ctrl+X, then Y, then Enter.

Make the shortcut executable:

chmod +x /home/pi/Desktop/SwingReplay.desktop

You can now launch the application by double-clicking the "Swing Replay" icon on your desktop.

