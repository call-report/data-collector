# API Reference

## Core Classes

### FFIECDownloader

The main class for downloading FFIEC data.

```python
from ffiec_data_collector import FFIECDownloader
```

#### Constructor

```python
FFIECDownloader(download_dir: Optional[Path] = None)
```

**Parameters:**
- `download_dir` (Path, optional): Directory to save downloaded files. Defaults to current directory.

#### Methods

##### download()

```python
download(
    product: Product,
    period: Union[ReportingPeriod, str],
    format: FileFormat = FileFormat.XBRL,
    save_to_disk: bool = True
) -> Union[DownloadResult, BinaryIO]
```

Download data for specified parameters.

**Parameters:**
- `product`: The product to download (see Product enum)
- `period`: Reporting period as ReportingPeriod object or date string (YYYYMMDD or MM/DD/YYYY)
- `format`: File format (default: XBRL)
- `save_to_disk`: If True, save to disk; if False, return file-like object

**Returns:**
- `DownloadResult` if save_to_disk=True
- `BinaryIO` object if save_to_disk=False

##### download_latest()

```python
download_latest(
    product: Product,
    format: FileFormat = FileFormat.XBRL
) -> DownloadResult
```

Download the most recent data for a product.

**Parameters:**
- `product`: The product to download
- `format`: File format (default: XBRL)

**Returns:**
- `DownloadResult` object

##### select_product()

```python
select_product(product: Product) -> List[ReportingPeriod]
```

Select a product and get available reporting periods.

**Parameters:**
- `product`: The product to select

**Returns:**
- List of `ReportingPeriod` objects

##### get_available_products()

```python
get_available_products() -> List[Product]
```

Get list of all available products.

**Returns:**
- List of `Product` enum values

##### get_bulk_data_sources_cdr()

```python
get_bulk_data_sources_cdr() -> Dict[str, Union[str, List[str]]]
```

Get CDR bulk data source information.

**Returns:**
- Dictionary with:
  - `published_date`: Latest publication date
  - `available_quarters`: List of available quarters in YYYYMMDD format

##### get_bulk_data_sources_ubpr()

```python
get_bulk_data_sources_ubpr() -> Dict[str, Union[str, List[str]]]
```

Get UBPR bulk data source information.

**Returns:**
- Dictionary with:
  - `published_date`: Latest publication date
  - `available_quarters`: List of available quarters in YYYYMMDD format

## Enums

### Product

Available FFIEC data products.

```python
from ffiec_data_collector import Product
```

**Values:**
- `Product.CALL_SINGLE`: Call Reports - Single Period
- `Product.CALL_FOUR_PERIODS`: Call Reports - Balance Sheet, Income Statement, Past Due - Four Periods
- `Product.UBPR_RATIO_SINGLE`: UBPR Ratio - Single Period
- `Product.UBPR_RATIO_FOUR`: UBPR Ratio - Four Periods
- `Product.UBPR_RANK_FOUR`: UBPR Rank - Four Periods
- `Product.UBPR_STATS_FOUR`: UBPR Stats - Four Periods

**Properties:**
- `value`: Form value string
- `display_name`: Human-readable name
- `is_single_period`: True if single period product
- `is_call_report`: True if Call Report product
- `is_ubpr`: True if UBPR product

### FileFormat

Available file formats for download.

```python
from ffiec_data_collector import FileFormat
```

**Values:**
- `FileFormat.TSV`: Tab Delimited format
- `FileFormat.XBRL`: eXtensible Business Reporting Language (XML)

**Properties:**
- `form_value`: Value used in form submission
- `display_name`: Human-readable name
- `mime_type`: MIME type of the format

## Data Classes

### ReportingPeriod

Represents a reporting period/quarter.

```python
@dataclass
class ReportingPeriod:
    value: str        # Form value like "146"
    date_str: str     # Display string like "03/31/2025"
```

**Properties:**
- `date`: datetime object
- `quarter`: Quarter number (1-4)
- `year`: Year as integer
- `yyyymmdd`: Date in YYYYMMDD format

### DownloadResult

Result of a download operation.

