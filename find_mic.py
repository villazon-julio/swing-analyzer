import pyaudio

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')

print("\n--------------------------------------------------")
print("Available Audio Input Devices:")
print("--------------------------------------------------")

found_mic = False
for i in range(0, numdevices):
    device_info = p.get_device_info_by_host_api_device_index(0, i)
    if (device_info.get('maxInputChannels')) > 0:
        print(f"  Index: {i}, Name: {device_info.get('name')}")
        found_mic = True

if not found_mic:
    print("No input devices found.")

print("--------------------------------------------------\n")
print("Find your USB microphone in the list above.")
print("Then, open 'golf.py' and set the MICROPHONE_INDEX variable to the correct Index number.")

p.terminate()
