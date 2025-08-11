# Getting Started

## Installation

### Requirements

- Python 3.10 or higher
- pip package manager

### Install from PyPI

```bash
pip install ffiec-data-collector
```

### Install from Source

```bash
git clone https://github.com/yourusername/ffiec-data-collector.git
cd ffiec-data-collector
pip install -e .
```

### Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

## Basic Usage

### Import the Library

```python
from ffiec_data_collector import FFIECDownloader, Product, FileFormat
```

### Initialize the Downloader

```python
# Create downloader with default settings
downloader = FFIECDownloader()

# Or specify a custom download directory
from pathlib import Path
downloader = FFIECDownloader(download_dir=Path("/path/to/downloads"))
```

### Download Latest Data

```python
# Download the most recent Call Report
result = downloader.download_latest(Product.CALL_SINGLE, FileFormat.XBRL)

if result.success:
    print(f"Downloaded: {result.filename}")
    print(f"Size: {result.size_bytes:,} bytes")
    print(f"Path: {result.file_path}")
else:
    print(f"Download failed: {result.error_message}")
```

### Download Specific Quarter

```python
# Download Q1 2024 data (March 31, 2024)
result = downloader.download_cdr_single_period("20240331")

# Or use the full download method
result = downloader.download(
    product=Product.CALL_SINGLE,
    period="20240331",  # YYYYMMDD format
    format=FileFormat.XBRL
)
```

### Get Available Quarters

```python
# Get list of available quarters for Call Reports
periods = downloader.select_product(Product.CALL_SINGLE)

# Display the 5 most recent quarters
for period in periods[:5]:
    print(f"Q{period.quarter} {period.year}: {period.date_str}")
```

### Get Metadata

```python
# Get CDR metadata
cdr_info = downloader.get_bulk_data_sources_cdr()
print(f"Latest data: {cdr_info['published_date']}")
print(f"Available quarters: {len(cdr_info['available_quarters'])}")

# Get UBPR metadata
ubpr_info = downloader.get_bulk_data_sources_ubpr()
print(f"Latest UBPR: {ubpr_info['published_date']}")
```

## Data Products

### Call Reports

- **CALL_SINGLE**: Single period, all schedules
- **CALL_FOUR_PERIODS**: Four periods, subset of schedules (Balance Sheet, Income Statement, Past Due)

### UBPR (Uniform Bank Performance Report)

- **UBPR_RATIO_SINGLE**: Single period ratios
- **UBPR_RATIO_FOUR**: Four period ratios
- **UBPR_RANK_FOUR**: Four period rankings
- **UBPR_STATS_FOUR**: Four period statistics

### File Formats

- **XBRL**: eXtensible Business Reporting Language (XML-based)
- **TSV**: Tab-Separated Values (text format)

## Error Handling

```python
try:
    result = downloader.download_latest(Product.CALL_SINGLE)
    if result.success:
        print(f"Success: {result.filename}")
    else:
        print(f"Download failed: {result.error_message}")
except Exception as e:
    print(f"Error: {e}")
```

## Important Usage Guidelines

### Responsible Use of Government Resources

When using this library, you are accessing a government website (FFIEC). Please ensure responsible usage:

```python
import time
from ffiec_data_collector import FFIECDownloader

downloader = FFIECDownloader()

# Example: Add delays between requests
quarters = ["20240331", "20231231", "20230930"]
for quarter in quarters:
    result = downloader.download_cdr_single_period(quarter)
    # Be respectful - add delay between downloads
    time.sleep(5)  # 5 second delay
```

### Production Integration Guidelines

For production systems, implement proper safeguards:

```python
import time
from datetime import datetime, timedelta

class RateLimitedDownloader:
    def __init__(self, requests_per_hour=10):
        self.downloader = FFIECDownloader()
        self.last_request = None
        self.min_interval = 3600 / requests_per_hour  # seconds between requests
    
    def download_with_rate_limit(self, *args, **kwargs):
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()
            if elapsed < self.min_interval:
                sleep_time = self.min_interval - elapsed
                time.sleep(sleep_time)
        
        result = self.downloader.download(*args, **kwargs)
        self.last_request = datetime.now()
        return result

# Use rate-limited downloader
safe_downloader = RateLimitedDownloader(requests_per_hour=6)
```

## Next Steps

- See [API Reference](api_reference.html) for complete documentation
- Check out [Examples](examples.html) for more usage patterns
- Learn about [Website Validation](api_reference.html#validation) for monitoring FFIEC website changes
- Review the [Important Disclaimers](../README.html#important-disclaimers) for responsible usage guidelines