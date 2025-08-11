"""
FFIEC Website Thumbprint System
Monitors structural changes to FFIEC download pages to detect breaking changes
"""

import hashlib
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests


class WebpageChangeException(Exception):
    """Raised when webpage structure has changed from expected thumbprint"""

    pass


@dataclass
class FormElement:
    """Represents a form element on the page"""

    name: str
    id: str
    type: str
    options: Optional[List[str]] = None

    def to_hash(self) -> str:
        """Generate hash for this element"""
        content = f"{self.name}|{self.id}|{self.type}|{self.options}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class PageThumbprint:
    """
    Captures the structural signature of an FFIEC webpage
    Used to detect breaking changes in the website
    """

    url: str
    timestamp: str
    viewstate_present: bool
    viewstate_generator_present: bool

    # Fields with default values must come after required fields
    version: str = "1.0"
    viewstate_generator_value: Optional[str] = None
    form_elements: List[FormElement] = None
    products: List[Dict[str, str]] = None
    date_format_pattern: Optional[str] = None
    download_button_ids: List[str] = None
    radio_button_ids: List[str] = None
    javascript_files: List[str] = None
    uses_dopostback: bool = False
    uses_webform_postback: bool = False
    structural_hash: Optional[str] = None

    def __post_init__(self):
        """Calculate structural hash after initialization"""
        if not self.structural_hash:
            self.structural_hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """Calculate a hash of the structural elements"""
        components = [
            self.url,
            str(self.viewstate_present),
            str(self.viewstate_generator_present),
            self.viewstate_generator_value or "",
            json.dumps(sorted([e.to_hash() for e in (self.form_elements or [])])),
        ]

        if self.products:
            components.append(json.dumps(sorted([str(p) for p in self.products])))

        if self.download_button_ids:
            components.append(json.dumps(sorted(self.download_button_ids)))

        if self.radio_button_ids:
            components.append(json.dumps(sorted(self.radio_button_ids)))

        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert FormElement objects to dicts
        if self.form_elements:
            data["form_elements"] = [asdict(e) for e in self.form_elements]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "PageThumbprint":
        """Create from dictionary"""
        # Convert form_elements back to FormElement objects
        if "form_elements" in data and data["form_elements"]:
            data["form_elements"] = [FormElement(**e) for e in data["form_elements"]]
        return cls(**data)

    def save(self, filepath: Path) -> None:
        """Save thumbprint to JSON file"""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: Path) -> "PageThumbprint":
        """Load thumbprint from JSON file"""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


