import subprocess, os
from flask import request, jsonify
from .config import VIDEO_FOLDER

def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing URL'}), 400

    os.makedirs(VIDEO_FOLDER, exist_ok=True)

    try:
        result = subprocess.run([
            'yt-dlp',
            '-S', 'res:1440,fps',
            '-t', 'mp4',
            '-o', os.path.join(VIDEO_FOLDER, '%(title)s.%(ext)s'),
            url
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({'error': 'Download failed', 'details': result.stderr}), 500

        return jsonify({'status': 'Download successful', 'output': result.stdout})
    except Exception as e:
        return jsonify({'error': str(e)}), 500