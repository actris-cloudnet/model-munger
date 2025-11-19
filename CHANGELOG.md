# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.3.3 – 2025-11-19

- Handle time in older ARPEGE files

## 0.3.2 – 2025-11-14

- Process levels online to reduce memory usage

## 0.3.1 – 2025-08-20

- Add `sfc_geopotential` and `sfc_height` to `ecmwf-open`

## 0.3.0 – 2025-08-11

- Add GDAS1 support
- Add `source` attribute to netCDF output
- Add `comment` attribute to `rh` variable in netCDF output

## 0.2.0 – 2025-04-15

- Support moving sites
- Add `--steps` argument

## 0.1.5 – 2025-02-10

- Handle missing values in `ecmwf-open` extractor

## 0.1.4 – 2025-02-07

- Improve handling of missing variables when merging models
- Reduce logging for non-interactive sessions

## 0.1.3 – 2025-01-29

- Fix processing date ranges in CLI

## 0.1.2 – 2025-01-28

- Handle missing variables in `ecmwf-open`

## 0.1.1 – 2025-01-28

- Support "today" and "yesterday" values in CLI

## 0.1.0 – 2025-01-28

- Add ARPEGE support
- Add support for intermediate files

## 0.0.2 – 2024-10-07

- Fix password environment variable

## 0.0.1 – 2024-10-07

- Initial release with ECMWF open data support
