from flask import Flask, request, jsonify
import yt_dlp
import re

app = Flask(__name__)


def valid_instagram_url(url):
    pattern = r"^https?://(www\.)?instagram\.com/(reel|p|tv)/"
    return bool(re.match(pattern, url))


@app.route("/api/download", methods=["GET"])
def download():

    url = request.args.get("url")

    if not url:
        return jsonify({
            "success": False,
            "error": "Missing url"
        }), 400

    if not valid_instagram_url(url):
        return jsonify({
            "success": False,
            "error": "Invalid Instagram URL"
        }), 400

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "best",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(url, download=False)

            return jsonify({
                "success": True,
                "id": info.get("id"),
                "title": info.get("title"),
                "description": info.get("description"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "width": info.get("width"),
                "height": info.get("height"),
                "url": info.get("url")
            })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api", methods=["GET"])
def home():
    return jsonify({
        "name": "Instagram Downloader API",
        "status": "online",
        "usage": "/api/download?url=INSTAGRAM_URL"
    })


if __name__ == "__main__":
    app.run()
