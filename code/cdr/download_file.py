from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By

from xbrl import process_file

import os

import time

from .utils import convert_date_format, convert_from_yyyymmdd

def init_download(browser, data_source, quarter, format, download_loc):

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
   
    if data_source == 'UBPR':

        for option in form_list_box.options:
            if option.text == 'UBPR Ratio -- Single Period':
                option.click()
                break
    
    elif data_source == 'CDR':

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


    # convert the selection date to the format expected by the website
    selection_date = convert_from_yyyymmdd(quarter)

    print("selection date is ", selection_date)

    print("list box options are ", [d.text for d in list(year_list_box.options)])

    # select the date in the listbox
    for option in year_list_box.options:
        if option.text == selection_date:
            option.click()
            break


    # click the xbrl button
    browser.find_element(By.ID, 'XBRLRadiobutton').click()

    # wait a couple seconds
    time.sleep(2)

    print("Downloading file...")

    # download the file
    browser.find_element(By.ID, 'Download_0').click()

    file_downloaded = False
    # get the latest file downloaded in the /home/seluser directory
    
    while not file_downloaded:
        files = os.listdir(download_loc)

        print("found files ", files)

        # do we have a .ZIP file in the folder?
        file_still_downloading = any(['part' in f for f in files])

        if not file_still_downloading:
            file_downloaded = True
            break
        print("Waiting for file to download...")
        time.sleep(1)

    print("File downloaded!")
    print("Processing file...", file_downloaded)

    # process the file
    ret_str = process_file.process_xbrl_file(download_loc + "/" + files[-1])

    return ret_str

    return True