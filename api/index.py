import os
import re
import glob
import time
import uuid
import threading
from flask import Flask, request, jsonify, send_from_directory
import yt_dlp

app = Flask(__name__)

DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "/app/downloads")
MAX_FILE_AGE = int(os.environ.get("MAX_FILE_AGE", "3600"))
MAX_DURATION = int(os.environ.get("MAX_DURATION", "7200"))

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

YOUTUBE_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$",
    re.IGNORECASE
)


def valid_youtube_url(url):
    if not url:
        return False

    url = url.strip()

    if not YOUTUBE_REGEX.match(url):
        return False

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url


def cleanup_old_files():
    while True:
        try:
            now = time.time()

            for path in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
                try:
                    if os.path.isfile(path):
                        age = now - os.path.getmtime(path)

                        if age > MAX_FILE_AGE:
                            os.remove(path)

                except Exception:
                    pass

        except Exception:
            pass

        time.sleep(300)


threading.Thread(
    target=cleanup_old_files,
    daemon=True
).start()


def get_common_options():
    return {
        "quiet": True,
        "no_warnings": True,

        # Allow yt-dlp to use the JS runtime installed in Docker
        "js_runtimes": {
            "deno": {}
        },

        # Don't download playlists accidentally
        "noplaylist": True,

        # Network
        "socket_timeout": 30,
        "retries": 3,

        # Avoid keeping partial files
        "continuedl": False,

        # Security
        "restrictfilenames": True,

        # FFmpeg
        "ffmpeg_location": "/usr/bin/ffmpeg",
    }


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "service": "YouTube Downloader API",
        "version": "1.0",
        "endpoint": "/api/download?url=YOUTUBE_URL"
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "online"
    })


@app.route("/api/info", methods=["GET"])
def info():

    url = request.args.get("url", "").strip()

    if not valid_youtube_url(url):
        return jsonify({
            "success": False,
            "error": "Invalid YouTube URL"
        }), 400

    try:

        options = get_common_options()

        options["skip_download"] = True

        with yt_dlp.YoutubeDL(options) as ydl:

            data = ydl.extract_info(url, download=False)

            duration = data.get("duration")

            if duration and duration > MAX_DURATION:
                return jsonify({
                    "success": False,
                    "error": "Video is too long"
                }), 400

            return jsonify({
                "success": True,
                "id": data.get("id"),
                "title": data.get("title"),
                "thumbnail": data.get("thumbnail"),
                "duration": duration,
                "uploader": data.get("uploader"),
                "webpage_url": data.get("webpage_url")
            })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/download", methods=["GET"])
def download():

    url = request.args.get("url", "").strip()

    if not valid_youtube_url(url):
        return jsonify({
            "success": False,
            "error": "Invalid YouTube URL"
        }), 400

    job_id = uuid.uuid4().hex

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{job_id}.%(ext)s"
    )

    options = get_common_options()

    options.update({

        # Best available video + best audio
        # FFmpeg merges them into MP4
        "format": (
            "bestvideo[ext=mp4]+bestaudio[ext=m4a]/"
            "best[ext=mp4]/best"
        ),

        "outtmpl": output_template,

        "merge_output_format": "mp4",

        "postprocessors": [],

    })

    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            info_data = ydl.extract_info(
                url,
                download=False
            )

            duration = info_data.get("duration")

            if duration and duration > MAX_DURATION:
                return jsonify({
                    "success": False,
                    "error": "Video exceeds maximum allowed duration"
                }), 400

            title = info_data.get("title")
            thumbnail = info_data.get("thumbnail")

            # Download
            ydl.download([url])

        # Find generated file
        files = glob.glob(
            os.path.join(DOWNLOAD_DIR, f"{job_id}.*")
        )

        files = [
            f for f in files
            if not f.endswith(".part")
            and not f.endswith(".ytdl")
        ]

        if not files:

            return jsonify({
                "success": False,
                "error": "Download completed but file was not found"
            }), 500

        filepath = files[0]

        filename = os.path.basename(filepath)

        base_url = request.host_url.rstrip("/")

        download_url = (
            f"{base_url}/files/{filename}"
        )

        return jsonify({

            "success": True,

            "title": title,

            "thumbnail": thumbnail,

            "video": download_url,

            "filename": filename

        })

    except Exception as e:

        # Remove failed files
        for f in glob.glob(
            os.path.join(DOWNLOAD_DIR, f"{job_id}.*")
        ):
            try:
                os.remove(f)
            except Exception:
                pass

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/files/<path:filename>", methods=["GET"])
def files(filename):

    return send_from_directory(
        DOWNLOAD_DIR,
        filename,
        as_attachment=True
    )


if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", "8080")
    )

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )
