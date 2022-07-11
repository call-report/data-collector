from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options

from uuid import uuid4

def return_browser(tmp_dir) -> dict:
    """Creates selenium browser object

    Creates selenium browser object and initializes download location

    Returns:
        dict: Dict containing browser object and download location
    """

    s = Service('/usr/bin/geckodriver')


    options = Options()
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.useWindow", False)
    options.set_preference("browser.download.dir", tmp_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                        "application/pdf, application/octet-string, application/force-download")
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(service=s, options=options)


    return driver