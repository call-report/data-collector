from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

import time

from .utils import convert_date_format

def populate_download_options(browser, source_data="UBPR"):

    browser.get('https://cdr.ffiec.gov/public/PWS/DownloadBulkData.aspx')

    form_list_box = None

    attempt_nums = 0

    while form_list_box is None:
        try:
            form_list_box = Select(browser.find_element(By.ID, "ListBox1"))
        except:
            attempt_nums += 1
            if attempt_nums > 10:
                raise Exception("Could not find form list box")
            time.sleep(1)
   
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

    attempt_nums = 0


    year_list_box = None

    while year_list_box is None:
        try:
            year_list_box = Select(browser.find_element(By.ID, 'DatesDropDownList'))
        except:
            attempt_nums += 1
            if attempt_nums > 10:
                raise Exception("Could not find form list box")
            time.sleep(1)


    potential_dates = [d.text for d in list(year_list_box.options)]
    reformatted_dates = [convert_date_format(d) for d in potential_dates]

    return reformatted_dates