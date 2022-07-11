from flask import Flask, request, Response
from cdr import download_dates, last_updated, download_file
from browser import init_browser
import json
from uuid import uuid4
import os
import shutil

app = Flask(__name__)
browser = None

@app.route("/")
def return_rest_options():
    return json.dumps(
        ["/bulk_data_sources"]
    )

@app.route("/query/bulk_data_sources")
def return_cdr_data_sources():
    return json.dumps(["cdr",'ubpr'])

@app.route("/query/bulk_data_sources/cdr")
def return_cdr_dates():
    browser = init_browser.return_browser()
    last_updated_date = last_updated.get_last_updated(browser, source_data="CDR")
    
    return_dict = {
        "last_updated": last_updated_date,
        "quarters": download_dates.populate_download_options(browser, source_data="CDR")
    }

    return return_dict

@app.route("/query/bulk_data_sources/ubpr")
def return_ubpr_dates():
    
    browser = init_browser.return_browser()

    last_updated_date = last_updated.get_last_updated(browser, source_data="UBPR")
    
    return_dict = {
        "last_updated": last_updated_date,
        "quarters": download_dates.populate_download_options(browser, source_data="UBPR")
    }

    return return_dict


@app.route("/download/bulk_data_sources/cdr")
def download_cdr_file():

    tmp_dir = '/tmp/' + str(uuid4())

    browser = init_browser.return_browser(tmp_dir)

    quarter = None
    format = None

    # check for query string parameter named "quarter"
    if "quarter" in request.args:
        quarter = request.args["quarter"]

    if quarter is None:
        # return 400 error if no quarter is specified
        return """A query string parameter named "quarter" is required for this request""", 400

    # download the filedo

    ret_str = download_file.init_download(browser, data_source="CDR", quarter=quarter, format=format, download_loc=tmp_dir)
    
    file_name = "cdr-{}.json".format(quarter)
    response = Response(ret_str)
    response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Length'] = ret_str.__len__()
    response.headers['Cache-Control'] = 'no-cache, must-revalidate'

    # delete the do
    shutil.rmtree(tmp_dir)

    return response
