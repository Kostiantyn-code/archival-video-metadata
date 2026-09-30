"""Той самий запуск, але з історичним форматом тривалості та розміру."""
import sys

from archival_video_metadata import main


if __name__ == "__main__":
    sys.exit(main(compatible=True))
