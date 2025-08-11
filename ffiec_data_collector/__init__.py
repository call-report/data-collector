"""
FFIEC Data Collector - Modern Python library for downloading FFIEC data

A lightweight implementation for accessing FFIEC bulk data downloads with 
automatic last-updated date tracking.
"""

__version__ = "2.0.0rc1"
__author__ = "Michael"
__email__ = "michael@civicforge.solutions"

from .downloader import (
    FFIECDownloader,
    Product,
    FileFormat,
    ReportingPeriod,
    DownloadRequest,
    DownloadResult
)

from .thumbprint import (
    ThumbprintValidator,
    ValidatedFFIECDownloader,
    PageThumbprint,
    FormElement,
    WebpageChangeException
)

__all__ = [
    "FFIECDownloader",
    "Product",
    "FileFormat",
    "ReportingPeriod",
    "DownloadRequest",
    "DownloadResult",
    "ThumbprintValidator",
    "ValidatedFFIECDownloader",
    "PageThumbprint",
    "FormElement",
    "WebpageChangeException"
]