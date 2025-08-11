.. FFIEC Data Collector documentation master file

FFIEC Data Collector Documentation
===================================

A lightweight Python library for collecting bulk FFIEC CDR data.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   responsible_usage
   api_reference
   examples
   development
   changelog

.. important::
   **Government Website Access**: You are accessing a U.S. government website and are responsible for complying with all terms of use and acceptable use policies. This library was not designed for high-frequency access. See :doc:`responsible_usage` for required safeguards and guidelines.

.. warning::
   **Website Structure Dependencies**: This library depends on the current structure of FFIEC web pages, which were not designed for automated access. The library validates website structure before operations and will raise exceptions if changes are detected. See :doc:`responsible_usage` for details.

Overview
--------

The FFIEC Data Collector provides a modern, lightweight approach to downloading bulk financial data from the Federal Financial Institutions Examination Council (FFIEC) Central Data Repository. This library uses direct HTTP requests to interface with FFIEC's ASP.NET WebForms backend, eliminating the need for browser automation tools.

Key Features
------------

* Direct HTTP requests, no browser automation needed
* Access to CDR Bulk Data, UBPR Ratios, Rankings, and Statistics
* Data downloads in XBRL and TSV formats
* Tracks breaking changes in FFIEC's website structure
* No external dependencies like Selenium
* Save to disk or process in memory
 
Quick Example
-------------

.. code-block:: python

   from ffiec_data_collector import FFIECDownloader, Product, FileFormat

   # Initialize downloader
   downloader = FFIECDownloader()

   # Download latest Call Report
   result = downloader.download_latest(Product.CALL_SINGLE, FileFormat.XBRL)
   print(f"Downloaded: {result.filename}")

Installation
------------

Install the package using pip:

.. code-block:: bash

   pip install ffiec-data-collector

Or install from source:

.. code-block:: bash

   git clone https://github.com/yourusername/ffiec-data-collector.git
   cd ffiec-data-collector
   pip install -e .

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`