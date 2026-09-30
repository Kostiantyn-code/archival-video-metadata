import contextlib
import csv
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
import archival_video_metadata as metadata


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='відео архів ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'input'
        self.source.mkdir()
        self.output = self.root / 'output'

    def run_metadata(self, *extra, compatible=False):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return metadata.main(['--input', str(self.source), '--output', str(self.output),
                                  *extra], compatible=compatible)

    def test_duration_rounding_and_hours(self):
        for seconds, expected in [(69.499, '01:09'), (69.5, '01:10'),
                                  (3599.5, '01:00:00'), (3661, '01:01:01')]:
            self.assertEqual(metadata.format_duration(seconds), expected)

    def test_hash_and_size(self):
        path = self.source / 'sample.mp4'
        path.write_bytes(b'abc')
        self.assertEqual(metadata.calculate_sha256(path), hashlib.sha256(b'abc').hexdigest().upper())
        self.assertEqual(metadata.get_file_size(path), '0,00')
        self.assertEqual(metadata.get_file_size(path, compatible=True), '0,0')

    def test_empty_input_creates_no_report(self):
        self.assertEqual(self.run_metadata(), 0)
        self.assertFalse(self.output.exists())

    def test_missing_input_is_not_created(self):
        self.source = self.root / 'missing'
        self.assertEqual(self.run_metadata(), 1)
        self.assertFalse(self.source.exists())

    def test_output_conflict(self):
        self.assertEqual(self.run_metadata('--output', str(self.source)), 1)
        self.assertEqual(self.run_metadata('--output', str(self.root)), 1)

    def test_recursive_discovery_ignores_output_and_other_extensions(self):
        (self.source / '2026').mkdir()
        (self.source / '2026' / 'A.MP4').touch()
        (self.source / 'note.txt').touch()
        output = self.source / 'reports'
        output.mkdir()
        (output / 'exclude.mp4').touch()
        self.assertEqual(metadata.find_video_files(self.source, output),
                         [self.source / '2026' / 'A.MP4'])

    def test_missing_dependency_message(self):
        (self.source / 'a.mp4').touch()
        with patch.object(metadata, 'av', None):
            self.assertEqual(self.run_metadata(), 1)
        self.assertFalse(self.output.exists())

    def test_csv_and_errors_preserve_previous_runs(self):
        for folder in ('А', 'Б'):
            (self.source / folder).mkdir()
            (self.source / folder / 'same.mp4').write_bytes(b'abc')
        (self.source / 'bad.mp4').touch()

        def info(path, compatible=False):
            if path.name == 'bad.mp4':
                raise ValueError('Пошкоджене відео')
            return '320x240', '01:09'

        with patch.object(metadata, 'av', object()), patch.object(metadata, 'get_video_info', side_effect=info):
            self.assertEqual(self.run_metadata('--relative-paths'), 2)
            first = next(self.output.glob('*/metadata.csv'))
            original = first.read_bytes()
            self.assertTrue(original.startswith(b'\xef\xbb\xbf'))
            with first.open(encoding='utf-8-sig', newline='') as file:
                rows = list(csv.reader(file, delimiter=';'))
            self.assertEqual([r[0] for r in rows], ['А/same.mp4', 'Б/same.mp4'])
            self.assertTrue(all(len(r) == 5 for r in rows))
            self.assertIn('bad.mp4', first.with_name('errors.txt').read_text())
            self.assertEqual(self.run_metadata(), 2)
            self.assertEqual(len(list(self.output.glob('*/metadata.csv'))), 2)
            self.assertEqual(first.read_bytes(), original)

    def test_compatibility_duration(self):
        from types import SimpleNamespace
        stream = SimpleNamespace(duration=36619, time_base=0.1,
                                 codec_context=SimpleNamespace(width=320, height=240))
        container = contextlib.nullcontext(SimpleNamespace(streams=SimpleNamespace(video=[stream])))
        fake_av = unittest.mock.Mock()
        fake_av.open.return_value = container
        with patch.object(metadata, 'av', fake_av):
            self.assertEqual(metadata.get_video_info('test', compatible=True), ('320x240', '01:01'))

    @unittest.skipIf(metadata.av is None, 'PyAV is required for the integration test')
    def test_real_video_and_cli_from_another_directory(self):
        av = metadata.av
        path = self.source / 'Відео 01.MP4'
        with av.open(str(path), 'w') as container:
            stream = container.add_stream('mpeg4', rate=25)
            stream.width = 64
            stream.height = 48
            stream.pix_fmt = 'yuv420p'
            for _ in range(26):
                frame = av.VideoFrame(64, 48, 'yuv420p')
                for plane in frame.planes:
                    plane.update(bytes(plane.buffer_size))
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
        self.assertEqual(metadata.get_video_info(path), ('64x48', '00:01'))
        (self.source / 'broken.mp4').write_bytes(b'not a video')
        script = Path(metadata.__file__).resolve()
        for entry in (script, script.with_name('powershell_compatible.py')):
            result = subprocess.run([sys.executable, str(entry), '--input', str(self.source),
                                     '--output', str(self.output)], cwd=self.root,
                                    capture_output=True, text=True, encoding='utf-8',
                                    env={**os.environ, 'PYTHONUTF8': '1'})
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        for report in self.output.glob('*/metadata.csv'):
            with report.open(encoding='utf-8-sig', newline='') as file:
                rows = list(csv.reader(file, delimiter=';'))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][0:3], [path.name, '64x48', '00:01'])
            self.assertEqual(rows[0][4], hashlib.sha256(path.read_bytes()).hexdigest().upper())


if __name__ == '__main__':
    unittest.main()
