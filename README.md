# FFIEC Data Collector

A lightweight Python library for collecting bulk FFIEC CDR data. Direct HTTP implementation that interfaces with FFIEC's ASP.NET WebForms backend. This version (2.0) is an update from the previous library, which required the use of Selenium and a headless browser. This library does not require any browser automation, making it faster and more efficient.

## Key Functions

- Direct HTTP requests, no browser automation needed
- Access to CDR Bulk Data, UBPR Ratios, Rankings, and Statistics
- Data downloads in XBRL and TSV formats
- Tracks breaking changes in FFIEC's website structure
- No external dependencies like Selenium
- Save to disk or process in memory

## Installation

### Release Candidate (Current)

```bash
# Install the latest release candidate
pip install --pre ffiec-data-collector

# Or install specific RC version
pip install ffiec-data-collector==2.0.0rc1
```

Using uv:
```bash
uv add ffiec-data-collector==2.0.0rc1
```

### Stable Release (Future)

```bash
pip install ffiec-data-collector
```

Using uv:
```bash
uv add ffiec-data-collector
```

### Install from source

Using pip:
```bash
git clone https://github.com/call-report/data-collector.git
cd data-collector
pip install -e .
```

Using uv:
```bash
git clone https://github.com/call-report/data-collector.git
cd data-collector
uv sync --dev
```

## Quick Start

```python
from ffiec_data_collector import FFIECDownloader, Product, FileFormat

# Initialize downloader
downloader = FFIECDownloader()

# Download latest Call Report
result = downloader.download_latest(Product.CALL_SINGLE, FileFormat.XBRL)
print(f"Downloaded: {result.filename}")
print(f"Data last updated: {result.last_updated}")

# Download specific quarter
result = downloader.download_cdr_single_period("20240331")
print(f"Downloaded Q1 2024: {result.filename}")

# Get available quarters
info = downloader.get_bulk_data_sources_cdr()
print(f"Available quarters: {info['available_quarters']}")
```

## Available Data Products

| Product | Description | Periods |
|---------|-------------|---------|
| `CALL_SINGLE` | Call Reports - Single Period | One quarter |
| `CALL_FOUR_PERIODS` | Call Reports - Balance Sheet, Income Statement, Past Due | Four quarters |
| `UBPR_RATIO_SINGLE` | UBPR Ratio - Single Period | One quarter |
| `UBPR_RATIO_FOUR` | UBPR Ratio - Four Periods | Four quarters |
| `UBPR_RANK_FOUR` | UBPR Rank - Four Periods | Four quarters |
| `UBPR_STATS_FOUR` | UBPR Stats - Four Periods | Four quarters |

## Advanced Usage

### Download Multiple Quarters

```python
quarters = ["20240331", "20231231", "20230930", "20230630"]
for quarter in quarters:
    result = downloader.download_cdr_single_period(quarter)
    if result.success:
        print(f"✓ {quarter}: {result.filename}")
```

### Download to Memory

```python
from io import BytesIO

# Get content without saving to disk
content = downloader.download(
    product=Product.CALL_SINGLE,
    period="20240331",
    format=FileFormat.XBRL,
    save_to_disk=False
)

# Process ZIP file in memory
import zipfile
with zipfile.ZipFile(content) as zf:
    for info in zf.filelist:
        print(f"{info.filename}: {info.file_size} bytes")
```

### Website Structure Validation

```python
from ffiec_data_collector import ValidatedFFIECDownloader

# Automatically validates website hasn't changed
validated_downloader = ValidatedFFIECDownloader()
result = validated_downloader.download(
    product=Product.CALL_SINGLE,
    period="20240331"
)
```

### Check Website Health

```python
from ffiec_data_collector import ThumbprintValidator

validator = ThumbprintValidator()
results = validator.validate_all()

for page_type, result in results.items():
    print(f"{page_type}: {'Valid' if result['valid'] else 'Invalid'}")
```

## Command Line Interface

```bash
# Download latest Call Report
ffiec-download --product call-single --format xbrl

# Download specific quarter
ffiec-download --product call-single --quarter 20240331

# Validate website structure
ffiec-validate
```

## Documentation

Full documentation is available at [Read the Docs](https://ffiec-data-collector.readthedocs.io/).

### Building Documentation Locally

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build HTML documentation
cd docs
make html

# View documentation
open _build/html/index.html
```

### Documentation Structure

The documentation includes:
- **Getting Started** - Installation and quick start guide
- **API Reference** - Complete API documentation
- **Examples** - Jupyter notebooks and code examples
- **Development** - Contributing guidelines and development setup

## Examples

See the `examples/` directory for Jupyter notebooks demonstrating:
- Basic downloading workflows
- Bulk data collection
- Building data pipelines
- Processing downloaded data

## API Reference

### FFIECDownloader

Main class for downloading FFIEC data.

**Methods:**
- `download(product, period, format)` - Download specific data
- `download_latest(product, format)` - Download most recent data
- `get_available_products()` - List all products
- `select_product(product)` - Get available periods for product
- `get_bulk_data_sources_cdr()` - Get CDR metadata
- `get_bulk_data_sources_ubpr()` - Get UBPR metadata

### Product Enum

Available data products:
- `Product.CALL_SINGLE` - Call Reports (single period)
- `Product.CALL_FOUR_PERIODS` - Call Reports (four periods)
- `Product.UBPR_RATIO_SINGLE` - UBPR Ratios (single period)
- `Product.UBPR_RATIO_FOUR` - UBPR Ratios (four periods)
- `Product.UBPR_RANK_FOUR` - UBPR Rankings
- `Product.UBPR_STATS_FOUR` - UBPR Statistics

### FileFormat Enum

Supported file formats:
- `FileFormat.XBRL` - eXtensible Business Reporting Language
- `FileFormat.TSV` - Tab-delimited values

## Requirements

- Python 3.8+
- requests
- python-dateutil

## Development

```bash
# Clone repository
git clone https://github.com/call-report/ffiec-data-collector.git
cd ffiec-data-collector

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black ffiec_data_collector/

# Type checking
mypy ffiec_data_collector/
```

## Publishing to PyPI

```bash
# Build distribution packages
python -m build

# Upload to TestPyPI (for testing)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI
python -m twine upload dist/*
```

## License

Mozilla Public License 2.0 - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

## Important Disclaimers

### Government Website Usage Responsibility

**You are responsible for your use of this library with respect to the FFIEC government website.** The FFIEC website has terms of use and acceptable use policies that you must comply with. If you are integrating this code into software applications, you are responsible for implementing appropriate safeguards such as:

- Rate limiting and request throttling
- Circuit breakers to prevent excessive requests
- Monitoring and logging of usage patterns
- Respect for server resources and bandwidth

Failure to use this library responsibly may result in your IP address being blocked or other restrictions imposed by the FFIEC.

### Website Structure Dependencies

**This library relies on the current structure of FFIEC web pages, which were not designed for automated access.** When the library runs, it validates that the assumed structure of the web page remains unchanged. If the FFIEC updates their website structure:

- The library will detect structural changes through its thumbprint validation system
- A `WebpageChangeException` will be raised to prevent incorrect operation
- You will need to update to a newer version of this library that supports the new structure

This design ensures the library fails safely rather than producing incorrect results when the website changes.

### General Disclaimer

This library is not affiliated with, endorsed by, or sponsored by the FFIEC. It is an independent tool for accessing publicly available data. Users are solely responsible for ensuring their usage complies with all applicable terms of service, laws, and regulations.