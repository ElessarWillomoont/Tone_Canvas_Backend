import os
from flask import send_file, jsonify
import soundfile as sf

from utils.pitch_processing import process_pitch_file, save_interpolated_data_to_json, generate_sine_wave

def handle_get_pitch_json(files, current_index, temp_dir, corpus_dir):
    if not files:
        print("[❌] 没有音频文件可用")
        return "No wav files found", 404

    wav_file = files[current_index]
    pitch_file = os.path.join(corpus_dir, wav_file.replace('.wav', '.Pitch'))

    print(f"\n🎧 正在处理音频文件: {wav_file}")
    print(f"🎯 期望的 Pitch 文件路径: {pitch_file}")

    if not os.path.exists(pitch_file):
        print(f"[⚠️] Pitch 文件不存在: {pitch_file}")
        return "No pitch file found for the current wav file", 404

    try:
        target_sample_rate = 100
        print(f"📐 开始处理 pitch 文件，目标采样率: {target_sample_rate}")
        new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)
        print(f"✅ Pitch 处理成功，数据点数: {len(new_times)}")

        json_output_path = os.path.join(temp_dir, 'interpolated_pitch_data.json')
        save_interpolated_data_to_json(new_times, interpolated_frequencies, json_output_path)
        print(f"📦 JSON 文件保存成功: {json_output_path}")

        return send_file(json_output_path, as_attachment=True)

    except Exception as e:
        print(f"[💥] 处理 pitch 文件失败: {e}")
        return jsonify(error=f"Error processing pitch file: {str(e)}"), 500


def handle_get_pitch_audio(files, current_index, temp_dir, corpus_dir):
    if not files:
        print("[❌] 没有音频文件可用")
        return "No wav files found", 404

    wav_file = files[current_index]
    pitch_file = os.path.join(corpus_dir, wav_file.replace('.wav', '.Pitch'))

    print(f"\n🔊 正在生成 pitch 音频: {wav_file}")
    print(f"🎯 期望的 Pitch 文件路径: {pitch_file}")

    if not os.path.exists(pitch_file):
        print(f"[⚠️] Pitch 文件不存在: {pitch_file}")
        return "No pitch file found for the current wav file", 404

    try:
        target_sample_rate = 44100
        print(f"🎵 开始生成正弦波，目标采样率: {target_sample_rate}")
        new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)
        print(f"✅ Pitch 数据加载成功，数据点数: {len(new_times)}")

        sine_wave = generate_sine_wave(interpolated_frequencies, target_sample_rate)
        print(f"🎼 正弦波生成完毕，总样本数: {len(sine_wave)}")

        audio_output_path = os.path.join(temp_dir, 'pitch_only_audio_manually.wav')
        sf.write(audio_output_path, sine_wave, target_sample_rate)
        print(f"📁 音频文件保存成功: {audio_output_path}")

        return send_file(audio_output_path, as_attachment=True)

    except Exception as e:
        print(f"[💥] 生成 pitch 音频失败: {e}")
        return jsonify(error=f"Error generating pitch audio: {str(e)}"), 500
