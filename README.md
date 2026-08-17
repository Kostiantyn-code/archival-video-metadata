# archival-video-metadata

Tools for automated extraction of technical metadata from digital video files for archival description.

The repository contains two implementations of the workflow: Python scripts and the original PowerShell script.

## Python scripts

The Python scripts are located in the `python/` directory.

- `python/archival_video_metadata.py` — recommended version;
- `python/powershell_compatible.py` — version designed to preserve compatibility with the output of the original PowerShell implementation.

The only third-party Python dependency required by the current scripts is **PyAV** (`av`); the remaining imported modules belong to the Python standard library.

For installation and execution on Windows, see **[PYTHON_SETUP.md](PYTHON_SETUP.md)**.

Quick installation:

```powershell
py -m pip install -r requirements.txt
```

Recommended script:

```powershell
py python\archival_video_metadata.py
```

## PowerShell script

The original PowerShell implementation is located at:

`powershell/resolution3.ps1`

It directly uses **ffprobe**, which is included with FFmpeg, to obtain video resolution and duration. Therefore FFmpeg must be installed separately for this version.

For installation and execution on Windows, see **[POWERSHELL_SETUP.md](POWERSHELL_SETUP.md)**.

Run from the repository directory:

```powershell
.\powershell\resolution3.ps1
```
