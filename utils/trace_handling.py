import yaml
from datetime import datetime
from flask import jsonify

def handle_send_trace(trace, current_index, files, current_data_file):
    if not current_data_file:
        return jsonify(error="No current data file. Set user ID first."), 400

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

def handle_send_button_log(button_name, current_data_file):
    if not current_data_file:
        return jsonify(error="No current data file. Set user ID first."), 400

    if not button_name:
        return jsonify(error="Button name is required."), 400

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

    with open(current_data_file, 'a') as yaml_file:
        yaml.dump({
            "button_logs": [{
                "button_name": button_name,
                "timestamp": current_time
            }]
        }, yaml_file)

    return jsonify(message="Button log appended to YAML file."), 201
