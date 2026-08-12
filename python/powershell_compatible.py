import csv
import hashlib
from pathlib import Path

import av


# ------------------------------------------------------------
# Settings
# ------------------------------------------------------------

INPUT_DIR = Path(r"D:\temp\2026")
OUTPUT_FILE = Path(r"D:\temp\resolution-python.csv")

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mpg",
}


# ------------------------------------------------------------
# SHA-256
# ------------------------------------------------------------

def calculate_sha256(file_path):
    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(block)

    # PowerShell Get-FileHash returns uppercase hexadecimal characters.
    return sha256.hexdigest().upper()


# ------------------------------------------------------------
# Video technical characteristics
# ------------------------------------------------------------

def get_video_info(file_path):
    with av.open(str(file_path)) as container:
        video_stream = container.streams.video[0]

        resolution = (
            f"{video_stream.codec_context.width}"
            f"x"
            f"{video_stream.codec_context.height}"
        )

        duration_seconds = float(
            video_stream.duration * video_stream.time_base
        )

        # Compatibility with the original PowerShell output:
        # discard the fractional part of a second.
        total_seconds = int(duration_seconds)

        minutes = (total_seconds // 60) % 60
        seconds = total_seconds % 60

        duration = f"{minutes:02d}:{seconds:02d}"

        return resolution, duration


# ------------------------------------------------------------
# File size
# ------------------------------------------------------------

def get_file_size(file_path):
    # Equivalent to:
    # [math]::Round((Get-Item $filePath).Length / 1MB, 2)
    size_mb = round(
        file_path.stat().st_size / (1024 * 1024),
        2
    )

    # Preserve the formatting of the original PowerShell output.
    size_text = str(size_mb)

    # Use a decimal comma, as in the original script.
    return size_text.replace(".", ",")


# ------------------------------------------------------------
# Main program
# ------------------------------------------------------------

def main():
    video_files = [
        file_path
        for file_path in INPUT_DIR.rglob("*")
        if (
            file_path.is_file()
            and file_path.suffix.lower() in VIDEO_EXTENSIONS
        )
    ]

    video_files.sort(
        key=lambda path: str(path.relative_to(INPUT_DIR)).lower()
    )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csv_file:

        writer = csv.writer(
            csv_file,
            delimiter=";",
            lineterminator="\n"
        )

        for file_path in video_files:
            resolution, duration = get_video_info(file_path)
            size = get_file_size(file_path)
            sha256 = calculate_sha256(file_path)

            writer.writerow([
                file_path.name,
                resolution,
                duration,
                size,
                sha256,
            ])

            print(
                f"{file_path.name};"
                f"{resolution};"
                f"{duration};"
                f"{size};"
                f"{sha256}"
            )

    print()
    print(f"Processed files: {len(video_files)}")
    print(f"Result: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
