import cv2
import base64
import numpy as np
import time
import threading
import socketio

# Import everything from your main detection logic (you called it tilapiai2c)
from tilapiai2c import (
    preprocess_frame,
    process_frame,
    state,
    lcd_update_thread,
    lcd,
    FRAME_SKIP,
)

sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=5,
    reconnection_delay=1,
    logger=True, 
    engineio_logger=True
)

connected_event = threading.Event()

@sio.event
def connect():
    print("Socket.IO connected")
    connected_event.set()

@sio.event
def disconnect():
    print("Socket.IO disconnected")
    connected_event.clear()

#sio.connect("https://steady-bluejay-meet.ngrok-free.app", transports=["websocket"])
sio.connect("http://e-dust.gl.at.ply.gg:14680", transports=["websocket"])


def encode_frame(frame: np.ndarray) -> str:
    """Encode OpenCV frame to base64 JPEG"""
    _, buffer = cv2.imencode('.jpg', frame)
    return "data:image/jpeg;base64,"+base64.b64encode(buffer).decode('utf-8')

def generate_frames():
    connected_event.wait()
    threading.Thread(target=lcd_update_thread, daemon=True).start()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open camera")

    frame_counter = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_counter += 1
            if frame_counter % FRAME_SKIP != 0:
                continue

            _, buffer = cv2.imencode('.jpg', frame)
            encoded = base64.b64encode(buffer).decode('utf-8')
            try:
                sio.emit('frame', f"data:image/jpeg;base64,{encoded}")
            except socketio.exceptions.BadNamespaceError as e:
                print("Emit failed - not connected:", e)

            #processed_frame = preprocess_frame(frame)
            #annotated_frame = process_frame(processed_frame)

            with state.lock:
                state.frame_count += 1
                elapsed = time.time() - state.start_time
                if elapsed >= 1.0:
                    state.fps = state.frame_count / elapsed
                    state.frame_count = 0
                    state.start_time = time.time()

            time.sleep(0.1)
            yield encode_frame(frame)

    finally:
        cap.release()
        lcd.clear()
        lcd.write_string("Stopped.")

