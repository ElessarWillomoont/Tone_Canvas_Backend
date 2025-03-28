from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import yaml
from datetime import datetime

from utils.pitch_processing import process_pitch_file, save_interpolated_data_to_json, generate_sine_wave
from utils.file_parsing import parse_praat_pitch_file
from utils.audio_utils import calculate_times, segment_nonzero_times_and_frequencies, interpolate_pitch_segments
from utils.pitch_handling import handle_get_pitch_json, handle_get_pitch_audio
from utils.trace_handling import handle_send_trace, handle_send_button_log

app = Flask(__name__)

# Enable CORS with specific configuration
CORS(app, resources={r"/api/*": {"origins": ["http://100.65.232.106:3000", " https://740d-88-173-177-226.ngrok-free.app"]}})

corpus_dir = os.path.join(os.path.dirname(__file__), 'corpus')
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
data_base_dir = os.path.join(os.path.dirname(__file__), 'data_base')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

if not os.path.exists(data_base_dir):
    os.makedirs(data_base_dir)

files = [f for f in os.listdir(corpus_dir) if f.endswith('.wav')]
current_index = 0
user_id = None
current_data_file = None

@app.route('/api/get-wav-file', methods=['GET'])
def get_wav_file():
    global current_index
    if not files:
        return "No wav files found", 404

    file_to_play = files[current_index]
    return send_from_directory(corpus_dir, file_to_play)

@app.route('/api/switch-wav-file', methods=['POST'])
def switch_wav_file():
    global current_index
    current_index = (current_index + 1) % len(files)
    return jsonify(currentIndex=current_index)

@app.route('/api/get-icon/<filename>', methods=['GET'])
def get_icon(filename):
    return send_from_directory(icons_dir, filename)

@app.route('/api/get-pitch-json', methods=['GET'])
def get_pitch_json():
    global current_index
    return handle_get_pitch_json(files, current_index, temp_dir, corpus_dir)

@app.route('/api/get-pitch-audio', methods=['GET'])
def get_pitch_audio():
    global current_index
    return handle_get_pitch_audio(files, current_index, temp_dir, corpus_dir)

@app.route('/api/get-file-name', methods=['GET'])
def get_file_name():
    global current_index
    if not files:
        return jsonify(error="No wav files found"), 404

    file_name = files[current_index]
    return jsonify(fileName=file_name)

@app.route('/api/send-user-id', methods=['POST'])
def send_user_id():
    global user_id, current_data_file

    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify(error="User ID is required"), 400

    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    user_file_path = os.path.join(data_base_dir, f"{user_id}.yaml")

    if os.path.exists(user_file_path):
        current_data_file = user_file_path
    else:
        new_file_name = f"{user_id}_{current_time}.yaml"
        current_data_file = os.path.join(data_base_dir, new_file_name)
        with open(current_data_file, 'w') as yaml_file:
            yaml.dump({"user_id": user_id, "created_at": current_time}, yaml_file)

    return jsonify(message=f"Current data file set to: {current_data_file}"), 201

@app.route('/api/send-trace', methods=['POST'])
def send_trace():
    global current_index, current_data_file
    trace = request.json.get('trace')
    return handle_send_trace(trace, current_index, files, current_data_file)

@app.route('/api/send-button-log', methods=['POST'])
def send_button_log():
    global current_data_file
    button_name = request.json.get('button_name')
    return handle_send_button_log(button_name, current_data_file)

@app.route('/api/get-progress', methods=['GET'])
def get_progress():
    global current_index

    total_files = len(files)

    return jsonify({
        "total_files": total_files,
        "current_index": current_index
    }), 200

@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    global current_data_file, user_id

    if "audio" not in request.files:
        return jsonify(error="No audio file provided"), 400
    
    if not user_id or not current_data_file:
        return jsonify(error="User ID and data file are required before uploading"), 400

    file = request.files["audio"]
    if file.filename == '':
        return jsonify(error="Empty filename"), 400
    
    # 确定用户目录
    user_upload_dir = os.path.join(UPLOAD_FOLDER, user_id)
    os.makedirs(user_upload_dir, exist_ok=True)

    # 计算音频序号
    existing_files = [f for f in os.listdir(user_upload_dir) if f.endswith(".wav") or f.endswith(".mp3")]
    file_index = len(existing_files) + 1  # 递增序号

    # 生成文件名
    current_time = datetime.now().strftime("%Y%m%d_%H%M")
    base_filename = f"{user_id}_{os.path.basename(current_data_file).replace('.yaml', '')}_{file_index}"
    wav_filename = f"{base_filename}.wav"
    mp3_filename = f"{base_filename}.mp3"

    # 保存 WAV 文件
    wav_path = os.path.join(user_upload_dir, wav_filename)
    file.save(wav_path)

    return jsonify({
        "message": "Upload successful",
        "wav_file": wav_filename,
    }), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
