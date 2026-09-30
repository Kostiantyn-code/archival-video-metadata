import argparse
import csv
from datetime import datetime
import hashlib
import math
import os
import sys
from pathlib import Path

try:
    import av
except ImportError:
    av = None


# ============================================================
# НАЛАШТУВАННЯ
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "input"
OUTPUT_DIR = PROJECT_DIR / "output"

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

def get_video_info(file_path, compatible=False):
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

        if not math.isfinite(duration_seconds) or duration_seconds < 0:
            raise ValueError("Некоректна тривалість відеопотоку")

        if compatible:
            total_seconds = int(duration_seconds)
            duration = f"{(total_seconds // 60) % 60:02d}:{total_seconds % 60:02d}"
        else:
            duration = format_duration(duration_seconds)

        return resolution, duration


# ============================================================
# РОЗМІР ФАЙЛА
# ============================================================

def get_file_size(file_path, compatible=False):
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

    if compatible:
        return str(round(size_mb, 2)).replace(".", ",")

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

def process_file(file_path, compatible=False):

    resolution, duration = get_video_info(
        file_path, compatible=compatible
    )

    size = get_file_size(
        file_path, compatible=compatible
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

def build_parser():
    parser = argparse.ArgumentParser(
        description="Технічні метадані відео: роздільна здатність, тривалість, розмір і SHA-256."
    )
    parser.add_argument("--input", type=Path, default=INPUT_DIR,
                        help="Папка з відео та підпапками (типово: input біля run.bat).")
    parser.add_argument("--output", type=Path, default=OUTPUT_DIR,
                        help="Папка звітів (типово: output біля run.bat).")
    parser.add_argument("--relative-paths", action="store_true",
                        help="Записувати відносні шляхи замість самих назв файлів.")
    return parser


def find_video_files(input_dir, output_dir):
    """Не приховувати помилки читання директорій та не сканувати власні звіти."""
    output_dir = output_dir.resolve()

    def on_error(error):
        raise error

    video_files = []
    for root, dirs, files in os.walk(input_dir, onerror=on_error):
        dirs[:] = [name for name in dirs
                   if (Path(root) / name).resolve() != output_dir]
        for name in files:
            path = Path(root) / name
            if path.suffix.lower() in VIDEO_EXTENSIONS and path.is_file():
                video_files.append(path)
    return sorted(video_files, key=lambda p: (
        str(p.relative_to(input_dir)).casefold(), str(p.relative_to(input_dir))))


def main(argv=None, compatible=False):
    args = build_parser().parse_args(argv)
    try:
        input_dir = args.input.expanduser().resolve()
        output_dir = args.output.expanduser().resolve()
        # Створюємо лише стандартну папку: помилковий шлях користувача — це помилка.
        if input_dir == INPUT_DIR:
            input_dir.mkdir(parents=True, exist_ok=True)
        if not input_dir.is_dir():
            print(f"Помилка: вхідну папку не знайдено: {input_dir}", file=sys.stderr)
            return 1
        if input_dir == output_dir or output_dir in input_dir.parents:
            print("Помилка: папка звітів має бути окремою від вхідної "
                  "та не містити її.", file=sys.stderr)
            return 1
        video_files = find_video_files(input_dir, output_dir)
        if not video_files:
            print(f"Відеофайлів не знайдено: {input_dir}")
            print("Покладіть сюди відео (можна з підпапками) і запустіть програму ще раз.")
            print("Підтримувані розширення: " + ", ".join(sorted(VIDEO_EXTENSIONS)))
            return 0
        if av is None:
            print("Не вдалося імпортувати PyAV. Запустіть run.bat або встановіть "
                  "залежність командою: python -m pip install -r requirements.txt",
                  file=sys.stderr)
            return 1

        # Кожен запуск має власну папку; попередні звіти не перезаписуються.
        run_dir = output_dir / datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
        run_dir.mkdir(parents=True, exist_ok=False)
        output_file = run_dir / "metadata.csv"
        error_file = run_dir / "errors.txt"
        total_files = len(video_files)
        print(f"Вхідна папка: {input_dir}")
        print(f"Знайдено відеофайлів: {total_files}")
        print("Обчислення SHA-256 читає кожен файл повністю; великі відео потребують часу.")
        if not args.relative_paths and len({p.name for p in video_files}) < total_files:
            print("Увага: є однакові назви файлів у різних папках. "
                  "Параметр --relative-paths дозволяє розрізнити їх у CSV.")

        errors = 0
        with output_file.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file, delimiter=";", lineterminator="\n")
            for number, file_path in enumerate(video_files, start=1):
                relative_path = file_path.relative_to(input_dir).as_posix()
                print(f"[{number}/{total_files}] {relative_path}", flush=True)
                try:
                    result = process_file(file_path, compatible=compatible)
                except Exception as error:
                    errors += 1
                    with error_file.open("a", encoding="utf-8") as log:
                        log.write(f"{file_path} : {error}\n")
                    print(f"   ПОМИЛКА: {error}")
                    continue
                if args.relative_paths:
                    result[0] = relative_path
                writer.writerow(result)
                csv_file.flush()

        print(f"\nУспішно: {total_files - errors}; помилок: {errors}.")
        print(f"Результат: {output_file}")
        if errors:
            print(f"Протокол помилок: {error_file}")
        return 2 if errors else 0
    except OSError as error:
        print(f"Помилка доступу до файлів: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nОбробку перервано. Уже записані рядки залишено у звіті.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
