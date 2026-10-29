"""
sh2mp4 - Records shell commands to MP4 videos
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("sh2mp4")
except PackageNotFoundError:
    # Source-only checkouts have no installed distribution metadata.
    __version__ = "0+unknown"