```python
from datetime import date

@dataclass
class DownloadResult:
    success: bool
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    content_type: Optional[str] = None
    error_message: Optional[str] = None
    file_path: Optional[Path] = None
    last_updated: Optional[date] = None  # Last updated date for the specific product type
    call_updated: Optional[date] = None  # Call Report last updated date
    ubpr_updated: Optional[date] = None  # UBPR last updated date
```

**New in v2.0.0:** The DownloadResult now includes last updated information from the FFIEC webpage:

- `last_updated`: The relevant last updated date for the downloaded product (either call_updated or ubpr_updated)
- `call_updated`: The "Call Updated" date from the FFIEC webpage
- `ubpr_updated`: The "UBPR Updated" date from the FFIEC webpage

All dates are Python `datetime.date` objects parsed from FFIEC's MM/DD/YYYY format.

### DownloadRequest

Encapsulates a download request with all parameters.

```python
@dataclass
class DownloadRequest:
    product: Product
    period: ReportingPeriod
    format: FileFormat
```

**Methods:**
- `get_expected_filename()`: Generate expected filename based on parameters

## Validation Classes

### ThumbprintValidator

Validates current webpage structure against stored thumbprints.

```python
from ffiec_data_collector import ThumbprintValidator
```

#### Constructor

```python
ThumbprintValidator(thumbprint_dir: Optional[Path] = None)
```

**Parameters:**
- `thumbprint_dir`: Directory to store/load thumbprints (default: ~/.ffiec_thumbprints)

#### Methods

##### capture_thumbprint()

```python
capture_thumbprint(url: str, page_type: str = "bulk_download") -> PageThumbprint
```

Capture current thumbprint of a webpage.

**Parameters:**
- `url`: URL to capture
- `page_type`: Type of page (bulk_download, taxonomy, bhc_financial)

**Returns:**
- `PageThumbprint` object

##### validate()

```python
validate(url: str, page_type: str = "bulk_download") -> Dict[str, Any]
```

Validate current webpage against known thumbprint.

**Parameters:**
- `url`: URL to validate
- `page_type`: Type of page

**Returns:**
- Dictionary with validation results

**Raises:**
- `WebpageChangeException`: If critical changes detected

##### validate_all()

```python
validate_all() -> Dict[str, Dict[str, Any]]
```

Validate all known FFIEC pages.

**Returns:**
- Dictionary with validation results for each page

### ValidatedFFIECDownloader

FFIEC Downloader with automatic structure validation.

```python
from ffiec_data_collector import ValidatedFFIECDownloader
```

#### Constructor

```python
ValidatedFFIECDownloader(
    download_dir: Optional[Path] = None,
    skip_validation: bool = False
)
```

**Parameters:**
- `download_dir`: Directory for downloads
- `skip_validation`: Skip thumbprint validation (use with caution)

### PageThumbprint

Captures the structural signature of an FFIEC webpage.

```python
@dataclass
class PageThumbprint:
    url: str
    timestamp: str
    version: str = "1.0"
    viewstate_present: bool
    viewstate_generator_present: bool
    # ... additional fields
```

**Methods:**
- `calculate_hash()`: Calculate a hash of the structural elements
- `to_dict()`: Convert to dictionary for JSON serialization
- `from_dict()`: Create from dictionary
- `save()`: Save thumbprint to JSON file
- `load()`: Load thumbprint from JSON file

## Exceptions

### WebpageChangeException

Raised when webpage structure has changed from expected thumbprint.

```python
from ffiec_data_collector import WebpageChangeException

try:
    result = downloader.download_latest(Product.CALL_SINGLE)
except WebpageChangeException as e:
    print(f"Website structure changed: {e}")
```

## Convenience Methods

### download_cdr_single_period()

```python
download_cdr_single_period(
    quarter: str,
    format: FileFormat = FileFormat.XBRL
) -> DownloadResult
```

Download Call Report data for a single period.

**Parameters:**
- `quarter`: Quarter in YYYYMMDD format (e.g., "20240331")
- `format`: File format (default: XBRL)

### download_ubpr_single_period()

```python
download_ubpr_single_period(
    quarter: str,
    format: FileFormat = FileFormat.XBRL
) -> DownloadResult
```

Download UBPR Ratio data for a single period.

**Parameters:**
- `quarter`: Quarter in YYYYMMDD format (e.g., "20240331")
- `format`: File format (default: XBRL)