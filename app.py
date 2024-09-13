from flask import Flask, request, send_file, jsonify
import os
from uuid import UUID
from flask_cors import CORS
from Video_creation import ConstructVideo
from moviepy.config import change_settings
import shutil
import threading

change_settings(change_settings({"IMAGEMAGICK_BINARY": "/usr/local/bin/magick"}))
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return '''
        <h1>Video Fetcher</h1>
        <form action="/get_video" method="post">
            <label for="uuid">Enter UUID:</label>
            <input type="text" id="uuid" name="uuid" required><br>
            <button type="submit">Submit</button>
        </form>
        <h1>Deleat Video</h1>
        <form action="/remove_video_uuid" method="post">
            <label for="uuid">Enter UUID:</label>
            <input type="text" id="uuid" name="uuid" required><br>
            <button type="submit">Submit</button>
        </form>
    '''

def async_construct_video(uuid):
    video = ConstructVideo(uuid)    
    # call the end point 


@app.route('/get_video', methods=['POST'])
def get_video():

    uuid = request.form.get('uuid')
    
    if not uuid:
        return jsonify({"error": "UUID is required."}), 400

    # Start the video construction process in a new thread
    video_thread = threading.Thread(target=async_construct_video, args=(uuid,))
    video_thread.start()

    # Return a response that the process has started
    return jsonify({"message": f"Video construction process for UUID {uuid} has started."}), 202




@app.route('/remove_video_uuid', methods=['POST'])
def remove_video_uuid():

    uuid = request.form.get('uuid')
    key = request.form.get('key')
    
    if not (key == '8ce1122516288b1029ba21fd0718925d793ccc91e01bd0bac55b0323953887ba1f16'):
        return jsonify({"error": "Invalid Key"}), 404

    if not uuid:
        return jsonify({"error": "UUID is required."}), 400
    
    try:
        UUID(uuid)
    except ValueError:
        return jsonify({"error": "Invalid UUID format."}), 400

    video_path = f"tmp/{uuid}"

    if os.path.exists(video_path):
        shutil.rmtree(video_path)
        return jsonify({"message": "Video removed successfully."})
    else:
        return jsonify({"error": "Video file not found."}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)