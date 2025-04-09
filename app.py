
# import eventlet
# eventlet.monkey_patch()  # Add this line at the top

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from threading import Thread
import time
from tilapiai2c import state
import numpy as np

from tracker import generate_frames, sio

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

last_frame_time = None
current_fps = 0.0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reset_count', methods=['POST'])
def reset_count():
    with state.lock:
        state.left_to_right = 0
    return jsonify({'message': 'Count reset to 0'}), 200

def stream_video():
    for encoded_frame in generate_frames():
        socketio.emit('video_frame', {'image': encoded_frame})
        time.sleep(0.03)  # ~30 fps

#@sio.on('processed_frame')
#def on_processed_frame(data):
#    with state.lock:
#        state.left_to_right = data['count']
#        socketio.emit('video_frame', {'image': data['frame']})

#@sio.on('processed_frame')
#def on_processed_frame(data):
#    global current_frame, last_frame_time
#    with state.lock:
#        now = time.time()
#        
        # Calculate FPS
#        if last_frame_time is not None:
#            time_diff = now - last_frame_time
#            if time_diff > 0:
#                currently_fps = 1.0 / time_diff
                # Optional: smoothing FPS (simple moving average)
#                current_fps = (current_fps * 0.9) + (currently_fps * 0.1)
#        
#        last_frame_time = now  # update timestamp
        
        # Update your state with incoming data
#        state.left_to_right = data['count']
        
        # Emit frame and FPS
#        socketio.emit('video_frame', {
#            'image': data['frame'],
#            'fps': round(current_fps, 2)  # send FPS rounded to 2 decimal places
#        })

#sio.connect("https://steady-bluejay-meet.ngrok-free.app", transports=["websocket"])
#sio.connect("http://e-dust.gl.at.ply.gg:14680", transports=["websocket"])

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

