
# import eventlet
# eventlet.monkey_patch()  # Add this line at the top

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread
import time
from tilapiai2c import state
import numpy as np

from tracker import generate_frames

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

@app.route('/')
def index():
    return render_template('index.html')

def stream_video():
    for encoded_frame in generate_frames():
        socketio.emit('video_frame', {'image': encoded_frame})
        time.sleep(0.03)  # ~30 fps

def emit_counts():
    while True:
        with state.lock:
            last_id = state.crossed_objects[-1][0] if state.crossed_objects else "--"
            last_dir = state.crossed_objects[-1][2] if state.crossed_objects else "--"

            data = {
                'left_to_right': int(state.left_to_right_count),
                'right_to_left': int(state.right_to_left_count),
                'fps': round(float(state.fps), 1),
                'last_object': {
                    'id': int(last_id) if isinstance(last_id, (np.integer, int)) else str(last_id),
                    'dir': str(last_dir),
                }
            }
        try:
            socketio.emit('count_update', data)
        except Exception as e:
            print(f"[EMIT ERROR] {e}")  # Make this visible
        time.sleep(0.5)


@socketio.on('connect')
def on_connect():
    print("Client connected")

if __name__ == '__main__':
    Thread(target=stream_video, daemon=True).start()
    Thread(target=emit_counts, daemon=True).start()
    socketio.run(app, host="0.0.0.0", port=5001, allow_unsafe_werkzeug=True)

