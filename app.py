from flask import Flask, render_template, request, jsonify
import os
import spotisound1

app = Flask(__name__)

# Define a path for saving downloads (server-side)
DOWNLOADS_FOLDER = os.path.join(os.getcwd(), 'downloads')  # Ensure this folder exists
if not os.path.exists(DOWNLOADS_FOLDER):
    os.makedirs(DOWNLOADS_FOLDER)
	
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_playlist():
    playlist_url = request.form['playlist_url']
    try:
        if "spotify.com" in playlist_url:
            playlist_id = playlist_url.split("/")[-1].split("?")[0]
            spotisound1.download_path = DOWNLOADS_FOLDER  # Update the download path
            spotisound1.download_spotify_playlist(playlist_id)
        elif "soundcloud.com" in playlist_url:
            spotisound1.download_path = DOWNLOADS_FOLDER  # Update the download path
            spotisound1.download_soundcloud_playlist(playlist_url)
        else:
            return jsonify({"success": False, "message": "URL not recognized"}), 400

        return jsonify({"success": True, "message": "Downloaded successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
