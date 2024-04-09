# import cv2
# import base64
# import numpy as np
# import socketio
# import eventlet
# from datetime import datetime

# import cv2
# import mediapipe as mp
# import time


import cv2
import base64
import numpy as np
import socketio
import eventlet
from flask import Flask
from blink_detector import BlinkDetector

# Initialize Flask app and Socket.IO server
app = Flask(__name__)
sio = socketio.Server(cors_allowed_origins='*')

# Attach Socket.IO server to Flask app
app = socketio.WSGIApp(sio, app)

# Initialize the BlinkDetector or any other required setup
detector = BlinkDetector()

# Define Socket.IO event handlers
@sio.on('connect')
def connect(sid, environ):
    print('Connected', sid)

@sio.on('disconnect')
def disconnect(sid):
    print('Disconnected', sid)

@sio.on('description')
def desc(sid,data):
    # sio.emit('description', data)
    print("desc something",data)

@sio.on('frame')
def process_frame(sid, data):
    # Convert base64 image to numpy array
    img_bytes = base64.b64decode(data.split(',')[1])
    nparr = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    # print("                           dwaWDWD")
    # Process the frame and detect blinks (example)
    detector.detect_blinks(frame)
    if detector.toSend:
        # Notify clients or perform any action upon blink detection
        # print("Blink : ",detector.returnLetter())
        letter=detector.dec_let
        # print("letter:::::::::::::              ",letter)
        sio.emit('timestamp', {'timestamp': letter}, room=sid)  
        detector.toSend=False
        # detector.hasBlinked=False  
    # else:
    #     sio.emit('timestamp', {'timestamp': ""}, room=sid)
    # desc(sid,detector.returnLetter())

    # Further processing or handling of the frame data

    cv2.imshow('Processed Frame', frame)
    # Display the processed frame
    cv2.waitKey(1)


# Define other routes or functions as needed

    # Start the server using Eventlet
eventlet.wsgi.server(eventlet.listen(('localhost', 3001)), app)