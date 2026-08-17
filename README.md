# archival-video-metadata

Tools for automated extraction of technical metadata from digital video files for archival description.

Репозитарій містить дві реалізації процесу: Python-сценарії та первинний PowerShell-сценарій.

## Файли

### Python

- `python/archival_video_metadata.py` — рекомендована версія;
- `python/powershell_compatible.py` — версія, сумісна за форматом результату з первинним PowerShell-сценарієм;
- `requirements.txt` — перелік сторонніх Python-залежностей.

### PowerShell

- `powershell/resolution3.ps1` — первинна реалізація на PowerShell.

## Python: швидкий запуск у Windows

Для Python-версії потрібно самостійно встановити **Python** і сторонню бібліотеку **PyAV (`av`)**. Модулі `csv`, `hashlib`, `math` і `pathlib` входять до стандартної бібліотеки Python.

Для звичайного встановлення PyAV у Windows окремий FFmpeg не потрібний: Python-сценарії не запускають `ffmpeg.exe` або `ffprobe.exe` як окремі програми.

Встановлення залежності:

```powershell
py -m pip install -r requirements.txt
```

або:

```powershell
py -m pip install av
```

Перевірка:

```powershell
py -c "import av; print(av.__version__)"
```

Перед запуском змініть у сценарії шляхи до вхідної директорії та вихідних файлів.

Запуск рекомендованої версії:

```powershell
py python\archival_video_metadata.py
```

Запуск сумісної версії:

```powershell
py python\powershell_compatible.py
```

**PyCharm Community Edition не є обов'язковим.** Він використовувався під час розроблення й тестування для редагування коду, контролю виконання та перегляду повідомлень про помилки.

## PowerShell: швидкий запуск у Windows

PowerShell-сценарій безпосередньо використовує **`ffprobe.exe`**, який входить до FFmpeg. Тому для цієї версії **FFmpeg потрібно встановити окремо**.

Поточний сценарій очікує `ffprobe.exe` за шляхом:

```text
C:\Tools\ffmpeg\bin\ffprobe.exe
```

Якщо FFmpeg установлено в іншому місці, змініть шлях у `powershell/resolution3.ps1`.

Також змініть:

```powershell
$mainDirectory = "d:\temp\2026"
$outputFilePath = "d:\temp\resolution.csv"
```

Запуск із кореня репозитарію:

```powershell
.\powershell\resolution3.ps1
```

Якщо Windows блокує локальний сценарій, див. докладну інструкцію `POWERSHELL_SETUP.txt`.

## Формат результату

Сценарії формують текстові табличні дані для подальшого використання в електронних таблицях.

Основний порядок полів:

1. назва файла або шлях до файла;
2. роздільна здатність;
3. тривалість;
4. розмір файла;
5. SHA-256.

Роздільник полів — **крапка з комою (`;`)**, а дробова частина розміру файла записується з **десятковою комою**. Це зручно для типових українських регіональних налаштувань Windows і Microsoft Excel.

Приклад:

```text
0001.mp4;1920x1080;03:27;31,30;A1B2C3D4...
```

Рекомендований Python-сценарій записує CSV у **UTF-8 with BOM (`utf-8-sig`)**. Якщо Excel не розпізнає структуру автоматично, використайте **Data → From Text/CSV**, вибравши UTF-8 та роздільник `;`.

Докладні відмінності між реалізаціями наведено у `OUTPUT_FORMAT.txt`.

## License

MIT License.
