"""Module to load data from the MeteoSwiss dataset."""

from bisect import bisect_right
from glob import glob
import os
from zipfile import ZipFile
from xarray import open_dataset
from pandas import concat
from pyproj import Transformer


def lat_lon_to_e_n(lat, lon):
    """
    Converts latitude and longitude (EPSG:4326) to E and N coordinates (EPSG:2056).

    Parameters
    ----------
    lat: float:
        Latitude in degrees.
    lon: float
        Longitude in degrees.

    Returns
    -------
    tuple: A tuple containing the E and N coordinates.

    Notes
    -----
    Latitude and longitude are in degrees, and the output E and N coordinates are in
    the Swiss coordinate system (EPSG:2056). The transformation is performed using the
    pyproj library.

    """
    pyproj_transformer = Transformer.from_crs("EPSG:4326", "EPSG:2056", always_xy=True)
    return pyproj_transformer.transform(lon, lat)


def _coordinate_to_cell_index(coordinates, point):
    """Return the grid-cell index containing a point for a 1D coordinate axis."""
    values = list(coordinates)

    if len(values) == 0:
        raise ValueError("Grid coordinates cannot be empty")
    if len(values) == 1:
        return 0

    descending = values[0] > values[-1]
    ordered_values = values[::-1] if descending else values
    midpoints = [
        (left + right) / 2 for left, right in zip(ordered_values[:-1], ordered_values[1:])
    ]

    edges = [0.0] * (len(ordered_values) + 1)
    edges[1:-1] = midpoints
    edges[0] = ordered_values[0] - (midpoints[0] - ordered_values[0])
    edges[-1] = ordered_values[-1] + (ordered_values[-1] - midpoints[-1])

    if point < edges[0] or point > edges[-1]:
        raise ValueError(
            f"Point {point} lies outside the coordinate range "
            f"[{edges[0]}, {edges[-1]}]"
        )

    index = bisect_right(edges, point) - 1
    index = min(index, len(ordered_values) - 1)

    if descending:
        return len(values) - 1 - index
    return index


def read_data(file_path, variable, x, y, names=None):
    """
    Reads data from a file and returns it as a list of lines.

    Parameters
    ----------
    file_path : str
        The path to the file to read.
    variable : str
        The variable to read from the file.
    x : list
        The list of E coordinates to read.
    y : list
        The list of N coordinates to read.
    names : list, optional
        The list of names to use for the columns in the output DataFrame. If None, the
        columns will be named "0", "1", etc. (default is None).

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the data read from the file, with columns named according
        to the `names` parameter and indexed by time.

    """
    fnames = glob(os.path.join(file_path, f"**{variable}**.zip"))

    print(f"Found {len(fnames)} files for variable '{variable}' in '{file_path}'.")

    # Convert floats to lists to allow for single coordinate input
    if isinstance(x, float) or isinstance(x, int):
        x = [x]
    if isinstance(y, float) or isinstance(y, int):
        y = [y]
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    if names is None:
        names = [f"{i}" for i in range(len(x))]

    dfs = []

    for fname in fnames:
        input_zip = ZipFile(fname)

        for file in input_zip.namelist():
            df = open_dataset(input_zip.extract(file))
            e_coordinates = df.coords["E"].values
            n_coordinates = df.coords["N"].values

            data = {}

            for e, n, name in zip(x, y, names):
                e_index = _coordinate_to_cell_index(e_coordinates, e)
                n_index = _coordinate_to_cell_index(n_coordinates, n)
                data[name] = (
                    df.isel(E=e_index, N=n_index)
                    .to_dataframe()[variable]
                    .squeeze()
                )

            dfs.append(concat(data, axis=1))

            # Cleanup temporary files
            os.remove(input_zip.extract(file))

    combined_data = concat(dfs, axis=0).sort_index()

    return combined_data
