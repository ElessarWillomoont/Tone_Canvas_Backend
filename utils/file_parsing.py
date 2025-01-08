def parse_praat_pitch_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    frames_data = []
    current_frame = None
    x1, dx = None, None

    for line in content:
        line = line.strip()
        if line.startswith('x1 ='):
            x1 = float(line.split('=')[1].strip())
        elif line.startswith('dx ='):
            dx = float(line.split('=')[1].strip())
        elif line.startswith('frames [') and 'frames []' not in line:
            if current_frame is not None:
                frames_data.append(current_frame)
            current_frame = {'frame': int(line.split('[')[1].split(']')[0]), 'candidates': []}
        elif line.startswith('frequency ='):
            candidate = {'frequency': float(line.split('=')[1].strip())}
            current_frame['candidates'].append(candidate)
        elif line.startswith('strength ='):
            current_frame['candidates'][-1]['strength'] = float(line.split('=')[1].strip())

    if current_frame is not None:
        frames_data.append(current_frame)
    
    return frames_data, x1, dx
