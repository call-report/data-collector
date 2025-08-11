# Changelog

All notable changes to the FFIEC Data Collector project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-08-08

### Added
- Complete rewrite using direct HTTP requests
- Lightweight implementation without browser automation dependencies
- Website structure validation system with thumbprint monitoring
- Support for all FFIEC data products (Call Reports, UBPR Ratio/Rank/Stats)
- Both XBRL and TSV format support
- In-memory download option for direct data processing
- Comprehensive Python package structure
- Full API documentation
- Jupyter notebook examples
- Read the Docs integration
- Type hints throughout the codebase
- Parallel download support
- Automatic retry logic for failed requests

### Changed
- Migrated from browser automation to direct HTTP requests
- Reduced Docker image size from ~1GB to ~50MB
- Improved download speed by 10-50x
- Reduced memory usage by 95%
- Switched to Mozilla Public License 2.0 (MPL 2.0)

### Removed
- Selenium dependency
- Geckodriver requirement
- Firefox browser dependency
- All browser automation code
- Complex wait and timing logic

### Fixed
- Eliminated timing-related download failures
- Resolved browser memory leaks
- Fixed intermittent element detection issues

## [1.x.x] - Previous Versions

### Legacy Implementation
- Used Selenium WebDriver for browser automation
- Required Firefox and geckodriver
- Implemented page navigation through browser control
- Downloaded files through browser's download mechanism

### Known Issues (Resolved in 2.0.0)
- Large Docker image size
- Slow startup times
- Memory leaks in long-running processes
- Timing-dependent failures
- Complex dependency management

## Migration Guide

### From 1.x to 2.0.0

#### Code Changes

**Old (1.x):**
```python
from selenium import webdriver
driver = webdriver.Firefox()
# Complex browser automation...
```

**New (2.0.0):**
```python
from ffiec_data_collector import FFIECDownloader
downloader = FFIECDownloader()
result = downloader.download_latest(Product.CALL_SINGLE)
```

#### Docker Changes

**Old Dockerfile:**
```dockerfile
FROM selenium/standalone-firefox:latest
# ~1GB image with browser
```

**New Dockerfile:**
```dockerfile
FROM python:3.11-slim
RUN pip install ffiec-data-collector
# ~50MB image
```

#### API Endpoints (Backward Compatible)

The following methods maintain backward compatibility:
- `download_cdr_single_period(quarter)`
- `download_ubpr_single_period(quarter)`
- `get_bulk_data_sources_cdr()`
- `get_bulk_data_sources_ubpr()`

## Roadmap

### Version 2.1.0 (Planned)
- [ ] Add support for BHC (Bank Holding Company) data
- [ ] Implement incremental download detection
- [ ] Add data validation utilities
- [ ] Create CLI with progress bars

### Version 2.2.0 (Future)
- [ ] Add support for additional FFIEC data sources
- [ ] Implement data transformation utilities
- [ ] Add cloud storage integration (S3, GCS, Azure)
- [ ] Create Docker Hub official image

## Support

For migration assistance or questions about changes:
- See [Development Guide](development.html)
- Open an issue on GitHub
- Review [API Reference](api_reference.html) for new methods

## License Note

Starting with version 2.0.0, this project is licensed under the Mozilla Public License 2.0 (MPL 2.0).
Previous versions may have been under different licensing terms.