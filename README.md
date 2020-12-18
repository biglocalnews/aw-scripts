# aw-scripts
Misc scripts and other code bits that haven't graduated to their own repos.

## Agenda Watch coverage analysis

The `merge_sites.py` script generates a standardized json file
that merges CivicPlus and Legistar site info and annotates with
FIPS codes for analysis downstream.

Data sources

* **civicplus_sites.csv** - obtained from private civic-scraper repo
* **legistar.json** - generated from DynamoDB using `get_leg_data.sh`
* [Census 2019 FIPS Codes reference file][] - downloaded from Census as Excel and manually converted to CSV

[Census 2019 FIPS Codes reference file]: https://www.census.gov/geographies/reference-files/2019/demo/popest/2019-fips.html
