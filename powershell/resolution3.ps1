# Function to get video information using ffprobe
function Get-VideoInfo($filePath) {
    $info = & "c:\Tools\ffmpeg\bin\ffprobe.exe" -v error -select_streams v:0 -show_entries stream=width,height,duration -of csv=p=0 $filePath
    $duration = [timespan]::FromSeconds($info.Split(',')[2])
    $durationFormatted = '{0:00}:{1:00}' -f $duration.Minutes, $duration.Seconds
    $sizeMB = [math]::Round((Get-Item $filePath).Length / 1MB, 2)
    $sizeFormatted = $sizeMB -replace '\.', ','
    $resolution = $info.Split(',')[0..1] -join 'x'
    $hash = Get-FileHash -Algorithm SHA256 -Path $filePath | Select-Object -ExpandProperty Hash
    return "$filePath;$resolution;$durationFormatted;$sizeFormatted;$hash"
}

# Main directory containing video files
$mainDirectory = "d:\temp\2026"

# Output file path
$outputFilePath = "d:\temp\resolution.csv"

# Recursively get all video files in the main directory
$videoFiles = Get-ChildItem -Path $mainDirectory -Recurse -File -Include *.mp4,*.mov,*.avi,*.mpg

# Loop through each video file to get its information
$results = foreach ($file in $videoFiles) {
    Get-VideoInfo $file.FullName
}

# Output results to CSV file
$results | Out-File -FilePath $outputFilePath -Encoding utf8
