"""
Unit tests for thumbprint validation system
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path
import json
import tempfile

from ffiec_data_collector.thumbprint import (
    ThumbprintValidator, ValidatedFFIECDownloader, PageThumbprint, 
    FormElement, WebpageChangeException
)


class TestFormElement:
    """Test cases for FormElement dataclass"""
    
    def test_form_element_creation(self):
        """Test FormElement creation"""
        element = FormElement(
            name="test_input",
            id="input_id", 
            type="text",
            options=["option1", "option2"]
        )
        
        assert element.name == "test_input"
        assert element.id == "input_id"
        assert element.type == "text"
        assert element.options == ["option1", "option2"]
    
    def test_form_element_hash(self):
        """Test FormElement hash generation"""
        element = FormElement(
            name="test_input",
            id="input_id",
            type="text",
            options=["option1", "option2"]
        )
        
        hash_value = element.to_hash()
        assert isinstance(hash_value, str)
        assert len(hash_value) == 32  # MD5 hash length
        
        # Same element should produce same hash
        element2 = FormElement(
            name="test_input",
            id="input_id",
            type="text", 
            options=["option1", "option2"]
        )
        assert element.to_hash() == element2.to_hash()
        
        # Different element should produce different hash
        element3 = FormElement(
            name="different_input",
            id="input_id",
            type="text",
            options=["option1", "option2"]
        )
        assert element.to_hash() != element3.to_hash()


class TestPageThumbprint:
    """Test cases for PageThumbprint dataclass"""
    
    def test_page_thumbprint_creation(self):
        """Test PageThumbprint creation"""
        form_elements = [
            FormElement(name="input1", id="id1", type="text"),
            FormElement(name="input2", id="id2", type="select", options=["a", "b"])
        ]
        
        thumbprint = PageThumbprint(
            url="https://example.com",
            timestamp=datetime.now().isoformat(),
            viewstate_present=True,
            viewstate_generator_present=True,
            viewstate_generator_value="test_generator",
            form_elements=form_elements,
            products=[{"value": "prod1", "text": "Product 1"}],
            download_button_ids=["download_btn"],
            radio_button_ids=["radio1", "radio2"]
        )
        
        assert thumbprint.url == "https://example.com"
        assert thumbprint.viewstate_present is True
        assert thumbprint.viewstate_generator_present is True
        assert len(thumbprint.form_elements) == 2
        assert len(thumbprint.products) == 1
        assert "download_btn" in thumbprint.download_button_ids
    
    def test_page_thumbprint_hash_calculation(self):
        """Test structural hash calculation"""
        thumbprint = PageThumbprint(
            url="https://example.com",
            timestamp=datetime.now().isoformat(),
            viewstate_present=True,
            viewstate_generator_present=True,
            viewstate_generator_value="test_generator",
            form_elements=[FormElement(name="input1", id="id1", type="text")]
        )
        
        hash_value = thumbprint.calculate_hash()
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hash length
        
        # Hash should be consistent
        assert thumbprint.structural_hash == hash_value
    
    def test_page_thumbprint_serialization(self):
        """Test JSON serialization and deserialization"""
        form_elements = [
            FormElement(name="input1", id="id1", type="text"),
            FormElement(name="input2", id="id2", type="select", options=["a", "b"])
        ]
        
        original = PageThumbprint(
            url="https://example.com",
            timestamp="2025-08-08T12:00:00",
            viewstate_present=True,
            viewstate_generator_present=True,
            form_elements=form_elements
        )
        
        # Test to_dict
        data = original.to_dict()
        assert isinstance(data, dict)
        assert data["url"] == "https://example.com"
        assert len(data["form_elements"]) == 2
        
        # Test from_dict
        recreated = PageThumbprint.from_dict(data)
        assert recreated.url == original.url
        assert recreated.timestamp == original.timestamp
        assert len(recreated.form_elements) == len(original.form_elements)
        assert recreated.form_elements[0].name == original.form_elements[0].name
    
    def test_page_thumbprint_save_load(self):
        """Test saving and loading from file"""
        thumbprint = PageThumbprint(
            url="https://example.com",
            timestamp="2025-08-08T12:00:00",
            viewstate_present=True,
            viewstate_generator_present=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Test save
            thumbprint.save(temp_path)
            assert temp_path.exists()
            
            # Test load
            loaded = PageThumbprint.load(temp_path)
            assert loaded.url == thumbprint.url
            assert loaded.timestamp == thumbprint.timestamp
            assert loaded.structural_hash == thumbprint.structural_hash
        finally:
            temp_path.unlink()


class TestThumbprintValidator:
    """Test cases for ThumbprintValidator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = ThumbprintValidator(thumbprint_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_validator_initialization(self):
        """Test ThumbprintValidator initialization"""
        assert self.validator.thumbprint_dir == self.temp_dir
        assert self.temp_dir.exists()
        
        # Test with default directory
        validator = ThumbprintValidator()
        expected_dir = Path.home() / ".ffiec_thumbprints"
        assert validator.thumbprint_dir == expected_dir
    
    def test_extract_form_elements(self):
        """Test form element extraction from HTML"""
        html_content = '''
        <form>
            <select name="dropdown1" id="select1">
                <option value="opt1">Option 1</option>
                <option value="opt2">Option 2</option>
            </select>
            <input type="text" name="input1" id="text1" />
            <input type="radio" name="radio1" id="radio1" />
        </form>
        '''
        
        elements = self.validator._extract_form_elements(html_content)
        
        # Should find select and inputs (excluding ASP.NET internal fields)
        assert len(elements) >= 2
        
        # Check select element
        select_elements = [e for e in elements if e.type == "select"]
        assert len(select_elements) >= 1
        select_elem = select_elements[0]
        assert select_elem.name == "dropdown1"
        assert select_elem.id == "select1"
        assert "opt1" in select_elem.options or "opt2" in select_elem.options
    
    def test_extract_products(self):
        """Test product extraction from ListBox1"""
        html_content = '''
        <select id="ListBox1" name="ListBox1">
            <option value="ReportingSeriesSinglePeriod">Call Reports -- Single Period</option>
            <option value="PerformanceReportingSeriesSinglePeriod">UBPR Ratio -- Single Period</option>
        </select>
        '''
        
        products = self.validator._extract_products(html_content)
        
        assert len(products) == 2
        assert products[0]["value"] == "ReportingSeriesSinglePeriod"
        assert "Call Reports" in products[0]["text"]
        assert products[1]["value"] == "PerformanceReportingSeriesSinglePeriod"
        assert "UBPR" in products[1]["text"]
    
    def test_extract_download_buttons(self):
        """Test download button extraction"""
        html_content = '''
        <input type="submit" id="Download_0" value="Download" />
        <button id="DownloadButton">Download</button>
        '''
        
        buttons = self.validator._extract_download_buttons(html_content)
        
        assert "Download_0" in buttons
    
    def test_extract_radio_buttons(self):
        """Test radio button extraction"""
        html_content = '''
        <input type="radio" id="TSVRadioButton" name="format" />
        <input type="radio" id="XBRLRadiobutton" name="format" />
        '''
        
        radios = self.validator._extract_radio_buttons(html_content)
        
        assert "TSVRadioButton" in radios
        assert "XBRLRadiobutton" in radios
    
    @patch('ffiec_data_collector.thumbprint.requests.Session')
    def test_capture_thumbprint(self, mock_session_class):
        """Test thumbprint capture with mocked response"""
        # Set up mock
        mock_session = Mock()
        mock_response = Mock()
        mock_response.text = '''
        <html>
            <input type="hidden" name="__VIEWSTATE" value="test_viewstate" />
            <input type="hidden" name="__VIEWSTATEGENERATOR" value="test_generator" />
            <select id="ListBox1" name="ListBox1">
                <option value="ReportingSeriesSinglePeriod">Call Reports</option>
            </select>
            <input type="radio" id="TSVRadioButton" name="format" />
            <input type="submit" id="Download_0" value="Download" />
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        # Test capture
        thumbprint = self.validator.capture_thumbprint(
            "https://test.com",
            "bulk_download"
        )
        
        # Verify results
        assert thumbprint.url == "https://test.com"
        assert thumbprint.viewstate_present is True
        assert thumbprint.viewstate_generator_present is True
        assert thumbprint.viewstate_generator_value == "test_generator"
        assert len(thumbprint.products) == 1
        assert thumbprint.products[0]["value"] == "ReportingSeriesSinglePeriod"
        assert "TSVRadioButton" in thumbprint.radio_button_ids
        assert "Download_0" in thumbprint.download_button_ids
        assert thumbprint.uses_dopostback is False  # Not in test HTML
    
    def test_compare_thumbprints_identical(self):
        """Test comparison of identical thumbprints"""
        thumbprint = PageThumbprint(
            url="https://test.com",
            timestamp="2025-08-08T12:00:00",
            viewstate_present=True,
            viewstate_generator_present=True,
            viewstate_generator_value="test_gen",
            form_elements=[FormElement(name="test", id="test", type="text")],
            products=[{"value": "prod1", "text": "Product 1"}]
        )
        
        # Identical thumbprint
        identical = PageThumbprint(
            url="https://test.com", 
            timestamp="2025-08-08T12:01:00",  # Different timestamp is OK
            viewstate_present=True,
            viewstate_generator_present=True,
            viewstate_generator_value="test_gen",
            form_elements=[FormElement(name="test", id="test", type="text")],
            products=[{"value": "prod1", "text": "Product 1"}]
        )
        
        differences = self.validator._compare_thumbprints(thumbprint, identical)
        
        assert len(differences["critical_changes"]) == 0
        assert len(differences["warnings"]) == 0
    
    def test_compare_thumbprints_critical_changes(self):
        """Test comparison with critical changes"""
        original = PageThumbprint(
            url="https://test.com",
            timestamp="2025-08-08T12:00:00",
            viewstate_present=True,
            viewstate_generator_present=True,
            viewstate_generator_value="old_gen",
            form_elements=[FormElement(name="old_field", id="old_id", type="text")],
            products=[{"value": "old_prod", "text": "Old Product"}]
        )
        
        changed = PageThumbprint(
            url="https://test.com",
            timestamp="2025-08-08T12:01:00",
            viewstate_present=False,  # Critical change
            viewstate_generator_present=True,
            viewstate_generator_value="new_gen",  # Critical change
            form_elements=[FormElement(name="new_field", id="new_id", type="text")],  # Critical change
            products=[{"value": "new_prod", "text": "New Product"}]  # Critical change
        )
        
        differences = self.validator._compare_thumbprints(original, changed)
        
        assert len(differences["critical_changes"]) > 0
        assert any("ViewState presence changed" in change for change in differences["critical_changes"])
        assert any("ViewStateGenerator changed" in change for change in differences["critical_changes"])
        assert any("form elements" in change for change in differences["critical_changes"])
    
    def test_validate_first_run(self):
        """Test validation on first run (no stored thumbprint)"""
        with patch.object(self.validator, 'capture_thumbprint') as mock_capture:
            mock_thumbprint = PageThumbprint(
                url="https://test.com",
                timestamp="2025-08-08T12:00:00", 
                viewstate_present=True,
                viewstate_generator_present=True
            )
            mock_capture.return_value = mock_thumbprint
            
            result = self.validator.validate("https://test.com", "test_page")
            
            assert result["valid"] is True
            assert "First run" in result["warnings"][0]
            assert result["current_hash"] == mock_thumbprint.structural_hash
            assert result["stored_hash"] is None
            
            # Check that thumbprint was saved
            thumbprint_file = self.temp_dir / "test_page_thumbprint.json"
            assert thumbprint_file.exists()


class TestValidatedFFIECDownloader:
    """Test cases for ValidatedFFIECDownloader"""
    
    @patch('ffiec_data_collector.downloader.FFIECDownloader')
    @patch('ffiec_data_collector.thumbprint.ThumbprintValidator')  
    def test_validated_downloader_initialization(self, mock_validator_class, mock_downloader_class):
        """Test ValidatedFFIECDownloader initialization"""
        mock_validator = Mock()
        mock_downloader = Mock()
        mock_validator_class.return_value = mock_validator
        mock_downloader_class.return_value = mock_downloader
        
        # Test with validation enabled
        validated_downloader = ValidatedFFIECDownloader(skip_validation=False)
        
        assert validated_downloader.skip_validation is False
        mock_downloader_class.assert_called_once()
        mock_validator_class.assert_called_once()
    
    @patch('ffiec_data_collector.downloader.FFIECDownloader')
    @patch('ffiec_data_collector.thumbprint.ThumbprintValidator')
    def test_validated_download_success(self, mock_validator_class, mock_downloader_class):
        """Test validated download with successful validation"""
        mock_validator = Mock()
        mock_downloader = Mock()
        mock_validator_class.return_value = mock_validator
        mock_downloader_class.return_value = mock_downloader
        
        # Set up validation result
        mock_validator.validate.return_value = {
            "valid": True,
            "warnings": []
        }
        
        # Set up download result
        mock_download_result = Mock()
        mock_downloader.download.return_value = mock_download_result
        
        validated_downloader = ValidatedFFIECDownloader(skip_validation=False)
        result = validated_downloader.download("arg1", "arg2", kwarg1="value1")
        
        # Verify validation was called
        mock_validator.validate.assert_called_once()
        
        # Verify download was called
        mock_downloader.download.assert_called_once_with("arg1", "arg2", kwarg1="value1")
        
        assert result == mock_download_result
    
    @patch('ffiec_data_collector.downloader.FFIECDownloader')
    @patch('ffiec_data_collector.thumbprint.ThumbprintValidator')
    def test_validated_download_validation_failure(self, mock_validator_class, mock_downloader_class):
        """Test validated download with validation failure"""
        mock_validator = Mock()
        mock_downloader = Mock()
        mock_validator_class.return_value = mock_validator
        mock_downloader_class.return_value = mock_downloader
        
        # Set up validation failure
        mock_validator.validate.return_value = {
            "valid": False,
            "warnings": ["Website structure changed"]
        }
        
        validated_downloader = ValidatedFFIECDownloader(skip_validation=False)
        
        with pytest.raises(WebpageChangeException):
            validated_downloader.download("arg1", "arg2")
        
        # Verify validation was called but download was not
        mock_validator.validate.assert_called_once()
        mock_downloader.download.assert_not_called()
    
    @patch('ffiec_data_collector.downloader.FFIECDownloader')
    @patch('ffiec_data_collector.thumbprint.ThumbprintValidator')
    def test_validated_download_skip_validation(self, mock_validator_class, mock_downloader_class):
        """Test validated download with validation skipped"""
        mock_validator = Mock()
        mock_downloader = Mock()
        mock_validator_class.return_value = mock_validator
        mock_downloader_class.return_value = mock_downloader
        
        mock_download_result = Mock()
        mock_downloader.download.return_value = mock_download_result
        
        validated_downloader = ValidatedFFIECDownloader(skip_validation=True)
        result = validated_downloader.download("arg1", "arg2")
        
        # Verify validation was NOT called
        mock_validator.validate.assert_not_called()
        
        # Verify download was called
        mock_downloader.download.assert_called_once_with("arg1", "arg2")
        
        assert result == mock_download_result


class TestWebpageChangeException:
    """Test cases for WebpageChangeException"""
    
    def test_exception_creation(self):
        """Test WebpageChangeException creation and usage"""
        message = "Test webpage change detected"
        
        with pytest.raises(WebpageChangeException) as exc_info:
            raise WebpageChangeException(message)
        
        assert str(exc_info.value) == message
        assert isinstance(exc_info.value, Exception)


if __name__ == "__main__":
    pytest.main([__file__])