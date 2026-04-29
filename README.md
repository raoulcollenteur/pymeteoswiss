# pymeteoswiss

Simple Python package to extract time series at point locations from MeteoSwiss gridded
climate data.

## Features

- Read MeteoSwiss zipped NetCDF archives from a local folder.
- Extract one or more point time series with nearest-neighbor selection.
- Convert WGS84 latitude/longitude (EPSG:4326) to Swiss LV95 coordinates (EPSG:2056).
- Return results as a `pandas.DataFrame` indexed by time.

## Installation

### From source (recommended during development)

```bash
git clone https://github.com/raoulcollenteur/pymeteoswiss.git
cd pymeteoswiss
uv sync
```

### With pip in an existing environment

```bash
pip install -e .
```

## Quick start

```python
from pathlib import Path
import pymeteoswiss as pms

# Folder containing MeteoSwiss zip files
data_path = Path("examples/data")

# Coordinates in Swiss LV95 (EPSG:2056)
x, y = 2527330, 1163750

df = pms.read_data(
		file_path=data_path,
		variable="RhiresD",
		x=x,
		y=y,
)

print(df.head())
```

## Coordinate conversion helper

If your locations are in latitude/longitude (EPSG:4326), convert them first:

```python
import pymeteoswiss as pms

lat, lon = 46.95, 7.44
x, y = pms.lat_lon_to_e_n(lat=lat, lon=lon)
```

## Data expectations

- Input files are `.zip` archives containing NetCDF files.
- Archives are discovered with pattern `{variable}*.zip` in `file_path`.
- Variable and coordinate names in the NetCDF files are expected to match:
	- variable: value passed in `variable`
	- coordinates: `E` and `N`
- The package so far focusses on the "Ground-based spatial climate data":
  https://github.com/MeteoSwiss/opendata-climate-data
