import io
import re
import sys
from uuid import uuid4
from zipfile import ZipFile
from collections import OrderedDict
from datetime import datetime
import argparse
import requests
import pandas as pd
import numpy as np

"""
Downloads the latest data dictionary ZIP file from the Federal Reserve,
and converts it to JSON records representing the data dictionary.
While the MDRM data dictionary is machine readable, data cleaning steps are
helpful for purposes of joining the MDRM dataset to other datasets.
Version 0.0.1
TODO: Add support for different output formats
"""

DATA_DICTIONARY_URL = "https://www.federalreserve.gov/apps/mdrm/pdf/MDRM.zip"
MDRM_CSV_FILE = "MDRM_CSV.csv"


def iso8601_convert_to_yyyymmdd(t: str) -> str:
    """Converts ISO 8601 date to yyyy-mm-dd
    Args:
        t (str): ISO 8601 date
    Returns:
        str: yyyy-mm-dd format
    """
    ret = datetime.strptime(t, '%m/%d/%Y %H:%M:%S %p')
    ret_str = str(ret.year) + str(ret.month).zfill(2) + str(ret.day).zfill(2)
    return ret_str


def nan_to_none(x: any) -> any:
    """Converts NaN to None
    Args:
        x (str): _description_
    Returns:
        (any | None): returns python None if x is NaN
    """
    if type(x) == float:
        if np.isnan(x):
            return None
        else:
            return x
    else:
        return x


def bad_char_replace(x: str) -> str:
    """Replaces non-processable Windows ISO-8859-1 characters with a zero-length string
    Args:
        x (str): character string
    Returns:
        str: replaced character string
    """
    try:
        return x.replace('&#x0D;', '')
    except Exception as e:
        _ = e  # suppress error message
        return x


def new_line_char_conv(x):
    try:
        return x.replace("\n\n", "\n")
    except Exception as e:
        _ = e
        return x


def remove_cr(x):
    try:
        return x.replace("\r", "")
    except Exception as e:
        _ = e
        return x


def strip_html(text):
    try:
        return re.sub('<[^<]+?>', '', text)
    except Exception as e:
        _ = e
        return text


def collect_latest_data_dictionary_zip() -> bytes:
    """Collects the latest data dictionary zip file from the Federal Reserve
    Collects the latest data dictionary zip file from the Federal Reserve,
    and returns a byte array representing the CSV file contained within the downloaded ZIP file.
    Returns:
        bytes: Byte array representing the CSV file contained within the downloaded ZIP file.
    """
    try:
        response = requests.get(DATA_DICTIONARY_URL)
        response_bytes = response.content
        zip_io = io.BytesIO(response_bytes)
        zip_io.seek(0)
    except Exception as e:
        raise Exception("Error downloading data dictionary zip file: " + str(e))

    zip_obj = ZipFile(zip_io, 'r')
    zip_obj_filelist = zip_obj.namelist()

    # do we have the csv file in the zipfile?
    try:
        assert MDRM_CSV_FILE in zip_obj_filelist
    except AssertionError:
        raise Exception("MDRM CSV file not found in ZIP file")

    # extract the csv file
    csv_bytes = zip_obj.read(MDRM_CSV_FILE)

    return csv_bytes


def process_csv(csv_bytes: bytes) -> pd.DataFrame:
    """Converts the the CSV byte string to a Pandas DataFrame
    Converts the the CSV byte string to a Pandas DataFrame, and returns the DataFrame.
    Cleans the ingested data and converts non-human readable column data to human-readable data.
    Args:
        csv_bytes (bytes): byte string representing the CSV file
    Returns:
        df (pd.DataFrame): Pandas DataFrame representing the attribute data
    """
    # re-encode the csv_bytes to UTF-8
    csv_utf8 = csv_bytes.decode('utf-8')

    df = pd.read_csv(io.StringIO(csv_utf8), skiprows=1)

    # check that we have more than 1 row
    assert df.shape[0] > 1

    """
    These steps are conducted to clean up artifacts from the text data contained in the CSV file.
    """

    # strip the last two columns of html tags
    df['SeriesGlossary'] = df['SeriesGlossary'].apply(strip_html)
    df['Description'] = df['Description'].apply(strip_html)

    # replace bad characters with a zero-length string
    df = df.applymap(bad_char_replace)

    # strip extra newline characters
    df = df.applymap(remove_cr)

    # fix new line characters
    df = df.applymap(new_line_char_conv)

    # remove the last column, which is blank
    df = df.iloc[:, :-1]

    # convert the column names into snake_case
    column_name_change = OrderedDict({
        'Mnemonic': 'mnemonic',
        'Item Code': 'item_code',
        'Start Date': 'start_date',
        'End Date': 'end_date',
        'Item Name': 'item_name',
        'Confidentiality': 'is_conf',
        'ItemType': 'item_type',
        'Reporting Form': 'reporting_form',
        'Description': 'description',
        'SeriesGlossary': 'series_glossary'
    })

    df = df.rename(columns=column_name_change)

    # add human-readable item type descriptors
    item_type_translator = {'J': 'Projected', 'D': 'Derived', 'F': 'Financial reported',
                            'R': 'Rate', 'S': 'Structure', 'E': 'Examination/Supervision Data', 'P': 'Percentage'}

    df['item_type_explain'] = df.item_type.apply(
        lambda x: item_type_translator[x])

    # convert the Y/N flag for confidentiality to a boolean
    df['is_conf'] = df.is_conf.apply(lambda x: True if x == 'Y' else False)

    # # parse the start and end dates into python-format dates
    # uncomment the lines below if running this script manually
    # df['start_date'] = df.start_date.apply(lambda t: datetime.strptime(t, '%m/%d/%Y %H:%M:%S %p'))
    # df['end_date'] = df.end_date.apply(lambda t: datetime.strptime(t, '%m/%d/%Y %H:%M:%S %p'))


    # create an mdrm field that matches the actual field names
    df['mdrm'] = df.apply(lambda x: x['mnemonic'] + x['item_code'], axis=1)

    # drop duplicate rows before we convert the reporting forms to a list
    df = df.drop_duplicates()

    # convert the reporting form comma-delimited string to a list
    df['reporting_forms'] = df.reporting_form.apply(lambda x: x.split(',') if type(x) == str else [])

    # remove the reporting form column
    df = df.drop(columns=['reporting_form'])

    return df

def return_json_mdrm_record():
    data_dict_bytes = collect_latest_data_dictionary_zip()
    data_dict_df = process_csv(data_dict_bytes)
    data_dict_json_output = data_dict_df.to_json(orient='records')
    return data_dict_json_output
    