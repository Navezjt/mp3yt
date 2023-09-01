# Lucas Bubner, 2023
from flask import Flask, render_template, request, redirect, flash, send_file
from pytube import YouTube
from os import environ, remove
from waitress import serve
from io import BytesIO
from moviepy.editor import VideoFileClip

import logging
logging.basicConfig(filename='logs.log', filemode='a', format='%(asctime)s :: %(levelname)s :: %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO)

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Parse link into pytube object
        try:
            link = request.form["link"]
            type = request.form["type"]
            try:
                yt = YouTube(link, on_complete_callback=lambda _, path: convert(path, type))
            except Exception as e:
                logging.warning("%s", str(e))
                raise Exception("Invalid or unsupported link.")

            if yt.age_restricted:
                raise Exception("Cannot download age-restricted videos.")

            # Download video file
            try:
                yt = yt.streams.get_highest_resolution()
                yt.download(output_path="/tmp/mp3yt/", filename=strip(yt.title) + ".mp4")
            except Exception as e:
                logging.error("%s", str(e))
                raise Exception("Failed to download video. Please try again later.")
                
            # Write file into memory
            data = BytesIO()
            with open(f"/tmp/mp3yt/{strip(yt.title)}.{type}", "rb") as f:
                data.write(f.read())
            data.seek(0)
            # Remove file as it is no longer needed and is in memory
            remove(f"/tmp/mp3yt/{strip(yt.title)}.{type}")
            logging.info("successful conversion")
            
            # Send file to user
            return send_file(data,
                             as_attachment=True,
                             mimetype="audio/mp3" if type == "mp3" else "video/mp4",
                             download_name=f"{strip(yt.title)}.{type}")

        except Exception as e:
            flash(str(e))
            return redirect("/")
    else:
        return render_template("index.html")


def convert(path, type):
    if type == "mp4":
        return
    # Convert all downloaded mp4 files to mp3 if required
    with VideoFileClip(path) as video:
        video.audio.write_audiofile(path + ".mp3")
    # Delete mp4 file
    remove(path)


def strip(dodgy):
    # Limit to 75 characters
    dodgy = dodgy[:75]
    # Remove characters that are not allowed in file names
    return "".join(i for i in dodgy if i not in r'\/:*?"<>|#')


if __name__ == "__main__":
    app.secret_key = environ["SECRET_KEY"]
    app.config["SESSION_TYPE"] = "filesystem"
    serve(app, host="0.0.0.0")
