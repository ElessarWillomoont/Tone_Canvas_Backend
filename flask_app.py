from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_cors import CORS
import os
import soundfile as sf
import yaml
from datetime import datetime

from utils.pitch_processing import process_pitch_file, save_interpolated_data_to_json, generate_sine_wave
from utils.file_parsing import parse_praat_pitch_file
from utils.audio_utils import calculate_times, segment_nonzero_times_and_frequencies, interpolate_pitch_segments

app = Flask(__name__)
CORS(app)  # Enable CORS

corpus_dir = os.path.join(os.path.dirname(__file__), 'corpus')
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
data_base_dir = os.path.join(os.path.dirname(__file__), 'data_base')

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
    if not files:
        return "No wav files found", 404

    pitch_file = os.path.join(corpus_dir, files[current_index].replace('.wav', '.Pitch'))
    if not os.path.exists(pitch_file):
        return "No pitch file found for the current wav file", 404

    target_sample_rate = 100  # Desired sample rate for the output
    new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)

    json_output_path = os.path.join(temp_dir, 'interpolated_pitch_data.json')
    save_interpolated_data_to_json(new_times, interpolated_frequencies, json_output_path)
    
    return send_file(json_output_path, as_attachment=True)

@app.route('/api/get-pitch-audio', methods=['GET'])
def get_pitch_audio():
    global current_index
    if not files:
        return "No wav files found", 404

    pitch_file = os.path.join(corpus_dir, files[current_index].replace('.wav', '.Pitch'))
    if not os.path.exists(pitch_file):
        return "No pitch file found for the current wav file", 404

    target_sample_rate = 44100  # Desired sample rate for the output
    new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)

    sine_wave = generate_sine_wave(interpolated_frequencies, target_sample_rate)
    audio_output_path = os.path.join(temp_dir, 'pitch_only_audio_manually.wav')
    sf.write(audio_output_path, sine_wave, target_sample_rate)
    
    return send_file(audio_output_path, as_attachment=True)

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
    global current_data_file, current_index

    if not current_data_file:
        return jsonify(error="No current data file. Set user ID first."), 400

    trace = request.json.get('trace')
    if not trace:
        return jsonify(error="Trace data is required."), 400

    trace_start = trace.get('trace_start')
    trace_body = trace.get('trace_body')
    trace_end = trace.get('trace_end')

    if not (trace_start and trace_body and trace_end):
        return jsonify(error="Trace data must include trace_start, trace_body, and trace_end."), 400

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_file_name = files[current_index] if current_index < len(files) else "unknown"

    with open(current_data_file, 'a') as yaml_file:
        yaml.dump({
            f"trace_{current_time}": {
                "file_name": current_file_name,
                "trace_start": trace_start,
                "trace_body": [
                    {
                        "timestamp": point["timestamp"],
                        "pitch": point["pitch"],
                        "x": point["x"],
                        "y": point["y"]
                    } for point in trace_body
                ],
                "trace_end": trace_end
            }
        }, yaml_file)

    return jsonify(message="Trace data appended to YAML file."), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
