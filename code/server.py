from flask import Flask
from cdr import download_dates
import json

app = Flask(__name__)



@app.route("/")
def return_rest_options():
    return json.dumps(
        ["/bulk_data_sources"]
    )

@app.route("/bulk_data_sources")
def return_cdr_data_sources():
    return json.dumps(["cdr",'ubpr'])