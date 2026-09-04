from flask import Flask, request, jsonify
import yt_dlp
import re

app = Flask(__name__)


def valid_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/|live/)|youtu\.be/)[\w-]+"
    return bool(re.match(pattern, url))


@app.route("/api/download", methods=["GET"])
def download():

    url = request.args.get("url")

    if not url:
        return jsonify({
            "success": False,
            "error": "Missing url"
        }), 400

    if not valid_youtube_url(url):
        return jsonify({
            "success": False,
            "error": "Invalid YouTube URL"
        }), 400

    try:

        # استخراج معلومات الفيديو
        info_options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(info_options) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get("formats", [])

        # --------------------------------
        # أفضل فيديو
        # --------------------------------

        video_formats = [
            f for f in formats
            if f.get("vcodec") != "none"
            and f.get("url")
        ]

        video_formats.sort(
            key=lambda f: (
                f.get("height") or 0,
                f.get("tbr") or 0
            ),
            reverse=True
        )

        best_video = video_formats[0] if video_formats else None

        # --------------------------------
        # أفضل صوت
        # --------------------------------

        audio_formats = [
            f for f in formats
            if f.get("acodec") != "none"
            and f.get("vcodec") == "none"
            and f.get("url")
        ]

        audio_formats.sort(
            key=lambda f: (
                f.get("abr") or 0,
                f.get("tbr") or 0
            ),
            reverse=True
        )

        best_audio = audio_formats[0] if audio_formats else None

        return jsonify({

            "success": True,

            "id": info.get("id"),

            "title": info.get("title"),

            "thumbnail": info.get("thumbnail"),

            "description": info.get("description"),

            "duration": info.get("duration"),

            "width": info.get("width"),

            "height": info.get("height"),

            "video": {
                "url": best_video.get("url") if best_video else None,
                "format_id": best_video.get("format_id") if best_video else None,
                "ext": best_video.get("ext") if best_video else None,
                "width": best_video.get("width") if best_video else None,
                "height": best_video.get("height") if best_video else None,
                "fps": best_video.get("fps") if best_video else None,
                "filesize": best_video.get("filesize") if best_video else None
            },

            "audio": {
                "url": best_audio.get("url") if best_audio else None,
                "format_id": best_audio.get("format_id") if best_audio else None,
                "ext": best_audio.get("ext") if best_audio else None,
                "abr": best_audio.get("abr") if best_audio else None,
                "filesize": best_audio.get("filesize") if best_audio else None
            }

        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api", methods=["GET"])
def home():

    return jsonify({
        "name": "YouTube Downloader API",
        "status": "online",
        "usage": "/api/download?url=YOUTUBE_URL"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
