"""
Unit tests for FFIECDownloader class
"""

import pytest
from unittest.mock import Mock, patch
from datetime import date
from pathlib import Path

from ffiec_data_collector.downloader import (
    FFIECDownloader,
    Product,
    FileFormat,
    ReportingPeriod,
    DownloadResult,
    DownloadRequest,
)


class TestFFIECDownloader:
    """Test cases for FFIECDownloader class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.downloader = FFIECDownloader()

    def test_initialization(self):
        """Test FFIECDownloader initialization"""
        # Test default initialization
        downloader = FFIECDownloader()
        assert downloader.download_dir == Path.cwd()
        assert downloader._viewstate is None
        assert downloader._viewstate_generator is None

        # Test with custom download directory
        custom_dir = Path("/tmp/test_downloads")
        downloader = FFIECDownloader(download_dir=custom_dir)
        assert downloader.download_dir == custom_dir

    def test_extract_viewstate(self):
        """Test ViewState extraction from HTML"""
        html_content = """
        <html>
            <input type="hidden" name="__VIEWSTATE" value="test_viewstate_value" />
            <input type="hidden" name="__VIEWSTATEGENERATOR" value="test_generator_value" />
        </html>
        """

        viewstate, generator = self.downloader._extract_viewstate(html_content)
        assert viewstate == "test_viewstate_value"
        assert generator == "test_generator_value"

    def test_extract_viewstate_missing(self):
        """Test ViewState extraction with missing values"""
        html_content = "<html><body>No ViewState here</body></html>"

        with pytest.raises(ValueError, match="Could not extract ViewState"):
            self.downloader._extract_viewstate(html_content)

    def test_extract_last_updated_dates(self):
        """Test extraction of last updated dates from HTML"""
        html_content = """
        <div>
            Call Updated: 7/15/2025      UBPR Updated: 6/30/2025
        </div>
        """

        call_updated, ubpr_updated = self.downloader._extract_last_updated_dates(
            html_content
        )

        assert call_updated == date(2025, 7, 15)
        assert ubpr_updated == date(2025, 6, 30)

    def test_extract_last_updated_dates_missing(self):
        """Test extraction when dates are missing"""
        html_content = "<html><body>No dates here</body></html>"

        call_updated, ubpr_updated = self.downloader._extract_last_updated_dates(
            html_content
        )

        assert call_updated is None
        assert ubpr_updated is None

    def test_extract_last_updated_dates_partial(self):
        """Test extraction when only one date is present"""
        html_content = "Call Updated: 7/15/2025"

        call_updated, ubpr_updated = self.downloader._extract_last_updated_dates(
            html_content
        )

        assert call_updated == date(2025, 7, 15)
        assert ubpr_updated is None

    def test_extract_last_updated_dates_invalid_format(self):
        """Test extraction with invalid date format"""
        html_content = "Call Updated: invalid-date      UBPR Updated: 2025/06/30"

        call_updated, ubpr_updated = self.downloader._extract_last_updated_dates(
            html_content
        )

        # Should handle invalid dates gracefully
        assert call_updated is None
        assert ubpr_updated is None

    def test_get_last_updated_for_product(self):
        """Test getting last updated date for specific product types"""
        # Set up test dates
        self.downloader._call_updated = date(2025, 7, 15)
        self.downloader._ubpr_updated = date(2025, 6, 30)

        # Test Call Report product
        call_date = self.downloader._get_last_updated_for_product(Product.CALL_SINGLE)
        assert call_date == date(2025, 7, 15)

        # Test UBPR product
        ubpr_date = self.downloader._get_last_updated_for_product(
            Product.UBPR_RATIO_SINGLE
        )
        assert ubpr_date == date(2025, 6, 30)

    def test_get_available_products(self):
        """Test getting list of available products"""
        products = self.downloader.get_available_products()

        assert isinstance(products, list)
        assert len(products) > 0
        assert all(isinstance(p, Product) for p in products)
        assert Product.CALL_SINGLE in products
        assert Product.UBPR_RATIO_SINGLE in products


class TestDownloadResult:
    """Test cases for DownloadResult dataclass"""

    def test_download_result_creation(self):
        """Test DownloadResult creation with all fields"""
        result = DownloadResult(
            success=True,
            filename="test_file.zip",
            size_bytes=1024,
            content_type="application/zip",
            file_path=Path("/tmp/test_file.zip"),
            last_updated=date(2025, 7, 15),
            call_updated=date(2025, 7, 15),
            ubpr_updated=date(2025, 6, 30),
        )

        assert result.success is True
        assert result.filename == "test_file.zip"
        assert result.size_bytes == 1024
        assert result.content_type == "application/zip"
        assert result.last_updated == date(2025, 7, 15)
        assert result.call_updated == date(2025, 7, 15)
        assert result.ubpr_updated == date(2025, 6, 30)

    def test_download_result_minimal(self):
        """Test DownloadResult with minimal required fields"""
        result = DownloadResult(success=False, error_message="Test error")

        assert result.success is False
        assert result.error_message == "Test error"
        assert result.filename is None
        assert result.last_updated is None


class TestReportingPeriod:
    """Test cases for ReportingPeriod dataclass"""

    def test_reporting_period_properties(self):
        """Test ReportingPeriod property calculations"""
        # Q1 2024
        period = ReportingPeriod(value="146", date_str="03/31/2024")

        assert period.quarter == 1
        assert period.year == 2024
        assert period.yyyymmdd == "20240331"
        assert period.date.month == 3
        assert period.date.day == 31
        assert period.date.year == 2024

    def test_reporting_period_quarters(self):
        """Test quarter calculation for different months"""
        test_cases = [
            ("03/31/2024", 1),  # Q1
            ("06/30/2024", 2),  # Q2
            ("09/30/2024", 3),  # Q3
            ("12/31/2024", 4),  # Q4
        ]

        for date_str, expected_quarter in test_cases:
            period = ReportingPeriod(value="1", date_str=date_str)
            assert period.quarter == expected_quarter

    def test_reporting_period_string_representation(self):
        """Test string representation of ReportingPeriod"""
        period = ReportingPeriod(value="146", date_str="03/31/2024")
        expected = "Q1 2024 (03/31/2024)"
        assert str(period) == expected


class TestDownloadRequest:
    """Test cases for DownloadRequest dataclass"""

    def test_expected_filename_generation(self):
        """Test expected filename generation for different scenarios"""
        period = ReportingPeriod(value="146", date_str="03/31/2024")

        # Test Call Report XBRL
        request = DownloadRequest(
            product=Product.CALL_SINGLE, period=period, format=FileFormat.XBRL
        )
        expected = "FFIEC CDR Call Bulk XBRL 03312024.zip"
        assert request.get_expected_filename() == expected

        # Test Call Report TSV
        request = DownloadRequest(
            product=Product.CALL_SINGLE, period=period, format=FileFormat.TSV
        )
        expected = "FFIEC CDR Call Bulk TSV 03312024.zip"
        assert request.get_expected_filename() == expected

        # Test UBPR
        request = DownloadRequest(
            product=Product.UBPR_RATIO_SINGLE, period=period, format=FileFormat.XBRL
        )
        expected = "FFIEC CDR UBPR Ratio  Single Period XBRL 03312024.zip"
        assert request.get_expected_filename() == expected


class TestProductEnum:
    """Test cases for Product enum"""

    def test_product_properties(self):
        """Test Product enum properties"""
        # Test Call Report
        call_product = Product.CALL_SINGLE
        assert call_product.is_call_report is True
        assert call_product.is_ubpr is False
        assert call_product.is_single_period is True

        # Test UBPR
        ubpr_product = Product.UBPR_RATIO_SINGLE
        assert ubpr_product.is_call_report is False
        assert ubpr_product.is_ubpr is True
        assert ubpr_product.is_single_period is True

        # Test multi-period
        multi_product = Product.CALL_FOUR_PERIODS
        assert multi_product.is_single_period is False

    def test_product_values(self):
        """Test Product enum values and display names"""
        call_single = Product.CALL_SINGLE
        assert call_single.form_value == "ReportingSeriesSinglePeriod"
        assert "Call Reports" in call_single.display_name
        assert "Single Period" in call_single.display_name


class TestFileFormatEnum:
    """Test cases for FileFormat enum"""

    def test_file_format_properties(self):
        """Test FileFormat enum properties"""
        # Test XBRL
        xbrl = FileFormat.XBRL
        assert xbrl.form_value == "XBRLRadiobutton"
        assert "XBRL" in xbrl.display_name
        assert xbrl.mime_type == "application/xml"

        # Test TSV
        tsv = FileFormat.TSV
        assert tsv.form_value == "TSVRadioButton"
        assert "Tab Delimited" in tsv.display_name
        assert tsv.mime_type == "text/tab-separated-values"


# Mock tests for methods that require network access
class TestFFIECDownloaderMocked:
    """Test cases using mocked network requests"""

    @patch("ffiec_data_collector.downloader.requests.Session")
    def test_initialize_with_mock(self, mock_session_class):
        """Test initialization with mocked HTTP response"""
        # Set up mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = """
            <input type="hidden" name="__VIEWSTATE" value="mock_viewstate" />
            <input type="hidden" name="__VIEWSTATEGENERATOR" value="mock_generator" />
            Call Updated: 7/15/2025      UBPR Updated: 6/30/2025
        """
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        # Test initialization
        downloader = FFIECDownloader()
        downloader.initialize()

        # Verify results
        assert downloader._viewstate == "mock_viewstate"
        assert downloader._viewstate_generator == "mock_generator"
        assert downloader._call_updated == date(2025, 7, 15)
        assert downloader._ubpr_updated == date(2025, 6, 30)

        # Verify session was called
        mock_session.get.assert_called_once_with(downloader.BASE_URL)

    def test_find_period_by_date(self):
        """Test finding period by date string"""
        # Set up test periods
        periods = [
            ReportingPeriod(value="146", date_str="03/31/2024"),
            ReportingPeriod(value="145", date_str="12/31/2023"),
            ReportingPeriod(value="144", date_str="09/30/2023"),
        ]

        downloader = FFIECDownloader()
        downloader._available_periods = periods

        # Test MM/DD/YYYY format
        found_period = downloader._find_period_by_date("03/31/2024", periods)
        assert found_period.value == "146"

        # Test YYYYMMDD format
        found_period = downloader._find_period_by_date("20240331", periods)
        assert found_period.value == "146"

        # Test not found
        with pytest.raises(ValueError, match="Period .* not found"):
            downloader._find_period_by_date("01/01/2024", periods)


if __name__ == "__main__":
    pytest.main([__file__])
