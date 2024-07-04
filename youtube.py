import os
from typing import List
from pytube import YouTube, Playlist
from pathlib import Path
import subprocess
import time

# Constants
OUTPUT_DIR = r"INSERT_YOUR_OUTPUT_DIR_HERE"
FILE_TYPE = "mp4"  # or 'mp3', depending on what you want to download

# Define your URLs here in a single list, can be a mix of single videos and playlists.
URLS = [
    "https://www.youtube.com/playlist?list=PLGAnmvB9m7zOBVCZBUUmSinFV0wEir2Vw",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
]


class Youtube:
    def __init__(
        self,
        urls: List[str],
        outdir: str = OUTPUT_DIR,
        file_type: str = FILE_TYPE,
    ) -> None:
        self.outdir = outdir
        self.file_type = file_type
        self.urls = urls
        self.init_download()

    def init_download(self):
        for url in self.urls:
            if "playlist?list=" in url:
                self.download_playlist(url)
            else:
                self.download_video(url)
        print("All downloads completed.")

    def download_video(self, url):
        try:
            yt = YouTube(url)
            if self.file_type == "mp3":
                audio_stream = yt.streams.filter(only_audio=True, abr="160kbps").last()
                if audio_stream is not None:
                    self.download_with_retry(
                        audio_stream, output_path=self.outdir, rename_to_ext="mp3"
                    )
                else:
                    print(f"No audio stream found for {yt.title}.")
            elif self.file_type == "mp4":
                video_stream = (
                    yt.streams.filter(progressive=False, file_extension="mp4")
                    .order_by("resolution")
                    .desc()
                    .first()
                )
                audio_stream = yt.streams.filter(
                    only_audio=True, file_extension="mp4"
                ).first()

                if video_stream is not None and audio_stream is not None:
                    if not os.path.exists(self.outdir):
                        os.makedirs(self.outdir)

                    video_file = self.download_with_retry(
                        video_stream, output_path=self.outdir, filename="temp_video.mp4"
                    )
                    audio_file = self.download_with_retry(
                        audio_stream, output_path=self.outdir, filename="temp_audio.mp4"
                    )

                    if video_file and audio_file:
                        output_file = Path(self.outdir) / f"{yt.title}.mp4"

                        # Use subprocess to run ffmpeg with -progress flag
                        command = [
                            "ffmpeg",
                            "-i",
                            video_file,
                            "-i",
                            audio_file,
                            "-c:v",
                            "copy",
                            "-c:a",
                            "aac",
                            "-strict",
                            "experimental",
                            "-y",
                            str(output_file),
                            "-nostats",
                            "-loglevel",
                            "info",
                        ]

                        process = subprocess.Popen(
                            command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True,
                        )

                        # Read ffmpeg output and filter progress updates
                        for line in process.stderr:  # type: ignore
                            if "progress=" in line:
                                print(line.strip())

                        # Wait for ffmpeg process to finish
                        process.communicate()

                        # Clean up temp files
                        os.remove(video_file)
                        os.remove(audio_file)

                        if output_file.exists():
                            print(f"{yt.title} has been successfully downloaded.")
                        else:
                            print(f"ERROR: {yt.title} could not be downloaded.")
                    else:
                        print("It .")
                else:
                    print(f"No suitable streams found for {yt.title}.")
            else:
                print("Unsupported file type.")
        except Exception as e:
            print(f"Error processing {url}: {e}")

    def download_playlist(self, playlist_url):
        try:
            playlist = Playlist(playlist_url)
            for video_url in playlist.video_urls:
                self.download_video(video_url)
        except Exception as e:
            print(f"Error downloading playlist {playlist_url}: {e}")

    def download_with_retry(
        self,
        stream,
        output_path,
        filename=None,
        rename_to_ext=None,
        max_retries=3,
        delay=5,
    ):
        attempt = 0
        while attempt < max_retries:
            try:
                out_file = stream.download(output_path=output_path, filename=filename)
                if rename_to_ext:
                    base, ext = os.path.splitext(out_file)
                    new_file = Path(f"{base}.{rename_to_ext}")
                    os.rename(out_file, new_file)
                    return str(new_file)
                return out_file
            except Exception as e:
                print(f"Error downloading {stream.default_filename}: {e}")
                attempt += 1
                if attempt < max_retries:
                    print(f"Retrying... ({attempt}/{max_retries})")
                    time.sleep(delay)
                else:
                    print("Max retries reached. Download failed.")
                    return None


# Initialize the Youtube class with the URLs list
yt_downloader = Youtube(URLS)
