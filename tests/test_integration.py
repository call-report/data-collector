"""
Integration tests for FFIEC Data Collector

These tests require internet access and will make actual requests to FFIEC servers.
Run with: pytest -m integration

IMPORTANT: These tests should be run sparingly and responsibly to avoid
overloading government servers.
"""

import pytest
from datetime import date
from pathlib import Path
import tempfile
import time

from ffiec_data_collector import (
    FFIECDownloader,
    ValidatedFFIECDownloader,
    Product,
    FileFormat,
    ThumbprintValidator,
    WebpageChangeException,
)


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestFFIECDownloaderIntegration:
    """Integration tests for FFIECDownloader with real FFIEC website"""

    def setup_method(self):
        """Set up test fixtures with temporary directory"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.downloader = FFIECDownloader(download_dir=self.temp_dir)

        # Add delay to be respectful to FFIEC servers
        time.sleep(2)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialize_real_website(self):
        """Test initialization with real FFIEC website"""
        self.downloader.initialize()

        # Should have extracted ViewState
        assert self.downloader._viewstate is not None
        assert self.downloader._viewstate_generator is not None

        # Should have extracted last updated dates
        assert self.downloader._call_updated is not None
        assert self.downloader._ubpr_updated is not None
        assert isinstance(self.downloader._call_updated, date)
        assert isinstance(self.downloader._ubpr_updated, date)

        # Dates should be reasonable (not in the future, not too old)
        today = date.today()
        assert self.downloader._call_updated <= today
        assert self.downloader._ubpr_updated <= today

        # Should be within last 2 years
        from datetime import timedelta

        two_years_ago = today - timedelta(days=730)
        assert self.downloader._call_updated >= two_years_ago
        assert self.downloader._ubpr_updated >= two_years_ago

    def test_get_available_products(self):
        """Test getting available products"""
        products = self.downloader.get_available_products()

        assert len(products) > 0
        assert Product.CALL_SINGLE in products
        assert Product.UBPR_RATIO_SINGLE in products

    def test_select_product_call_reports(self):
        """Test selecting Call Reports product and getting periods"""
        periods = self.downloader.select_product(Product.CALL_SINGLE)

        assert len(periods) > 0

        # Should be sorted with most recent first
        assert periods[0].date >= periods[-1].date

        # Check period properties
        recent_period = periods[0]
        assert recent_period.quarter in [1, 2, 3, 4]
        assert recent_period.year >= 2020
        assert recent_period.yyyymmdd is not None
        assert len(recent_period.yyyymmdd) == 8

    def test_get_bulk_data_sources_cdr(self):
        """Test getting CDR bulk data sources info"""
        info = self.downloader.get_bulk_data_sources_cdr()

        assert "published_date" in info
        assert "available_quarters" in info
        assert len(info["available_quarters"]) > 0

        # Check date format
        published_date = info["published_date"]
        assert "/" in published_date  # MM/DD/YYYY format

        # Check quarters format
        for quarter in info["available_quarters"][:3]:  # Check first 3
            assert len(quarter) == 8  # YYYYMMDD format
            assert quarter.isdigit()

    def test_get_bulk_data_sources_ubpr(self):
        """Test getting UBPR bulk data sources info"""
        info = self.downloader.get_bulk_data_sources_ubpr()

        assert "published_date" in info
        assert "available_quarters" in info
        assert len(info["available_quarters"]) > 0

    @pytest.mark.slow
    def test_download_small_file_to_memory(self):
        """Test downloading a file to memory (no disk save)

        This test downloads actual data but doesn't save to disk,
        minimizing impact while testing the download mechanism.
        """
        # Download to memory to minimize server load
        content = self.downloader.download(
            product=Product.CALL_SINGLE,
            period=self.downloader.select_product(Product.CALL_SINGLE)[0],
            format=FileFormat.XBRL,
            save_to_disk=False,
        )

        # Should return BytesIO object
        from io import BytesIO

        assert isinstance(content, BytesIO)

        # Should have some content
        content_bytes = content.getvalue()
        assert len(content_bytes) > 1000  # Should be substantial

        # Should be a ZIP file
        assert content_bytes.startswith(b"PK")  # ZIP file signature


class TestThumbprintValidatorIntegration:
    """Integration tests for ThumbprintValidator with real website"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = ThumbprintValidator(thumbprint_dir=self.temp_dir)

        # Add delay to be respectful to servers
        time.sleep(2)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_capture_real_thumbprint(self):
        """Test capturing thumbprint from real FFIEC website"""
        thumbprint = self.validator.capture_thumbprint(
            "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx", "bulk_download"
        )

        # Verify basic structure
        assert (
            thumbprint.url == "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx"
        )
        assert thumbprint.viewstate_present is True
        assert thumbprint.viewstate_generator_present is True
        assert thumbprint.viewstate_generator_value is not None

        # Should have found form elements
        assert thumbprint.form_elements is not None
        assert len(thumbprint.form_elements) > 0

        # Should have found products
        assert thumbprint.products is not None
        assert len(thumbprint.products) > 0

        # Should have found the expected products
        product_values = [p["value"] for p in thumbprint.products]
        assert "ReportingSeriesSinglePeriod" in product_values
        assert "PerformanceReportingSeriesSinglePeriod" in product_values

        # Should have download buttons
        assert thumbprint.download_button_ids is not None
        assert len(thumbprint.download_button_ids) > 0

        # Radio buttons may or may not be present depending on website structure
        assert thumbprint.radio_button_ids is not None

        # Should detect JavaScript usage
        assert thumbprint.uses_dopostback is True

        # Should have structural hash
        assert thumbprint.structural_hash is not None
        assert len(thumbprint.structural_hash) == 64  # SHA256

    def test_validate_real_website_first_run(self):
        """Test validation on first run with real website"""
        result = self.validator.validate(
            "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx", "integration_test"
        )

        # First run should succeed and save thumbprint
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert "First run" in result["warnings"][0]
        assert result["current_hash"] is not None
        assert result["stored_hash"] is None

        # Thumbprint file should exist
        thumbprint_file = self.temp_dir / "integration_test_thumbprint.json"
        assert thumbprint_file.exists()

    def test_validate_real_website_second_run(self):
        """Test validation on second run (should match stored thumbprint)"""
        # First run
        result1 = self.validator.validate(
            "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx",
            "integration_test2",
        )

        # Add small delay
        time.sleep(1)

        # Second run
        result2 = self.validator.validate(
            "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx",
            "integration_test2",
        )

        # Second run should validate successfully
        assert result2["valid"] is True
        assert result2["stored_hash"] == result1["current_hash"]


