# Responsible Usage Guidelines

## Government Website Access

### Your Responsibilities

When using this library, you are accessing the Federal Financial Institutions Examination Council (FFIEC) website, which is a U.S. government resource. **You are solely responsible for ensuring your use of this library complies with:**

- FFIEC website terms of use and acceptable use policies
- Federal regulations regarding automated access to government systems

### Required Safeguards for Production Use

If you are integrating this library into production software, you **must** implement appropriate safeguards:

#### 1. Rate Limiting

```python
import time
from datetime import datetime, timedelta

class ResponsibleDownloader:
    def __init__(self, max_requests_per_hour=10):
        self.downloader = FFIECDownloader()
        self.request_times = []
        self.max_requests_per_hour = max_requests_per_hour
    
    def can_make_request(self):
        now = datetime.now()
        # Remove requests older than 1 hour
        self.request_times = [t for t in self.request_times 
                             if now - t < timedelta(hours=1)]
        return len(self.request_times) < self.max_requests_per_hour
    
    def download_with_limits(self, *args, **kwargs):
        if not self.can_make_request():
            raise Exception("Rate limit exceeded. Please wait before making more requests.")
        
        result = self.downloader.download(*args, **kwargs)
        self.request_times.append(datetime.now())
        
        # Add minimum delay between requests
        time.sleep(3)
        
        return result
```

#### 2. Circuit Breaker Pattern

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Requests blocked
    HALF_OPEN = "half_open" # Testing if service recovered

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is open - too many recent failures")
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            raise e

# Usage
breaker = CircuitBreaker()
try:
    result = breaker.call(downloader.download_latest, Product.CALL_SINGLE)
except Exception as e:
    print(f"Request failed or circuit breaker triggered: {e}")
```

#### 3. Request Monitoring and Logging

```python
import logging
from datetime import datetime

class MonitoredDownloader:
    def __init__(self):
        self.downloader = FFIECDownloader()
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.session_start = datetime.now()
    
    def download_with_monitoring(self, *args, **kwargs):
        self.request_count += 1
        self.logger.info(f"Request #{self.request_count} initiated at {datetime.now()}")
        
        try:
            result = self.downloader.download(*args, **kwargs)
            if result.success:
                self.logger.info(f"Download successful: {result.filename} ({result.size_bytes:,} bytes)")
            else:
                self.logger.warning(f"Download failed: {result.error_message}")
            return result
        except Exception as e:
            self.logger.error(f"Download exception: {e}")
            raise
    
    def get_usage_stats(self):
        session_duration = datetime.now() - self.session_start
        return {
            "requests_made": self.request_count,
            "session_duration": session_duration,
            "requests_per_hour": self.request_count / (session_duration.total_seconds() / 3600)
        }
```

## Website Structure Dependencies

### How the Library Works

This library interacts with FFIEC web pages that **were not designed for automated access**. The pages use ASP.NET WebForms with:

- ViewState tokens for session management
- JavaScript form submissions
- Dynamic HTML generation
- Complex form interactions

### Structural Validation System

The library includes a "thumbprint" validation system that:

1. **Captures the current structure** of FFIEC web pages
2. **Validates before each operation** that the structure hasn't changed
3. **Fails safely** if changes are detected

```python
from ffiec_data_collector import WebpageChangeException

try:
    result = downloader.download_latest(Product.CALL_SINGLE)
except WebpageChangeException as e:
    print(f"FFIEC website structure has changed: {e}")
    print("Please update to a newer version of this library")
    # Consider implementing fallback behavior or alerting
```

### When Website Changes Occur

If FFIEC updates their website:

1. **Detection**: The library will detect structural changes
2. **Prevention**: A `WebpageChangeException` will prevent incorrect operation
3. **Resolution**: You must update to a newer version that supports the new structure

### Monitoring Website Changes

```python
from ffiec_data_collector import ThumbprintValidator

def check_website_health():
    validator = ThumbprintValidator()
    results = validator.validate_all()
    
    for page_type, result in results.items():
        if not result.get('valid', True):
            print(f"WARNING: {page_type} structure has changed")
            return False
    return True

# Run before critical operations
if not check_website_health():
    print("Website structure issues detected - aborting automated process")
    exit(1)
```

## Best Practices Summary

### DO:
- ✅ Add delays between requests (minimum 3-5 seconds)
- ✅ Implement rate limiting (maximum 10-20 requests per hour)
- ✅ Use circuit breakers for production systems
- ✅ Monitor and log all requests
- ✅ Handle `WebpageChangeException` gracefully
- ✅ Test with small datasets first
- ✅ Respect server resources and bandwidth

### DON'T:
- ❌ Make rapid, successive requests
- ❌ Download the same data repeatedly
- ❌ Ignore error messages or exceptions
- ❌ Run unmonitored bulk download operations
- ❌ Assume the website structure will never change
- ❌ Use in high-frequency trading or time-sensitive applications

## Legal and Compliance Considerations

### Terms of Service Compliance

You are responsible for:
- Reading and understanding FFIEC website terms of use
- Ensuring your usage patterns comply with acceptable use policies
- Monitoring for any usage restrictions or requirements

### Documentation and Audit Trail

For regulated environments, maintain:
- Logs of all download requests and responses
- Documentation of data usage and retention policies
- Audit trails for compliance reporting

### Example Compliance-Ready Implementation

```python
import json
from datetime import datetime
from pathlib import Path

class ComplianceDownloader:
    def __init__(self, audit_log_path="./audit_log.json"):
        self.downloader = ResponsibleDownloader(max_requests_per_hour=5)
        self.audit_log = Path(audit_log_path)
        self.load_audit_log()
    
    def load_audit_log(self):
        if self.audit_log.exists():
            with open(self.audit_log) as f:
                self.audit_data = json.load(f)
        else:
            self.audit_data = {"downloads": [], "summary": {}}
    
    def save_audit_log(self):
        with open(self.audit_log, 'w') as f:
            json.dump(self.audit_data, f, indent=2, default=str)
    
    def compliant_download(self, product, period, purpose="data_analysis"):
        # Record request
        request_record = {
            "timestamp": datetime.now().isoformat(),
            "product": product.display_name,
            "period": str(period),
            "purpose": purpose,
            "user": "system",  # or actual user ID
        }
        
        try:
            result = self.downloader.download_with_limits(product, period)
            request_record.update({
                "success": result.success,
                "filename": result.filename,
                "size_bytes": result.size_bytes,
                "file_path": str(result.file_path) if result.file_path else None
            })
        except Exception as e:
            request_record.update({
                "success": False,
                "error": str(e)
            })
            raise
        finally:
            self.audit_data["downloads"].append(request_record)
            self.save_audit_log()
        
        return result

# Usage with full audit trail
compliance_downloader = ComplianceDownloader()
result = compliance_downloader.compliant_download(
    Product.CALL_SINGLE, 
    "20240331",
    purpose="Regulatory compliance analysis"
)
```

Remember: **You are accessing a government resource funded by taxpayers. Use it responsibly.**