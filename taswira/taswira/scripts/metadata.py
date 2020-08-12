"""Functions for extracting metadata from DB generated by GCBM"""
import sqlite3
from collections import OrderedDict

from ..units import Units
from . import get_config

RESULTS_TABLES = {
    "v_flux_indicator_aggregates": "flux_tc",
    "v_flux_indicators": "flux_tc",
    "v_pool_indicators": "pool_tc",
    "v_stock_change_indicators": "flux_tc",
}


def _get_simulation_years(conn):
    years = conn.execute(
        "SELECT MIN(year), MAX(year) from v_age_indicators").fetchone()

    return years


def _find_indicator_table(conn, indicator):
    hansen_jambi_table = {
        'flux': 'flux_reporting_results',
        'stock': 'stock_reporting_results'
    }
    return hansen_jambi_table[indicator], indicator


#    for table, value_col in RESULTS_TABLES.items():
#        if conn.execute(f"SELECT 1 FROM {table} WHERE indicator = ?",
#                        [indicator]).fetchone():
#            return table, value_col
#
#    return None, None


def _get_annual_result(conn, indicator, units=Units.Tc):
    table, value_col = ("flux_reporting_results", "flux")
    _, units_tc, _ = units.value
    start_year, end_year = (1999, 2020)

    db_result = conn.execute(f"""
            SELECT DISTINCT date_dimension_id_fk AS year, COALESCE(SUM({value_col}), 0) / {units_tc} AS value FROM {table}
            WHERE (year BETWEEN {start_year} AND {end_year})
            GROUP BY year
            ORDER BY year
            """).fetchall()

    data = OrderedDict()
    for year, value in db_result:
        data[str(year)] = value

    return data


def get_metadata(db_results):
    """Extract all metadata from non-spatial DB.

    Args:
        db_results: Path to SQLite DB with non-spatial data.

    Returns:
        A dict mapping keys to year-wise values of an indicator.
    """
    metadata = {}
    conn = sqlite3.connect(db_results)
    for config in get_config():
        indicator = config['database_indicator']
        title = config.get('title', indicator)
        metadata[title] = _get_annual_result(conn, indicator)
    return metadata
