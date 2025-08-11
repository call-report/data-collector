# Examples

## Basic Usage Examples

### Simple Download

Download the latest Call Report data:

```python
from ffiec_data_collector import FFIECDownloader, Product, FileFormat

downloader = FFIECDownloader()
result = downloader.download_latest(Product.CALL_SINGLE, FileFormat.XBRL)

if result.success:
    print(f"Downloaded: {result.filename}")
    print(f"Size: {result.size_bytes:,} bytes")
    print(f"Location: {result.file_path}")
    print(f"Data last updated: {result.last_updated}")
    print(f"Call Reports updated: {result.call_updated}")
    print(f"UBPR updated: {result.ubpr_updated}")
```

### Download Specific Quarter

```python
# Download Q1 2024 Call Report
result = downloader.download_cdr_single_period("20240331")

# Or using the full method
result = downloader.download(
    product=Product.CALL_SINGLE,
    period="20240331",
    format=FileFormat.TSV
)
```

### List Available Quarters

```python
# Get available quarters for Call Reports
periods = downloader.select_product(Product.CALL_SINGLE)

print(f"Available quarters: {len(periods)}")
print(f"Latest: {periods[0].date_str}")
print(f"Earliest: {periods[-1].date_str}")

# Display recent quarters
for period in periods[:4]:
    print(f"  Q{period.quarter} {period.year}: {period.date_str}")
```

### Working with Last Updated Dates

```python
from datetime import date

# Download and check data freshness
result = downloader.download_latest(Product.CALL_SINGLE)

if result.success and result.last_updated:
    # Calculate days since last update
    today = date.today()
    days_old = (today - result.last_updated).days
    
    print(f"Data is {days_old} days old")
    print(f"Last updated: {result.last_updated}")
    print(f"Call Reports updated: {result.call_updated}")
    print(f"UBPR data updated: {result.ubpr_updated}")
    
    # Check if data is recent enough for your needs
    if days_old > 90:  # More than 90 days old
        print("⚠️  Data may be stale")
    else:
        print("✓ Data is reasonably fresh")
        
    # Format dates for display
    print(f"Last updated (formatted): {result.last_updated.strftime('%B %d, %Y')}")
```

### Compare Update Dates Across Products

```python
from datetime import date, timedelta

# Download different product types and compare their update dates
products = [
    (Product.CALL_SINGLE, "Call Report"),
    (Product.UBPR_RATIO_SINGLE, "UBPR Ratios")
]

results = []
for product, name in products:
    result = downloader.download_latest(product)
    if result.success:
        results.append((name, result))
        print(f"{name}:")
        print(f"  Last updated: {result.last_updated}")
        print(f"  Days old: {(date.today() - result.last_updated).days}")
        print(f"  File: {result.filename}")
        print()

# Find the most recently updated data
if results:
    most_recent = max(results, key=lambda x: x[1].last_updated)
    print(f"Most recently updated: {most_recent[0]} ({most_recent[1].last_updated})")
```

### Data Freshness Filtering

```python
from datetime import date, timedelta

def download_if_fresh(downloader, product, max_age_days=30):
    """Download data only if it's been updated recently"""
    result = downloader.download_latest(product)
    
    if not result.success:
        return None, f"Download failed: {result.error_message}"
    
    if not result.last_updated:
        return result, "Warning: No last updated date available"
    
    days_old = (date.today() - result.last_updated).days
    
    if days_old > max_age_days:
        return None, f"Data is {days_old} days old, exceeds {max_age_days} day limit"
    
    return result, f"Data is fresh ({days_old} days old)"

# Use the function
result, message = download_if_fresh(downloader, Product.CALL_SINGLE, max_age_days=60)
print(message)

if result:
    print(f"Downloaded: {result.filename}")
```

## Advanced Examples

### Bulk Download Multiple Quarters (With Rate Limiting)

```python
from pathlib import Path
import time

downloader = FFIECDownloader(download_dir=Path("./bulk_downloads"))

# Download last 4 quarters with responsible rate limiting
quarters = ["20240331", "20231231", "20230930", "20230630"]
results = []

for quarter in quarters:
    print(f"Downloading {quarter}...", end=" ")
    result = downloader.download_cdr_single_period(quarter)
    results.append(result)
    
    if result.success:
        print(f"✓ ({result.size_bytes:,} bytes)")
    else:
        print(f"✗ Failed: {result.error_message}")
    
    # IMPORTANT: Be respectful to government servers
    # Add delay between requests to avoid overloading the server
    time.sleep(5)  # 5 second delay - adjust as needed

# Summary
successful = sum(1 for r in results if r.success)
print(f"\nCompleted: {successful}/{len(results)} downloads")
```

### Download to Memory for Processing

```python
from io import BytesIO
import zipfile
import xml.etree.ElementTree as ET

# Download without saving to disk
content = downloader.download(
    product=Product.CALL_SINGLE,
    period="20240331",
    format=FileFormat.XBRL,
    save_to_disk=False
)

# Process ZIP content in memory
with zipfile.ZipFile(content) as zf:
    print(f"ZIP contains {len(zf.filelist)} files")
    
    # Process XBRL files
    for file_info in zf.filelist:
        if file_info.filename.endswith('.xml'):
            with zf.open(file_info) as xml_file:
                # Parse XBRL content
                tree = ET.parse(xml_file)
                root = tree.getroot()
                print(f"Processing: {file_info.filename}")
                # Add your XBRL processing logic here
```

