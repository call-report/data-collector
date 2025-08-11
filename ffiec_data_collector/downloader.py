"""
FFIEC Data Downloader - Modern implementation without Selenium
Replaces browser automation with direct HTTP requests to FFIEC's ASP.NET WebForms backend
"""

from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Tuple, Union, BinaryIO
import re
import requests
from pathlib import Path


class Product(Enum):
    """FFIEC data products available for download"""

    CALL_SINGLE = ("ReportingSeriesSinglePeriod", "Call Reports -- Single Period")
    CALL_FOUR_PERIODS = (
        "ReportingSeriesSubsetSchedulesFourPeriods",
        "Call Reports -- Balance Sheet, Income Statement, Past Due -- Four Periods",
    )
    UBPR_RATIO_SINGLE = (
        "PerformanceReportingSeriesSinglePeriod",
        "UBPR Ratio -- Single Period",
    )
    UBPR_RATIO_FOUR = (
        "PerformanceReportingSeriesFourPeriods",
        "UBPR Ratio -- Four Periods",
    )
    UBPR_RANK_FOUR = ("PerformanceReportingSeriesRank", "UBPR Rank -- Four Periods")
    UBPR_STATS_FOUR = ("PerformanceReportingSeriesStats", "UBPR Stats -- Four Periods")

    def __init__(self, value: str, display_name: str):
        self._value = value
        self._display_name = display_name

    @property
    def form_value(self) -> str:
        return self._value

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def is_single_period(self) -> bool:
        return "Single" in self._display_name

    @property
    def is_call_report(self) -> bool:
        return "Call" in self._display_name

    @property
    def is_ubpr(self) -> bool:
        return "UBPR" in self._display_name


class FileFormat(Enum):
    """Available file formats for download"""

    TSV = ("TSVRadioButton", "Tab Delimited", "text/tab-separated-values")
    XBRL = (
        "XBRLRadiobutton",
        "eXtensible Business Reporting Language (XBRL)",
        "application/xml",
    )

    def __init__(self, form_value: str, display_name: str, mime_type: str):
        self._form_value = form_value
        self._display_name = display_name
        self._mime_type = mime_type

    @property
    def form_value(self) -> str:
        return self._form_value

    @property
    def display_name(self) -> str:
        return self._display_name

    @property
    def mime_type(self) -> str:
        return self._mime_type


@dataclass
class ReportingPeriod:
    """Represents a reporting period/quarter"""

    value: str  # Form value like "146"
    date_str: str  # Display string like "03/31/2025"

    @property
    def date(self) -> datetime:
        """Convert MM/DD/YYYY string to datetime"""
        return datetime.strptime(self.date_str, "%m/%d/%Y")

    @property
    def quarter(self) -> int:
        """Get quarter number (1-4)"""
        month = self.date.month
        return (month - 1) // 3 + 1

    @property
    def year(self) -> int:
        """Get year"""
        return self.date.year

    @property
    def yyyymmdd(self) -> str:
        """Get date in YYYYMMDD format"""
        return self.date.strftime("%Y%m%d")

    def __str__(self) -> str:
        return f"Q{self.quarter} {self.year} ({self.date_str})"


@dataclass
class DownloadRequest:
    """Encapsulates a download request with all parameters"""

    product: Product
    period: ReportingPeriod
    format: FileFormat

    def get_expected_filename(self) -> str:
        """Generate expected filename based on parameters"""
        product_prefix = "FFIEC CDR"

        if self.product.is_call_report:
            if self.product == Product.CALL_SINGLE:
                product_name = "Call Bulk"
            else:
                product_name = "Call Bulk Subset of Schedules"
        else:
            product_name = self.product.display_name.replace("--", "").strip()

        format_suffix = "XBRL" if self.format == FileFormat.XBRL else "TSV"
        date_suffix = self.period.date.strftime("%m%d%Y")

        return f"{product_prefix} {product_name} {format_suffix} {date_suffix}.zip"


@dataclass
class DownloadResult:
    """Result of a download operation"""

    success: bool
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    file_path: Optional[Path] = None
    last_updated: Optional[date] = (
        None  # Last updated date for the specific product type
    )
    call_updated: Optional[date] = None  # Call Report last updated date
    ubpr_updated: Optional[date] = None  # UBPR last updated date


