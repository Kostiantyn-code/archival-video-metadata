import csv
import hashlib
import math
from pathlib import Path

import av


# ============================================================
# НАЛАШТУВАННЯ
# ============================================================

INPUT_DIR = Path(r"D:\temp\2026")

OUTPUT_FILE = Path(
    r"D:\temp\resolution-python-recommended.csv"
)

ERROR_FILE = Path(
    r"D:\temp\resolution-python-errors.txt"
)

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mpg",
}


# ============================================================
# SHA-256
# ============================================================

def calculate_sha256(file_path):
    """
    Обчислення SHA-256 файла.
    Файл читається блоками і не завантажується
    повністю в оперативну пам'ять.
    """

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            sha256.update(block)

    # Для однакового представлення з PowerShell
    return sha256.hexdigest().upper()


# ============================================================
# ТРИВАЛІСТЬ
# ============================================================

def format_duration(duration_seconds):
    """
    Округлює тривалість до найближчої цілої секунди.

    Наприклад:
    69.499 -> 01:09
    69.500 -> 01:10
    69.900 -> 01:10

    Для відео тривалістю понад годину:
    3661 секунд -> 01:01:01
    """

    # Для додатних значень це дає звичайне
    # математичне округлення 0,5 вгору.
    total_seconds = math.floor(
        duration_seconds + 0.5
    )

    hours, remainder = divmod(
        total_seconds,
        3600
    )

    minutes, seconds = divmod(
        remainder,
        60
    )

    if hours > 0:
        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return (
        f"{minutes:02d}:"
        f"{seconds:02d}"
    )


# ============================================================
# ТЕХНІЧНІ ХАРАКТЕРИСТИКИ ВІДЕО
# ============================================================

def get_video_info(file_path):
    """
    Отримує роздільну здатність і тривалість
    першого відеопотоку.
    """

    with av.open(str(file_path)) as container:

        if not container.streams.video:
            raise ValueError(
                "У файлі не знайдено відеопотоку"
            )

        video_stream = container.streams.video[0]

        # ----------------------------------------
        # Роздільна здатність
        # ----------------------------------------

        width = video_stream.codec_context.width
        height = video_stream.codec_context.height

        if not width or not height:
            raise ValueError(
                "Не вдалося визначити "
                "роздільну здатність"
            )

        resolution = f"{width}x{height}"

        # ----------------------------------------
        # Тривалість
        # ----------------------------------------

        if video_stream.duration is None:
            raise ValueError(
                "Не вдалося визначити "
                "тривалість відеопотоку"
            )

        if video_stream.time_base is None:
            raise ValueError(
                "Не вдалося визначити "
                "часову базу відеопотоку"
            )

        duration_seconds = float(
            video_stream.duration
            * video_stream.time_base
        )

        duration = format_duration(
            duration_seconds
        )

        return resolution, duration


# ============================================================
# РОЗМІР ФАЙЛА
# ============================================================

def get_file_size(file_path):
    """
    Отримує фактичний розмір файла у байтах
    і представляє його в похідній одиниці,
    аналогічно попередньому PowerShell-сценарію.

    1 MB у PowerShell = 1024 * 1024 байтів.
    """

    size_bytes = file_path.stat().st_size

    size_mb = (
        size_bytes
        / (1024 * 1024)
    )

    # Завжди два знаки після коми:
    # 31,30
    # 25,02
    # 10,00

    return (
        f"{size_mb:.2f}"
        .replace(".", ",")
    )


# ============================================================
# ОБРОБКА ОДНОГО ФАЙЛА
# ============================================================

def process_file(file_path):

    resolution, duration = get_video_info(
        file_path
    )

    size = get_file_size(
        file_path
    )

    sha256 = calculate_sha256(
        file_path
    )

    return [
        file_path.name,
        resolution,
        duration,
        size,
        sha256,
    ]


# ============================================================
# ГОЛОВНА ПРОГРАМА
# ============================================================

def main():

    if not INPUT_DIR.exists():
        print(
            f"Помилка: директорію не знайдено: "
            f"{INPUT_DIR}"
        )
        return

    # ----------------------------------------
    # Пошук відеофайлів
    # ----------------------------------------

    video_files = [
        file_path
        for file_path in INPUT_DIR.rglob("*")
        if (
            file_path.is_file()
            and file_path.suffix.lower()
            in VIDEO_EXTENSIONS
        )
    ]

    # Сортуємо за відносним шляхом,
    # щоб порядок був стабільним.

    video_files.sort(
        key=lambda path: str(
            path.relative_to(INPUT_DIR)
        ).lower()
    )

    total_files = len(video_files)

    print(
        f"Знайдено відеофайлів: "
        f"{total_files}"
    )

    print()

    errors = []

    # ----------------------------------------
    # CSV
    # ----------------------------------------

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

        for number, file_path in enumerate(
            video_files,
            start=1
        ):

            print(
                f"[{number}/{total_files}] "
                f"{file_path.name}"
            )

            try:

                result = process_file(
                    file_path
                )

                writer.writerow(result)

                print(
                    "   "
                    + ";".join(result)
                )

            except Exception as error:

                error_text = (
                    f"{file_path} : {error}"
                )

                errors.append(
                    error_text
                )

                print(
                    f"   ПОМИЛКА: {error}"
                )

    # ----------------------------------------
    # Протокол помилок
    # ----------------------------------------

    if errors:

        ERROR_FILE.write_text(
            "\n".join(errors),
            encoding="utf-8"
        )

    elif ERROR_FILE.exists():

        ERROR_FILE.unlink()

    # ----------------------------------------
    # Підсумок
    # ----------------------------------------

    print()
    print("Готово.")

    print(
        f"Оброблено файлів: "
        f"{total_files}"
    )

    print(
        f"Успішно: "
        f"{total_files - len(errors)}"
    )

    print(
        f"Помилок: "
        f"{len(errors)}"
    )

    print(
        f"Результат: "
        f"{OUTPUT_FILE}"
    )

    if errors:
        print(
            f"Протокол помилок: "
            f"{ERROR_FILE}"
        )


if __name__ == "__main__":
    main()