class TestValidatedFFIECDownloaderIntegration:
    """Integration tests for ValidatedFFIECDownloader"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validated_downloader = ValidatedFFIECDownloader(
            download_dir=self.temp_dir, skip_validation=False
        )

        # Add delay to be respectful
        time.sleep(2)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validated_download_with_real_validation(self):
        """Test download with real website validation"""
        # This should work if website structure hasn't changed
        try:
            content = self.validated_downloader.download(
                product=Product.CALL_SINGLE,
                period=self.validated_downloader.downloader.select_product(
                    Product.CALL_SINGLE
                )[0],
                format=FileFormat.XBRL,
                save_to_disk=False,
            )

            # Should succeed and return content
            from io import BytesIO

            assert isinstance(content, BytesIO)
            assert len(content.getvalue()) > 1000

        except WebpageChangeException:
            # This is acceptable - means website structure has changed
            # and the validation system is working correctly
            pytest.skip(
                "Website structure has changed - validation system working correctly"
            )


@pytest.mark.slow
class TestRealDataDownload:
    """
    Slow integration tests that actually download files

    These should be run very sparingly to avoid overloading FFIEC servers
    """

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.downloader = FFIECDownloader(download_dir=self.temp_dir)

        # Longer delay for actual downloads
        time.sleep(5)

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_download_latest_call_report(self):
        """Test downloading latest Call Report (actual file download)

        WARNING: This downloads a real file which can be large (100MB+)
        Only run when necessary for full integration testing
        """
        result = self.downloader.download_latest(Product.CALL_SINGLE, FileFormat.XBRL)

        assert result.success is True
        assert result.filename is not None
        assert result.size_bytes > 1000000  # Should be at least 1MB
        assert result.file_path.exists()
        assert result.last_updated is not None
        assert isinstance(result.last_updated, date)
        assert result.call_updated is not None
        assert result.ubpr_updated is not None

        # File should be a ZIP
        with open(result.file_path, "rb") as f:
            header = f.read(2)
            assert header == b"PK"  # ZIP signature


# Utility function for manual testing
def manual_test_basic_functionality():
    """
    Manual test function for basic functionality
    Can be run independently for quick verification
    """
    print("Testing basic FFIEC Data Collector functionality...")

    downloader = FFIECDownloader()

    # Test initialization
    print("1. Testing initialization...")
    downloader.initialize()
    print(f"   ViewState: {downloader._viewstate[:20]}...")
    print(f"   Call updated: {downloader._call_updated}")
    print(f"   UBPR updated: {downloader._ubpr_updated}")

    # Test getting products
    print("2. Testing product list...")
    products = downloader.get_available_products()
    print(f"   Found {len(products)} products")

    # Test selecting a product
    print("3. Testing product selection...")
    periods = downloader.select_product(Product.CALL_SINGLE)
    print(f"   Found {len(periods)} periods for Call Reports")
    print(f"   Latest: {periods[0]}")

    # Test metadata
    print("4. Testing metadata...")
    cdr_info = downloader.get_bulk_data_sources_cdr()
    print(f"   CDR published: {cdr_info['published_date']}")
    print(f"   Available quarters: {len(cdr_info['available_quarters'])}")

    print("Basic functionality test completed successfully!")


if __name__ == "__main__":
    # Run manual test if called directly
    manual_test_basic_functionality()