class FFIECDownloader:
    """
    Modern FFIEC data downloader using direct HTTP requests
    Replaces Selenium-based approach with lightweight HTTP POST operations
    """

    BASE_URL = "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx"

    def __init__(self, download_dir: Optional[Path] = None):
        """
        Initialize the downloader

        Args:
            download_dir: Directory to save downloaded files (default: current directory)
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.download_dir = download_dir or Path.cwd()
        self.download_dir.mkdir(parents=True, exist_ok=True)

        self._viewstate: Optional[str] = None
        self._viewstate_generator: Optional[str] = None
        self._current_product: Optional[Product] = None
        self._current_period: Optional[ReportingPeriod] = None
        self._available_periods: List[ReportingPeriod] = []
        self._call_updated: Optional[date] = None
        self._ubpr_updated: Optional[date] = None

    def _extract_viewstate(self, html: str) -> Tuple[str, str]:
        """Extract ASP.NET ViewState and ViewStateGenerator from HTML"""
        viewstate_match = re.search(r'name="__VIEWSTATE".*?value="([^"]+)"', html)
        generator_match = re.search(
            r'name="__VIEWSTATEGENERATOR".*?value="([^"]+)"', html
        )

        if not viewstate_match or not generator_match:
            raise ValueError("Could not extract ViewState from page")

        return viewstate_match.group(1), generator_match.group(1)

    def _extract_last_updated_dates(
        self, html: str
    ) -> Tuple[Optional[date], Optional[date]]:
        """Extract Call and UBPR last updated dates from HTML and convert to date objects"""
        call_match = re.search(r"Call Updated: (\d{1,2}/\d{1,2}/\d{4})", html)
        ubpr_match = re.search(r"UBPR Updated: (\d{1,2}/\d{1,2}/\d{4})", html)

        call_updated = None
        ubpr_updated = None

        if call_match:
            try:
                call_updated = datetime.strptime(call_match.group(1), "%m/%d/%Y").date()
            except ValueError:
                pass  # If date parsing fails, leave as None

        if ubpr_match:
            try:
                ubpr_updated = datetime.strptime(ubpr_match.group(1), "%m/%d/%Y").date()
            except ValueError:
                pass  # If date parsing fails, leave as None

        return call_updated, ubpr_updated

    def _get_last_updated_for_product(self, product: Product) -> Optional[date]:
        """Get the appropriate last_updated date for a given product"""
        if product.is_call_report:
            return self._call_updated
        elif product.is_ubpr:
            return self._ubpr_updated
        else:
            return None

    def _post(self, data: Dict[str, Optional[str]]) -> requests.Response:
        """Make a POST request with proper headers"""
        headers = dict(self.session.headers)
        headers.update(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": self.BASE_URL,
                "Origin": "https://cdr.ffiec.gov",
            }
        )

        response = self.session.post(self.BASE_URL, data=data, headers=headers)
        response.raise_for_status()

        # Update ViewState for next request
        if "text/html" in response.headers.get("Content-Type", ""):
            self._viewstate, self._viewstate_generator = self._extract_viewstate(
                response.text
            )

        return response

    def initialize(self) -> None:
        """Initialize session and get initial ViewState"""
        response = self.session.get(self.BASE_URL)
        response.raise_for_status()
        self._viewstate, self._viewstate_generator = self._extract_viewstate(
            response.text
        )
        self._call_updated, self._ubpr_updated = self._extract_last_updated_dates(
            response.text
        )

    def get_available_products(self) -> List[Product]:
        """Get list of all available products"""
        return list(Product)

    def select_product(self, product: Product) -> List[ReportingPeriod]:
        """
        Select a product and get available reporting periods

        Args:
            product: The product to select

        Returns:
            List of available reporting periods for the selected product
        """
        if not self._viewstate:
            self.initialize()

        data: Dict[str, Optional[str]] = {
            "__EVENTTARGET": "ctl00$MainContentHolder$ListBox1",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstate_generator,
            "ctl00$MainContentHolder$ListBox1": product.form_value,
        }

        response = self._post(data)
        self._current_product = product

        # Extract available dates
        dates_match = re.search(
            r'<select name="ctl00\$MainContentHolder\$DatesDropDownList".*?>(.*?)</select>',
            response.text,
            re.DOTALL,
        )

        if not dates_match:
            raise ValueError(f"No dates found for product {product.display_name}")

        date_options = re.findall(
            r'<option.*?value="([^"]+)".*?>([^<]+)</option>', dates_match.group(1)
        )

        self._available_periods = [
            ReportingPeriod(value=val, date_str=text) for val, text in date_options
        ]

        return self._available_periods

    def select_period(self, period: Union[ReportingPeriod, str]) -> None:
        """
        Select a reporting period

        Args:
            period: ReportingPeriod object or date string (MM/DD/YYYY or YYYYMMDD)
        """
        if not self._current_product:
            raise ValueError("Must select product first")

        if isinstance(period, str):
            # Convert string to ReportingPeriod
            period = self._find_period_by_date(period)

        data: Dict[str, Optional[str]] = {
            "__EVENTTARGET": "ctl00$MainContentHolder$DatesDropDownList",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstate_generator,
            "ctl00$MainContentHolder$ListBox1": self._current_product.form_value,
            "ctl00$MainContentHolder$DatesDropDownList": period.value,
        }

        self._post(data)
        self._current_period = period

    def select_format(self, format: FileFormat) -> None:
        """
        Select file format (TSV or XBRL)

        Args:
            format: The file format to select
        """
        if not self._current_product or not self._current_period:
            raise ValueError("Must select product and period first")

        data: Dict[str, Optional[str]] = {
            "__EVENTTARGET": f"ctl00$MainContentHolder${format.form_value}",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstate_generator,
            "ctl00$MainContentHolder$ListBox1": self._current_product.form_value,
            "ctl00$MainContentHolder$DatesDropDownList": (
                self._current_period.value if self._current_period else None
            ),
            "ctl00$MainContentHolder$FormatType": format.form_value,
        }

        self._post(data)

    def download(
        self,
        product: Product,
        period: Union[ReportingPeriod, str],
        format: FileFormat = FileFormat.XBRL,
        save_to_disk: bool = True,
    ) -> Union[DownloadResult, BinaryIO]:
        """
        Download data for specified parameters

        Args:
            product: The product to download
            period: Reporting period (ReportingPeriod object or date string)
            format: File format (default: XBRL)
            save_to_disk: If True, save to disk; if False, return file-like object

        Returns:
            DownloadResult if save_to_disk=True, otherwise file-like object with content
        """
        # Initialize if needed
        if not self._viewstate:
            self.initialize()

        # Select product and get available periods
        available_periods = self.select_product(product)

        # Select period
        if isinstance(period, str):
            period = self._find_period_by_date(period, available_periods)
        self.select_period(period)

        # Select format
        self.select_format(format)

        # Prepare download request
        request = DownloadRequest(product=product, period=period, format=format)

        # Execute download
        data: Dict[str, Optional[str]] = {
            "ctl00$MainContentHolder$TabStrip1$Download_0": "Download",
            "__VIEWSTATE": self._viewstate,
            "__VIEWSTATEGENERATOR": self._viewstate_generator,
            "ctl00$MainContentHolder$ListBox1": product.form_value,
            "ctl00$MainContentHolder$DatesDropDownList": (
                self._current_period.value if self._current_period else None
            ),
            "ctl00$MainContentHolder$FormatType": format.form_value,
        }

        response = self._post(data)

        # Check if we got a file
        content_type = response.headers.get("Content-Type", "")
        content_disposition = response.headers.get("Content-Disposition", "")

        if (
            "application/octet-stream" not in content_type
            and "attachment" not in content_disposition
        ):
            return DownloadResult(
                success=False,
                error_message=f"Download failed - unexpected content type: {content_type}",
                call_updated=self._call_updated,
                ubpr_updated=self._ubpr_updated,
                last_updated=self._get_last_updated_for_product(product),
            )

        # Extract filename
        filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
        filename = (
            filename_match.group(1)
            if filename_match
            else request.get_expected_filename()
        )

        if save_to_disk:
            # Save to disk
            file_path = self.download_dir / filename
            with open(file_path, "wb") as f:
                f.write(response.content)

            return DownloadResult(
                success=True,
                filename=filename,
                size_bytes=len(response.content),
                content_type=content_type,
                file_path=file_path,
                call_updated=self._call_updated,
                ubpr_updated=self._ubpr_updated,
                last_updated=self._get_last_updated_for_product(product),
            )
        else:
            # Return content as file-like object
            from io import BytesIO

            return BytesIO(response.content)

    def _find_period_by_date(
        self, date_str: str, periods: Optional[List[ReportingPeriod]] = None
    ) -> ReportingPeriod:
        """
        Find reporting period by date string

        Args:
            date_str: Date in format MM/DD/YYYY or YYYYMMDD
            periods: List of periods to search (uses self._available_periods if None)

        Returns:
            Matching ReportingPeriod

        Raises:
            ValueError: If date not found
        """
        periods = periods or self._available_periods

        if not periods:
            raise ValueError("No periods available - select product first")

        # Convert YYYYMMDD to MM/DD/YYYY if needed
        if len(date_str) == 8 and date_str.isdigit():
            date_obj = datetime.strptime(date_str, "%Y%m%d")
            date_str = date_obj.strftime("%m/%d/%Y")

        for period in periods:
            if period.date_str == date_str:
                return period

        raise ValueError(f"Period {date_str} not found in available periods")

    def get_latest_period(self, product: Product) -> ReportingPeriod:
        """
        Get the most recent reporting period for a product

        Args:
            product: The product to check

        Returns:
            Most recent ReportingPeriod
        """
        periods = self.select_product(product)
        if not periods:
            raise ValueError(f"No periods available for {product.display_name}")
        return periods[0]  # Periods are returned in descending order

    def download_latest(
        self, product: Product, format: FileFormat = FileFormat.XBRL
    ) -> DownloadResult:
        """
        Download the most recent data for a product

        Args:
            product: The product to download
            format: File format (default: XBRL)

        Returns:
            DownloadResult
        """
        latest_period = self.get_latest_period(product)
        result = self.download(product, latest_period, format)
        assert isinstance(result, DownloadResult)
        return result

    def download_cdr_single_period(
        self, quarter: str, format: FileFormat = FileFormat.XBRL
    ) -> DownloadResult:
        """
        Download Call Report data for a single period
        Convenience method matching your existing API

        Args:
            quarter: Quarter in YYYYMMDD format (e.g., "20240331")
            format: File format (default: XBRL)

        Returns:
            DownloadResult
        """
        result = self.download(Product.CALL_SINGLE, quarter, format)
        assert isinstance(result, DownloadResult)
        return result

    def download_ubpr_single_period(
        self, quarter: str, format: FileFormat = FileFormat.XBRL
    ) -> DownloadResult:
        """
        Download UBPR Ratio data for a single period
        Convenience method matching your existing API

        Args:
            quarter: Quarter in YYYYMMDD format (e.g., "20240331")
            format: File format (default: XBRL)

        Returns:
            DownloadResult
        """
        result = self.download(Product.UBPR_RATIO_SINGLE, quarter, format)
        assert isinstance(result, DownloadResult)
        return result

    def get_bulk_data_sources_cdr(self) -> Dict[str, Union[str, List[str], None]]:
        """
        Get CDR bulk data source information
        Matches your existing /query/bulk_data_sources/cdr endpoint

        Returns:
            Dictionary with published date and available quarters
        """
        periods = self.select_product(Product.CALL_SINGLE)
        published_date: Optional[str] = periods[0].date_str if periods else None

        return {
            "published_date": published_date,
            "available_quarters": [p.yyyymmdd for p in periods],
        }

    def get_bulk_data_sources_ubpr(self) -> Dict[str, Union[str, List[str], None]]:
        """
        Get UBPR bulk data source information
        Matches your existing /query/bulk_data_sources/ubpr endpoint

        Returns:
            Dictionary with published date and available quarters
        """
        periods = self.select_product(Product.UBPR_RATIO_SINGLE)
        published_date: Optional[str] = periods[0].date_str if periods else None

        return {
            "published_date": published_date,
            "available_quarters": [p.yyyymmdd for p in periods],
        }


# Example usage
if __name__ == "__main__":
    # Initialize downloader
    downloader = FFIECDownloader(download_dir=Path("/tmp/ffiec_downloads"))

    # Example 1: Download latest Call Report in XBRL format
    result = downloader.download_latest(Product.CALL_SINGLE, FileFormat.XBRL)
    if result.success:
        print(f"Downloaded: {result.filename} ({result.size_bytes:,} bytes)")

    # Example 2: Download specific quarter UBPR data
    result = downloader.download_ubpr_single_period("20240331", FileFormat.TSV)
    if result.success:
        print(f"Downloaded: {result.filename} to {result.file_path}")

    # Example 3: Get available quarters for CDR
    cdr_info = downloader.get_bulk_data_sources_cdr()
    print(f"Latest CDR data: {cdr_info['published_date']}")
    print(f"Available quarters: {len(cdr_info['available_quarters'])}")

    # Example 4: Download without saving to disk (get content directly)
    from io import BytesIO

    content = downloader.download(
        Product.UBPR_RATIO_SINGLE, "20240331", FileFormat.XBRL, save_to_disk=False
    )
    if isinstance(content, BytesIO):
        print(f"Got file content in memory: {len(content.getvalue())} bytes")
