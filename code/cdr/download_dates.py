from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By


s = Service('/usr/bin/geckodriver')
download_dir = "/home/seluser"

options = Options()
options.set_preference("pdfjs.disabled", True)
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.manager.useWindow", False)
options.set_preference("browser.download.dir", download_dir)
options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
                       "application/pdf, application/force-download")
options.add_argument("--headless")
options.add_argument('--disable-gpu')
driver = webdriver.Firefox(service=s, options=options)


import random
import time
import os
from glob import glob
import tarfile
from datetime import datetime
import shutil
import io
import sys
import hashlib
import zipfile
from time import sleep
import json
import concurrent.futures
from hashlib import sha256
from uuid import uuid4
from pathlib import Path


def populate_download_options(browser, source_data="UBPR"):

    browser.get('https://cdr.ffiec.gov/public/PWS/DownloadBulkData.aspx')
    form_list_box = Select(browser.find_element(By.ID, "ListBox1"))

    if source_data == 'UBPR':

        for option in form_list_box.options:
            if option.text == 'UBPR Ratio -- Single Period':
                option.click()
                break
    
    elif source_data == 'CDR':

        for option in form_list_box.options:
            if option.text == 'Call Reports -- Single Period':
                option.click()
                break

    year_list_box = Select(browser.find_element(By.ID, 'DatesDropDownList'))

    potential_dates = [d.text for d in list(year_list_box.options)]

    return potential_dates