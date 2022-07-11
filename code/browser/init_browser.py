from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By


def return_browser():
    """Creates selenium browser object

    Creates selenium browser object and initializes download location

    Returns:
        _type_: _description_
    """

    s = Service('/usr/bin/geckodriver')

    download_dir = "/home/seluser"

    options = Options()
    options.set_preference("pdfjs.disabled", True)
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.useWindow", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                        "application/pdf, application/octet-string, application/force-download")
    options.add_argument("--headless")
    options.add_argument('--disable-gpu')
    driver = webdriver.Firefox(service=s, options=options)

    return driver