### Parallel Downloads

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def download_quarter(downloader, quarter):
    """Download a single quarter"""
    start = datetime.now()
    result = downloader.download_cdr_single_period(quarter)
    duration = (datetime.now() - start).total_seconds()
    return quarter, result, duration

# Quarters to download
quarters = ["20240331", "20231231", "20230930", "20230630"]

# Download in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = {
        executor.submit(download_quarter, downloader, q): q 
        for q in quarters
    }
    
    for future in as_completed(futures):
        quarter, result, duration = future.result()
        if result.success:
            print(f"✓ {quarter}: {result.filename} ({duration:.1f}s)")
        else:
            print(f"✗ {quarter}: Failed after {duration:.1f}s")
```

### Download Different Products

```python
# Download UBPR data
products_to_download = [
    (Product.UBPR_RATIO_SINGLE, "UBPR Ratios"),
    (Product.UBPR_RANK_FOUR, "UBPR Rankings"),
    (Product.UBPR_STATS_FOUR, "UBPR Statistics"),
]

quarter = "20240331"

for product, name in products_to_download:
    print(f"Downloading {name} for {quarter}...")
    result = downloader.download(product, quarter, FileFormat.XBRL)
    
    if result.success:
        print(f"  ✓ Saved: {result.filename}")
        print(f"  Size: {result.size_bytes:,} bytes")
    else:
        print(f"  ✗ Failed: {result.error_message}")
```

## Validation Examples

### Using Validated Downloader

```python
from ffiec_data_collector import ValidatedFFIECDownloader

# This automatically checks website structure before downloading
validated_downloader = ValidatedFFIECDownloader()

try:
    result = validated_downloader.download(
        product=Product.CALL_SINGLE,
        period="20240331",
        format=FileFormat.XBRL
    )
    print(f"✓ Validation passed, downloaded: {result.filename}")
except WebpageChangeException as e:
    print(f"✗ Website structure has changed: {e}")
    print("Please update the library or contact support")
```

### Manual Validation

```python
from ffiec_data_collector import ThumbprintValidator

validator = ThumbprintValidator()

# Validate specific page
result = validator.validate(
    "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx",
    "bulk_download"
)

if result["valid"]:
    print("✓ Website structure is valid")
else:
    print("✗ Website structure has changed")
    
if result.get("warnings"):
    print("Warnings:")
    for warning in result["warnings"]:
        print(f"  - {warning}")
```

### Capture Website Thumbprint

```python
# Capture current website structure
thumbprint = validator.capture_thumbprint(
    "https://cdr.ffiec.gov/public/pws/downloadbulkdata.aspx",
    "bulk_download"
)

print(f"Captured thumbprint:")
print(f"  URL: {thumbprint.url}")
print(f"  Timestamp: {thumbprint.timestamp}")
print(f"  Hash: {thumbprint.structural_hash}")
print(f"  ViewState present: {thumbprint.viewstate_present}")
print(f"  Products: {len(thumbprint.products)} available")

# Save for future validation
from pathlib import Path
thumbprint.save(Path("./my_thumbprint.json"))
```


## Error Handling

```python
from ffiec_data_collector import WebpageChangeException
import requests
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_download(downloader, product, period, format):
    """Download with comprehensive error handling"""
    try:
        logger.info(f"Downloading {product.display_name} for {period}")
        result = downloader.download(product, period, format)
        
        if result.success:
            logger.info(f"Success: {result.filename} ({result.size_bytes:,} bytes)")
            return result
        else:
            logger.error(f"Download failed: {result.error_message}")
            return None
            
    except WebpageChangeException as e:
        logger.error(f"Website structure changed: {e}")
        # Could notify administrators here
        return None
        
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {e}")
        return None
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout: {e}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None

# Use the safe download function
result = safe_download(
    downloader,
    Product.CALL_SINGLE,
    "20240331",
    FileFormat.XBRL
)
```

## Integration with Pandas

```python
import pandas as pd
import zipfile
from io import StringIO

def load_tsv_to_dataframe(downloader, quarter):
    """Download TSV data and load into pandas DataFrame"""
    
    # Download TSV format
    content = downloader.download(
        product=Product.CALL_SINGLE,
        period=quarter,
        format=FileFormat.TSV,
        save_to_disk=False
    )
    
    # Extract TSV files from ZIP
    dataframes = {}
    
    with zipfile.ZipFile(content) as zf:
        for file_info in zf.filelist:
            if file_info.filename.endswith('.txt'):
                with zf.open(file_info) as tsv_file:
                    # Read TSV content
                    tsv_content = tsv_file.read().decode('utf-8')
                    
                    # Load into DataFrame
                    df = pd.read_csv(
                        StringIO(tsv_content),
                        sep='\t',
                        dtype=str  # Keep all as strings initially
                    )
                    
                    # Store with filename as key
                    name = file_info.filename.replace('.txt', '')
                    dataframes[name] = df
                    
                    print(f"Loaded {name}: {len(df)} rows, {len(df.columns)} columns")
    
    return dataframes

# Load Q1 2024 data
dfs = load_tsv_to_dataframe(downloader, "20240331")

# Work with the data
if 'Schedule_RI' in dfs:  # Income Statement
    income_df = dfs['Schedule_RI']
    print(f"\nIncome Statement shape: {income_df.shape}")
    print(income_df.head())
```

## Jupyter Notebook Example

For a comprehensive Jupyter notebook example, see `examples/ffiec_data_collection_demo.ipynb` in the repository. The notebook includes:

- Interactive data exploration
- Visualization examples
- Step-by-step walkthrough
- Data processing workflows
- Integration with common data science libraries