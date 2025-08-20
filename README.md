# Model Munger

[![Run tests](https://github.com/actris-cloudnet/model-munger/actions/workflows/test.yml/badge.svg)](https://github.com/actris-cloudnet/model-munger/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/model-munger.svg)](https://badge.fury.io/py/model-munger)

Extract vertical profiles from numerical weather prediction (NWP) models and
output netCDF files.

## Supported models

| Model                                                                    | Horizontal resolution | Vertical resolution | Temporal resolution | Download                                 |
| ------------------------------------------------------------------------ | --------------------- | ------------------- | ------------------- | ---------------------------------------- |
| [ARPEGE](https://www.umr-cnrm.fr/spip.php?article121&lang=en)            | Native                | 105 model levels    | 1 hour              | Not supported                            |
| [ECMWF open data](https://www.ecmwf.int/en/forecasts/datasets/open-data) | 0.25 degrees          | 13 pressure levels  | 3 hours             | Last days from ECMWF, few years from AWS |
| [GDAS1](https://www.ready.noaa.gov/gdas1.php)                            | 1 degree              | 23 pressure levels  | 3 hours             | Since December 2004                      |

## Processing steps

Model Munger deals with three types of files:

- **Raw data** is model output stored for example as GRIB files. Model Munger
  can download the raw data for some models.
- **Intermediate files** are netCDF files containing vertical profiles in a
  single fixed or moving location. There may be multiple intermediate files, for
  example one for each model run. For some models, Model Munger extracts
  intermediate files from the raw data, but for other models, it uses the output
  from other tools.
- **Output file** is a harmonized netCDF file generated from one or more
  intermediate files. The output file contains up to 24 hours of data from a
  single fixed or moving location, possibly combined from different model runs.

## License

MIT
