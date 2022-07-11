# Bank Regulatory Data Collector Tool

## Quick Start

_This repo is in an "alpha" state_

Starts a self-contained docker container containing a RESTful server that interacts with the FFIEC's bulk download facility, allowing for simple GET-based requests for very large datasets.

### Prerequisites
- Linux or MacOS
  - WSL2 is likely to work, but has not been tested
- `arm64`/`aarch64`/`arm64v8` or `amd64`/`x86_64`
- Docker
- Recommend 12-16GB of memory available to the container
  - (memory requirement will decrease in subsequent versions)

__🚨 The RESTful server is intended only for single-user use, and not as an internet-facing production service 🚨__

### Steps

These steps will start a local server running on localhost to which requests may be submitted.

1. Clone the repo
2. Build the container: `make build`
3. Run the RESTful server: `make serve`'
   1. Defaults to `localhost:8080`

## Overview

Acquiring bank regulatory data from US Government regulators should hypothetically be a straightforward task: a download link with a script, ideally.

Instead, downloading bulk data from the Federal Financial Institution Examiners Council (FFIEC) requires clicking on various UI elements, triggering various Javascript functions and collecting various cookies, which then results in content delivered to the browser.

The usual techniques for automating downloads, such as using `curl`, `wget`, using python with `beautifulsoup` or simply cutting-and-pasting a browser link are not possibilities for data acquisition.

Similarly, accessing "webservice" data - the data provided by the FFIEC via a live datafeed, occurs via a relatively old "SOAP" protocol.

## Purpose

This code base, written primarily in python, is intended to be a universal "swiss army knife" for data collection from US bank regulator web site.

Via a RESTful interface, users can now retrieve the latest date of a bulk download release, with data fields normalized for further data input and ingestion.

Currently this library includes only bulk data download capabilities, but will expand to all regulators' data feeds.

## Objective

- Create a (mostly) platform independent means to collect data, including on MacOS (Intel + ARM/Apple Silicon).

- Conduct basic ETL from the source bulk XBRL data, preserving data types.
  - For example, ensuring that float/double values maintain their original values and aren't inadvertently truncated into integers; and that integers are marked as such, so that analysts do not need to reconvert float values back into integers.

- Provide for "zero shot" installation and usage; avoid the need to install, configure, or manage the heavy dependencies required to collect and process the data.
  - Specifically, limit the need to mess around with `selenium` for purposes of programmatic interact with the FFIEC web site.

## Motivation and Acknowledgements

- Elements of this code base were created from a previous effort; this effort utilized the [selenium](https://www.selenium.dev) automation toolkit running inside a docker container running on a cloud instance.

- The repo at  https://github.com/chosak/fdic-call-reports contains some similar functionality; however, the code contained within that repo was not used (or known) when this repo was created.
  - The primary differences are that the `chosak` repo contains a reporting layer, and downloads and processes the data from the original CSV format, while this repo currently only contains a data collection tool, and collects/processes XBRL-formatted data in order to preserve column types.
- Although a "pure" python-based CLI would be ideal, due to the requirement for the use of selenium and a docker container, a REST-based server was required.


## How to Use

### `/query/bulk_data_sources/cdr`
Returns a JSON structure with the published date for the latest bulk data download available for CDR data, and the quarters available for download.

CDR data reflects data contained within the FFIEC 031, 041, and 051 reports.

### `/query/bulk_data_sources/ubpr`
Returns a JSON structure with the published date for the latest bulk data download available for Universal Bank Performance Report data, and the quarters available for download.

### `/download/bulk_data_sources/ubpr`

Downloads a quarterly UBPR dataset, returning the JSON representation of the data. Submitted as a GET request.

#### Required parameters

- `quarter`: the quarter of the dataset requested

#### Example

```
wget http://localhost:8080/download/bulk_data_sources/ubpr?quarter=20090630
```


### `/download/bulk_data_sources/cdr`

Downloads a quarterly CDR dataset, returning the JSON representation of the data. Submitted as a GET request.

#### Required parameters

- `quarter`: the quarter of the dataset requested

#### Example

```
wget http://localhost:8080/download/bulk_data_sources/cdr?quarter=20090630
```

## Notes
- Depending on the speed of your internet connection and the speed of your computer, download and processing time can range from 60 seconds to 10 minutes. Currently, there is no indicator regarding the status of the download and ETL process.

## Known Issues
- The underlying UI for the FFIEC can site be a bit wonky. If you receive a 500 error, try again, and a resubmitted request is likely to succeed.

## Next Steps
- Reduce memory consumption requirements
- Add additional output formatting options
- Add SOAP webservice interface layer
- Improve documentation
- Add status of download and ETL process
- TBD