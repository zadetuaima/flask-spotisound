import spotipy
import os
import json
import re
import requests
from spotipy.oauth2 import SpotifyOAuth
from sclib import SoundcloudAPI, Track, Playlist
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
import yt_dlp

# Helper functions
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def embed_thumbnail_in_mp3(mp3_file_path, thumbnail_file_path):
    if os.path.exists(mp3_file_path) and os.path.exists(thumbnail_file_path):
        audio = MP3(mp3_file_path, ID3=ID3)
        with open(thumbnail_file_path, 'rb') as img_file:
            audio.tags.add(
                APIC(
                    encoding=0,  # UTF-8
                    mime='image/jpeg',
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=img_file.read()
                )
            )
        audio.save()
        os.remove(thumbnail_file_path)

def add_metadata(file_path, artist, album, genre, originaldate):
    if os.path.exists(file_path):
        audio = MP3(file_path, ID3=EasyID3)
        audio['artist'] = artist
        audio['album'] = album
        audio['genre'] = genre
        audio['originaldate'] = originaldate
        audio.save()

def add_metadata_sound(file_path, artist):
    if os.path.exists(file_path):
        audio = MP3(file_path, ID3=EasyID3)
        audio['artist'] = artist
        audio.save()

with open("key.json", "r") as file:
    api_tokens = json.load(file)

client_secret = api_tokens['client_secret']
client_id = api_tokens['client_id']
redirectURI = api_tokens['redirect']

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirectURI,
                                               scope="playlist-read-private"))

# SoundCloud setup
with open("soundcloud_key.json", "r") as sound_file:
    sound_api_tokens = json.load(sound_file)

sound_id = sound_api_tokens['client_id']
sound_api = SoundcloudAPI(client_id=sound_id)

# Path to save downloads
download_path = r'C:\Users\Zade\Downloads\Test'

# Spotify download logic
def download_from_youtube(query, download_path):
    sanitized_query = sanitize_filename(query)
    mp3_file_path = os.path.join(download_path, f"{sanitized_query}.mp3")
    thumbnail_file_path = os.path.join(download_path, f"{sanitized_query}.jpg")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            },
            {
                'key': 'EmbedThumbnail',
            },
        ],
        'writethumbnail': True,
        'outtmpl': os.path.join(download_path, f"{sanitized_query}.%(ext)s"),
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"Downloading {query}...")
            ydl.download([f"ytsearch:{query}"])

            if os.path.exists(thumbnail_file_path):
                embed_thumbnail_in_mp3(mp3_file_path, thumbnail_file_path)
        except Exception as e:
            print(f"Error downloading {query}: {e}")

def download_spotify_playlist(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    for item in tracks:
        track = item['track']
        track_name = sanitize_filename(f"{track['artists'][0]['name']} - {track['name']}")
        artist = track['artists'][0]['name']
        album = track['album']['name']
        artist_id = track['artists'][0]['id']
        artist_info = sp.artist(artist_id)
        genre = artist_info["genres"]
        date = track['album']['release_date']
        originaldate = date.split('-')[0]

        download_from_youtube(track_name, download_path)

        file_path = os.path.join(download_path, f"{track_name}.mp3")
        add_metadata(file_path, artist, album, genre, originaldate)

# SoundCloud download logic
def download_soundcloud_playlist(url):
    playlist = sound_api.resolve(url)

    if isinstance(playlist, Playlist):
        for track in playlist.tracks:
            if isinstance(track, Track):
                track_name = sanitize_filename(f"{track.artist} - {track.title}.mp3")
                file_path = os.path.join(download_path, track_name)

                with open(file_path, 'wb+') as file:
                    track.write_mp3_to(file)

                if track.artwork_url:
                    high_res_artwork_url = track.artwork_url.replace("-large", "-t500x500")
                    response = requests.get(high_res_artwork_url)
                    if response.status_code == 200:
                        audio = MP3(file_path, ID3=ID3)
                        audio.tags.add(
                            APIC(
                                encoding=0,
                                mime='image/jpeg',
                                type=3,
                                desc='Cover',
                                data=response.content
                            )
                        )
                        audio.save()

                add_metadata_sound(file_path, track.artist)
                print(f"Track downloaded: {track_name}")