class ThumbprintValidator:
    """
    Validates current webpage structure against stored thumbprints
    """

    # Known thumbprints as of 2025-08-08
    KNOWN_THUMBPRINTS = {
        "bulk_download": {
            "url": "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx",
            "viewstate_generator": "651D9554",
            "products": [
                "ReportingSeriesSinglePeriod",
                "ReportingSeriesSubsetSchedulesFourPeriods",
                "PerformanceReportingSeriesSinglePeriod",
                "PerformanceReportingSeriesFourPeriods",
                "PerformanceReportingSeriesRank",
                "PerformanceReportingSeriesStats",
            ],
            "download_button": "ctl00$MainContentHolder$TabStrip1$Download_0",
            "format_radios": ["TSVRadioButton", "XBRLRadiobutton"],
            "date_pattern": r"\d{2}/\d{2}/\d{4}",
        },
        "taxonomy": {
            "url": "https://cdr.ffiec.gov/public/DownloadTaxonomy.aspx",
            "expected_elements": ["DatasetsDropDownList", "ReportingCycleDropDownList"],
        },
        "bhc_financial": {
            "url": "https://www.ffiec.gov/npw/FinancialReport/FinancialDataDownload",
            "expected_elements": ["ReportingCycleDropdown", "DataSeriesDropdown"],
        },
    }

    def __init__(self, thumbprint_dir: Optional[Path] = None):
        """
        Initialize validator

        Args:
            thumbprint_dir: Directory to store/load thumbprints (default: ~/.ffiec_thumbprints)
        """
        self.thumbprint_dir = thumbprint_dir or Path.home() / ".ffiec_thumbprints"
        self.thumbprint_dir.mkdir(parents=True, exist_ok=True)

    def capture_thumbprint(
        self, url: str, page_type: str = "bulk_download"
    ) -> PageThumbprint:
        """
        Capture current thumbprint of a webpage

        Args:
            url: URL to capture
            page_type: Type of page (bulk_download, taxonomy, bhc_financial)

        Returns:
            PageThumbprint object
        """
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        response = session.get(url)
        response.raise_for_status()
        html = response.text

        thumbprint = PageThumbprint(
            url=url,
            timestamp=datetime.now().isoformat(),
            viewstate_present=bool(re.search(r'name="__VIEWSTATE"', html)),
            viewstate_generator_present=bool(
                re.search(r'name="__VIEWSTATEGENERATOR"', html)
            ),
        )

        # Extract ViewState Generator value
        vsg_match = re.search(r'name="__VIEWSTATEGENERATOR".*?value="([^"]+)"', html)
        if vsg_match:
            thumbprint.viewstate_generator_value = vsg_match.group(1)

        # Extract form elements
        thumbprint.form_elements = self._extract_form_elements(html)

        # Extract products (for bulk download page)
        if page_type == "bulk_download":
            thumbprint.products = self._extract_products(html)
            thumbprint.download_button_ids = self._extract_download_buttons(html)
            thumbprint.radio_button_ids = self._extract_radio_buttons(html)

        # Check for JavaScript patterns
        thumbprint.uses_dopostback = "__doPostBack" in html
        thumbprint.uses_webform_postback = "WebForm_DoPostBackWithOptions" in html

        # Extract JavaScript files
        js_files = re.findall(r'<script.*?src="([^"]+)"', html)
        thumbprint.javascript_files = js_files[:10]  # Keep first 10 for reference

        # Detect date format pattern
        date_matches = re.findall(r"\d{2}/\d{2}/\d{4}", html)
        if date_matches:
            thumbprint.date_format_pattern = r"\d{2}/\d{2}/\d{4}"

        return thumbprint

    def _extract_form_elements(self, html: str) -> List[FormElement]:
        """Extract all form elements from HTML"""
        elements = []

        # Extract select elements
        selects = re.findall(
            r'<select[^>]*name="([^"]+)"[^>]*id="([^"]+)"[^>]*>(.*?)</select>',
            html,
            re.DOTALL,
        )
        for name, id_val, content in selects:
            options = re.findall(r'value="([^"]+)"', content)
            elements.append(
                FormElement(name=name, id=id_val, type="select", options=options[:5])
            )

        # Extract input elements
        inputs = re.findall(
            r'<input[^>]*type="([^"]+)"[^>]*name="([^"]+)"[^>]*id="([^"]+)"', html
        )
        for type_val, name, id_val in inputs:
            if not name.startswith("__"):  # Skip ASP.NET internal fields
                elements.append(FormElement(name=name, id=id_val, type=type_val))

        return elements

    def _extract_products(self, html: str) -> List[Dict[str, str]]:
        """Extract product options from ListBox1"""
        products = []
        listbox_match = re.search(r'id="ListBox1"[^>]*>(.*?)</select>', html, re.DOTALL)
        if listbox_match:
            options = re.findall(
                r'value="([^"]+)"[^>]*>([^<]+)</option>', listbox_match.group(1)
            )
            products = [{"value": val, "text": text.strip()} for val, text in options]
        return products

    def _extract_download_buttons(self, html: str) -> List[str]:
        """Extract download button IDs"""
        buttons = re.findall(r'id="(Download[^"]*)"', html)
        return list(set(buttons))

    def _extract_radio_buttons(self, html: str) -> List[str]:
        """Extract radio button IDs"""
        radios = re.findall(r'type="radio"[^>]*id="([^"]+)"', html)
        return list(set(radios))

    def validate(self, url: str, page_type: str = "bulk_download") -> Dict[str, Any]:
        """
        Validate current webpage against known thumbprint

        Args:
            url: URL to validate
            page_type: Type of page

        Returns:
            Dictionary with validation results

        Raises:
            WebpageChangeException: If critical changes detected
        """
        current = self.capture_thumbprint(url, page_type)

        # Load stored thumbprint if exists
        thumbprint_file = self.thumbprint_dir / f"{page_type}_thumbprint.json"

        if thumbprint_file.exists():
            stored = PageThumbprint.load(thumbprint_file)
            differences = self._compare_thumbprints(stored, current)

            if differences["critical_changes"]:
                raise WebpageChangeException(
                    f"Critical changes detected in {url}:\n"
                    + "\n".join(differences["critical_changes"])
                )

            return {
                "valid": not differences["critical_changes"],
                "warnings": differences["warnings"],
                "current_hash": current.structural_hash,
                "stored_hash": stored.structural_hash,
                "last_validated": stored.timestamp,
            }
        else:
            # First run - save thumbprint
            current.save(thumbprint_file)
            return {
                "valid": True,
                "warnings": ["First run - thumbprint saved"],
                "current_hash": current.structural_hash,
                "stored_hash": None,
                "last_validated": current.timestamp,
            }

    def _compare_thumbprints(
        self, stored: PageThumbprint, current: PageThumbprint
    ) -> Dict[str, List[str]]:
        """
        Compare two thumbprints and identify differences

        Returns:
            Dictionary with 'critical_changes' and 'warnings' lists
        """
        critical_changes = []
        warnings = []

        # Critical: ViewState structure changes
        if stored.viewstate_present != current.viewstate_present:
            critical_changes.append(
                f"ViewState presence changed: {stored.viewstate_present} -> {current.viewstate_present}"
            )

        if stored.viewstate_generator_value != current.viewstate_generator_value:
            critical_changes.append(
                f"ViewStateGenerator changed: {stored.viewstate_generator_value} -> {current.viewstate_generator_value}"
            )

        # Critical: Form element changes
        stored_elements = {(e.name, e.id, e.type) for e in (stored.form_elements or [])}
        current_elements = {
            (e.name, e.id, e.type) for e in (current.form_elements or [])
        }

        missing_elements = stored_elements - current_elements
        if missing_elements:
            critical_changes.append(f"Missing form elements: {missing_elements}")

        new_elements = current_elements - stored_elements
        if new_elements:
            warnings.append(f"New form elements found: {new_elements}")

        # Critical: Product changes (for bulk download)
        if stored.products and current.products:
            stored_product_values = {p["value"] for p in stored.products}
            current_product_values = {p["value"] for p in current.products}

            if stored_product_values != current_product_values:
                critical_changes.append("Product options changed")

        # Critical: Download button changes
        if stored.download_button_ids and current.download_button_ids:
            if set(stored.download_button_ids) != set(current.download_button_ids):
                critical_changes.append("Download button IDs changed")

        # Warning: JavaScript changes
        if stored.uses_dopostback != current.uses_dopostback:
            warnings.append(
                f"__doPostBack usage changed: {stored.uses_dopostback} -> {current.uses_dopostback}"
            )

        return {"critical_changes": critical_changes, "warnings": warnings}

    def validate_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Validate all known FFIEC pages

        Returns:
            Dictionary with validation results for each page
        """
        results = {}

        for page_type, config in self.KNOWN_THUMBPRINTS.items():
            try:
                results[page_type] = self.validate(config["url"], page_type)
            except Exception as e:
                results[page_type] = {"valid": False, "error": str(e)}

        return results


# Integration with main downloader
class ValidatedFFIECDownloader:
    """
    FFIEC Downloader with automatic structure validation
    Ensures webpage hasn't changed before attempting downloads
    """

    def __init__(
        self, download_dir: Optional[Path] = None, skip_validation: bool = False
    ):
        """
        Initialize validated downloader

        Args:
            download_dir: Directory for downloads
            skip_validation: Skip thumbprint validation (use with caution)
        """
        from .downloader import FFIECDownloader

        self.downloader = FFIECDownloader(download_dir)
        self.validator = ThumbprintValidator()
        self.skip_validation = skip_validation

    def download(self, *args, **kwargs):
        """
        Download with validation

        Validates webpage structure before attempting download
        """
        if not self.skip_validation:
            validation_result = self.validator.validate(
                "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx",
                "bulk_download",
            )

            if not validation_result["valid"]:
                raise WebpageChangeException(
                    "Cannot proceed with download - webpage structure has changed. "
                    "Please update the downloader to handle new structure."
                )

            if validation_result.get("warnings"):
                print(f"Warnings: {', '.join(validation_result['warnings'])}")

        return self.downloader.download(*args, **kwargs)


# CLI tool for thumbprint management
if __name__ == "__main__":
    import sys

    validator = ThumbprintValidator()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "capture":
            # Capture current thumbprints
            for page_type, config in validator.KNOWN_THUMBPRINTS.items():
                print(f"Capturing thumbprint for {page_type}...")
                try:
                    thumbprint = validator.capture_thumbprint(config["url"], page_type)
                    filepath = validator.thumbprint_dir / f"{page_type}_thumbprint.json"
                    thumbprint.save(filepath)
                    print(f"  Saved to {filepath}")
                    print(f"  Hash: {thumbprint.structural_hash}")
                except Exception as e:
                    print(f"  Error: {e}")

        elif command == "validate":
            # Validate all pages
            print("Validating FFIEC webpages...")
            results = validator.validate_all()

            for page_type, result in results.items():
                print(f"\n{page_type}:")
                if "error" in result:
                    print(f"  ERROR: {result['error']}")
                else:
                    print(f"  Valid: {result['valid']}")
                    if result.get("warnings"):
                        print(f"  Warnings: {', '.join(result['warnings'])}")
                    print(f"  Current hash: {result['current_hash'][:16]}...")

        elif command == "test":
            # Test with sample download
            print("Testing validated downloader...")
            try:
                from .downloader import Product

                downloader = ValidatedFFIECDownloader()
                # This will validate before attempting download
                result = downloader.download_latest(Product.CALL_SINGLE)
                print(f"Success: {result.filename}")
            except WebpageChangeException as e:
                print(f"Validation failed: {e}")
    else:
        print("Usage:")
        print("  python ffiec_thumbprint.py capture  - Capture current thumbprints")
        print(
            "  python ffiec_thumbprint.py validate - Validate against stored thumbprints"
        )
        print("  python ffiec_thumbprint.py test     - Test download with validation")
