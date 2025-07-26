"""
Tests for argument parsing
"""

import pytest
from pathlib import Path
import tempfile
import json

from sh2mp4.args import parse_and_validate_args


def create_test_cast_file() -> Path:
    """Create a temporary test cast file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cast", delete=False) as f:
        # Write minimal valid cast file
        header = {"version": 2, "width": 80, "height": 24, "timestamp": 1234567890}
        f.write(json.dumps(header) + "\n")
        f.write('[1.0, "o", "hello world\\n"]\n')
        return Path(f.name)


class TestBasicParsing:
    """Test basic argument parsing functionality"""

    def test_simple_command(self):
        """Test basic command recording"""
        args = parse_and_validate_args(["echo hello", "test.mp4"])

        assert args.command == "echo hello"
        assert args.output == "test.mp4"
        assert args.cast_file is None
        assert args.speed is None
        assert args.fps == 30
        assert args.recording_fps == 30

    def test_default_output(self):
        """Test default output filename"""
        args = parse_and_validate_args(["echo hello"])

        assert args.command == "echo hello"
        assert args.output == "output.mp4"

    def test_utility_modes(self):
        """Test utility mode flags"""
        args = parse_and_validate_args(["--check-deps"])
        assert args.check_deps is True
        assert args.command is None

        args = parse_and_validate_args(["--measure-fonts"])
        assert args.measure_fonts is True
        assert args.command is None


class TestCastFileMode:
    """Test cast file argument parsing"""

    def test_cast_file_basic(self):
        """Test basic cast file conversion"""
        cast_file = create_test_cast_file()
        try:
            args = parse_and_validate_args(["--cast-file", str(cast_file), "test.mp4"])

            # Basic args preserved
            assert args.cast_file == str(cast_file)
            assert args.output == "test.mp4"  # Output filename preserved exactly

            # Cast file processing results
            assert args.command is not None  # Should be asciinema command
            assert "asciinema play" in args.command
            assert args.cols == 80  # From cast file header
            assert args.lines == 24  # From cast file header
            assert args.recording_fps == 30  # No speed, so same as fps
        finally:
            cast_file.unlink()

    def test_cast_file_with_speed(self):
        """Test cast file with speed multiplier"""
        cast_file = create_test_cast_file()
        try:
            args = parse_and_validate_args(["--cast-file", str(cast_file), "--speed", "8x", "my-video.mp4"])

            # Basic args preserved
            assert args.cast_file == str(cast_file)
            assert args.speed == "8x"
            assert args.output == "my-video.mp4"  # Output filename preserved exactly

            # Speed processing results
            assert args.fps == 30
            assert args.recording_fps == 240  # 30 * 8
            assert "-s 8.0" in args.command  # Should include speed flag
        finally:
            cast_file.unlink()

    def test_cast_file_missing(self):
        """Test error when cast file doesn't exist"""
        with pytest.raises(SystemExit):
            parse_and_validate_args(["--cast-file", "/nonexistent/file.cast"])


class TestSpeedValidation:
    """Test speed parameter validation"""

    def test_speed_without_cast_file_warns(self, capsys):
        """Test that --speed without --cast-file gives warning"""
        args = parse_and_validate_args(["echo hello", "test.mp4", "--speed", "8x"])

        # Should ignore speed and warn
        assert args.speed is None
        assert args.recording_fps == 30
        assert args.output == "test.mp4"  # Output filename preserved

        captured = capsys.readouterr()
        assert "Warning: --speed only applies to --cast-file mode" in captured.err

    def test_valid_speed_values(self):
        """Test valid speed values are accepted"""
        cast_file = create_test_cast_file()
        try:
            for speed in ["2x", "4x", "8x"]:
                args = parse_and_validate_args(["--cast-file", str(cast_file), "--speed", speed])
                assert args.speed == speed
        finally:
            cast_file.unlink()


class TestErrorCases:
    """Test error handling and edge cases"""

    def test_no_command_without_utility_mode(self):
        """Test error when no command provided"""
        with pytest.raises(SystemExit):
            parse_and_validate_args([])

    def test_mysterious_cast_flag(self):
        """Test the mysterious --cast flag that shouldn't exist"""
        with pytest.raises(SystemExit):
            parse_and_validate_args(["--cast", "file.cast"])


class TestArgumentPrecedence:
    """Test how arguments interact and override each other"""

    def test_cast_file_respects_user_dimensions(self):
        """Test that user-provided dimensions override cast file dimensions"""
        cast_file = create_test_cast_file()
        try:
            args = parse_and_validate_args(
                ["--cast-file", str(cast_file), "--cols", "120", "--lines", "40", "output-file.mp4"]
            )

            # Should use user-provided dimensions, not cast file dims
            assert args.cols == 120  # User provided
            assert args.lines == 40  # User provided
            assert args.output == "output-file.mp4"  # Output filename preserved
        finally:
            cast_file.unlink()

    def test_cast_file_uses_optimized_dimensions_when_not_specified(self):
        """Test that cast file dimensions are used when user doesn't specify them"""
        cast_file = create_test_cast_file()
        try:
            args = parse_and_validate_args(["--cast-file", str(cast_file), "output-file.mp4"])

            # Should use dimensions from cast file when not explicitly specified
            assert args.cols == 80  # From cast file header
            assert args.lines == 24  # From cast file header
            assert args.output == "output-file.mp4"  # Output filename preserved
        finally:
            cast_file.unlink()


class TestOutputFilenamePreservation:
    """Critical tests to ensure output filename is always preserved exactly"""

    def test_live_recording_custom_filename(self):
        """Test custom filename in live recording mode"""
        args = parse_and_validate_args(["echo hello", "my-custom-video.mp4"])
        assert args.output == "my-custom-video.mp4"
        assert args.command == "echo hello"

    def test_live_recording_default_filename(self):
        """Test default filename in live recording mode"""
        args = parse_and_validate_args(["echo hello"])
        assert args.output == "output.mp4"
        assert args.command == "echo hello"

    def test_cast_file_custom_filename(self):
        """Test custom filename in cast file mode"""
        cast_file = create_test_cast_file()
        try:
            args = parse_and_validate_args(["--cast-file", str(cast_file), "cast-video.mp4"])
            assert args.output == "cast-video.mp4"
            assert args.cast_file == str(cast_file)
        finally:
            cast_file.unlink()

    def test_cast_file_with_speed_custom_filename(self):
        """Test custom filename with cast file and speed"""
        cast_file = create_test_cast_file()
        try:
            args = parse_and_validate_args(["--cast-file", str(cast_file), "--speed", "4x", "fast-video.mp4"])
            assert args.output == "fast-video.mp4"
            assert args.speed == "4x"
            assert args.cast_file == str(cast_file)
        finally:
            cast_file.unlink()

    def test_complex_filename_with_spaces_and_chars(self):
        """Test that complex filenames are preserved"""
        args = parse_and_validate_args(["echo test", "My Video - Demo (2024).mp4"])
        assert args.output == "My Video - Demo (2024).mp4"
        assert args.command == "echo test"


if __name__ == "__main__":
    pytest.main([__file__])
