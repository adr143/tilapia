import cv2
import base64
import numpy as np
import time
import threading

# Import everything from your main detection logic (you called it tilapiai2c)
from tilapiai2c import (
    preprocess_frame,
    process_frame,
    state,
    lcd_update_thread,
    lcd,
    FRAME_SKIP,
)

def encode_frame(frame: np.ndarray) -> str:
    """Encode OpenCV frame to base64 JPEG"""
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode('utf-8')

def generate_frames():
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

            processed_frame = preprocess_frame(frame)
            annotated_frame = process_frame(processed_frame)

            with state.lock:
                state.frame_count += 1
                elapsed = time.time() - state.start_time
                if elapsed >= 1.0:
                    state.fps = state.frame_count / elapsed
                    state.frame_count = 0
                    state.start_time = time.time()

            yield encode_frame(annotated_frame)

    finally:
        cap.release()
        lcd.clear()
        lcd.write_string("Stopped.")

