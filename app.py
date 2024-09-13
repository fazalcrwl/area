from flask import Flask, request, send_file, jsonify
import os
from uuid import UUID
from flask_cors import CORS
from Video_creation import ConstructVideo
from moviepy.config import change_settings
import shutil

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

@app.route('/get_video', methods=['POST'])
def get_video():

    uuid = request.form.get('uuid')
    
    if not uuid:
        return jsonify({"error": "UUID and output directory are required."}), 400

    ConstructVideo(uuid)
    video_path = f"tmp/{uuid}/save/final_video.mp4"

    return send_file(video_path, as_attachment=True)



@app.route('/remove_video_uuid', methods=['POST'])
def remove_video_uuid():
    uuid = request.form.get('uuid')
    
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