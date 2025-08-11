# Development

## Setting Up Development Environment

### Prerequisites

- Python 3.10 or higher
- Git
- pip and virtualenv

### Clone the Repository

```bash
git clone https://github.com/yourusername/ffiec-data-collector.git
cd ffiec-data-collector
```

### Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate on macOS/Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### Install Development Dependencies

```bash
# Install package in editable mode with dev dependencies
pip install -e ".[dev,docs]"
```

## Project Structure

```
ffiec-data-collector/
├── ffiec_data_collector/       # Main package
│   ├── __init__.py
│   ├── downloader.py          # Core downloader implementation
│   └── thumbprint.py          # Website validation system
├── docs/                       # Documentation
│   ├── conf.py                # Sphinx configuration
│   ├── index.rst              # Documentation index
│   └── *.md                   # Documentation pages
├── examples/                   # Example notebooks and scripts
│   └── ffiec_data_collection_demo.ipynb
├── tests/                      # Test suite
│   ├── test_downloader.py
│   └── test_thumbprint.py
├── setup.py                    # Package configuration
├── requirements.txt            # Core dependencies
├── .readthedocs.yaml          # Read the Docs config
└── README.md                   # Project README
```

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ffiec_data_collector --cov-report=html

# Run specific test file
pytest tests/test_downloader.py

# Run with verbose output
pytest -v
```

### Integration Tests

```bash
# Test actual downloads (requires internet)
pytest tests/test_integration.py -m integration

# Skip integration tests
pytest -m "not integration"
```

### Test Coverage

```bash
# Generate coverage report
pytest --cov=ffiec_data_collector --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=ffiec_data_collector --cov-report=html
# Open htmlcov/index.html in browser
```

## Code Quality

### Formatting with Black

```bash
# Format all code
black ffiec_data_collector/

# Check formatting without changes
black --check ffiec_data_collector/

# Format specific file
black ffiec_data_collector/downloader.py
```

### Linting with Flake8

```bash
# Run linter
flake8 ffiec_data_collector/

# With specific configuration
flake8 --max-line-length=100 ffiec_data_collector/
```

### Type Checking with MyPy

```bash
# Run type checker
mypy ffiec_data_collector/

# With stricter settings
mypy --strict ffiec_data_collector/
```

## Building Documentation

### Local Documentation Build

```bash
cd docs

# Build HTML documentation
make html

# Clean and rebuild
make clean html

# Open in browser (macOS)
open _build/html/index.html

# Open in browser (Linux)
xdg-open _build/html/index.html
```

### Documentation Formats

```bash
# Build different formats
make latexpdf  # PDF via LaTeX
make epub       # ePub format
make json       # JSON format
```

## Building and Publishing

### Build Distribution Packages

```bash
# Install build tools
pip install build twine

# Build source and wheel distributions
python -m build

# Check distribution files
ls dist/
```

### Test with TestPyPI

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ ffiec-data-collector
```

### Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Verify installation
pip install ffiec-data-collector
```

## Contributing

### Development Workflow

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your changes**
5. **Run tests** to ensure nothing broke
6. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a Pull Request** on GitHub

### Code Style Guidelines

- Follow PEP 8 style guide
- Use type hints for all functions
- Add docstrings to all public functions and classes
- Keep line length under 100 characters
- Use descriptive variable names

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

Example:
```
feat: add support for multi-period UBPR downloads

- Implement UBPR_RATIO_FOUR product type
- Add period validation for multi-period products
- Update documentation with new examples

Closes #123
```

## Debugging

### Enable Debug Logging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific module
logger = logging.getLogger('ffiec_data_collector.downloader')
logger.setLevel(logging.DEBUG)
```

### Inspect HTTP Traffic

```python
import requests
import logging
from http.client import HTTPConnection

# Enable HTTP debugging
HTTPConnection.debuglevel = 1

# Configure logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True
```

### Debug ViewState Issues

```python
from ffiec_data_collector import FFIECDownloader

downloader = FFIECDownloader()
downloader.initialize()

# Check ViewState values
print(f"ViewState: {downloader._viewstate[:50]}...")
print(f"ViewStateGenerator: {downloader._viewstate_generator}")
```

## Website Structure Updates

When FFIEC updates their website structure:

### 1. Capture New Thumbprint

```bash
python -m ffiec_data_collector.thumbprint capture
```

### 2. Compare Changes

```python
from ffiec_data_collector import ThumbprintValidator
from pathlib import Path

validator = ThumbprintValidator()

# Load old and new thumbprints
old = PageThumbprint.load(Path("old_thumbprint.json"))
new = validator.capture_thumbprint(
    "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx"
)

# Compare
print(f"Old hash: {old.structural_hash}")
print(f"New hash: {new.structural_hash}")
```

### 3. Update Code

Update the extraction logic in `downloader.py` to handle the new structure.

### 4. Test Changes

```python
# Test with new structure
downloader = FFIECDownloader()
result = downloader.download_latest(Product.CALL_SINGLE)
assert result.success
```

### 5. Submit Pull Request

Include:
- Updated thumbprint files
- Code changes to handle new structure
- Test results showing successful downloads

## Performance Optimization

### Connection Pooling

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure connection pooling and retries
session = requests.Session()
retry = Retry(
    total=3,
    read=3,
    connect=3,
    backoff_factor=0.3
)
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=10,
    max_retries=retry
)
session.mount('http://', adapter)
session.mount('https://', adapter)
```

### Timeout Configuration

```python
# Set appropriate timeouts
downloader.session.timeout = (10, 300)  # (connect, read) in seconds
```

## Release Process

### 1. Update Version

Update version in:
- `setup.py`
- `ffiec_data_collector/__init__.py`
- `docs/conf.py`

### 2. Update Changelog

Add entry to `CHANGELOG.md` with:
- Version number
- Release date
- Changes summary

### 3. Create Release

```bash
# Tag the release
git tag -a v2.0.0 -m "Release version 2.0.0"

# Push tags
git push origin v2.0.0
```

### 4. Build and Upload

```bash
# Clean old builds
rm -rf dist/ build/

# Build distributions
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### 5. Update Documentation

Documentation on Read the Docs updates automatically from the main branch.

## Support

For development questions:
- Open an issue on GitHub
- Check existing issues and pull requests
- Review the documentation

## License

This project is licensed under the Mozilla Public License 2.0 (MPL 2.0). See LICENSE file for details.