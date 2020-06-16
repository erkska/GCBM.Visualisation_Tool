import argparse
import glob
import os
import re
import tempfile

import terracotta as tc
from terracotta.server.app import app

from . import arg_types
from .helpers import get_free_port


def start_terracotta(dbpath, port):
    """Load given DB and start a Terracotta server.

    Arguments:

        dbpath: Path to a Terracota-generated DB.
        port: Port number for Terracotta server.
    """
    tc.update_settings(DRIVER_PATH=dbpath, DRIVER_PROVIDER='sqlite')
    app.run(port=port, threaded=False)


def ingest(rasterdir, outputdir):
    """Ingest raster files into a Terracotta database.

    Arguments:

        rasterdir: Path to directory containing raster files.
        outputdir: Path to directory for saving the generated DB.
    """
    TEMP_DB_NAME = 'terracotta.sqlite'
    RASTER_GLOB = r'*.tiff'
    GCBM_RASTER_NAME_PATTERN = r'(?P<title>\w+)_(?P<year>\d{4}).tiff'
    GCBM_RASTER_KEYS = ('title', 'year')
    # TODO: Add descriptions.
    GCBM_RASTER_KEYS_DESCRIPTION = {
        'title': '',
        'year': '',
    }

    driver = tc.get_driver(os.path.join(
        outputdir, TEMP_DB_NAME), provider='sqlite')
    driver.create(GCBM_RASTER_KEYS, GCBM_RASTER_KEYS_DESCRIPTION)

    raster_files = glob.glob(rasterdir + os.sep + RASTER_GLOB)

    for raster_path in raster_files:
        raster_filename = os.path.basename(raster_path)

        match = re.match(GCBM_RASTER_NAME_PATTERN, raster_filename)
        if match is None:
            raise ValueError(
                f'Input file {raster_filename} does not match raster pattern')

        keys = match.groups()

        with driver.connect():
            # TODO: Add metadata.
            driver.insert(keys, raster_path)

    return driver.path


def console():
    """The command-line interface for Taswira"""
    parser = argparse.ArgumentParser(
        description="Interactive visualization tool for GCBM")
    parser.add_argument("config", type=arg_types.indicator_file,
                        help="Path to JSON config file",)
    parser.add_argument("spatial_results", type=arg_types.spatial_results,
                        help="Path to GCBM spatial output")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmpdirname:
        db = ingest(args.spatial_results, tmpdirname)
        port = get_free_port()
        start_terracotta(db, port)