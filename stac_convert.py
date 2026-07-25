#!/usr/bin/env python3
"""
Auto-convert a raw raster into a STAC Item (with the SAR extension).

This is the CORE of Server A in the Hainan project: "raw SAR -> standardized STAC".
Pure-Python (no heavy deps) so it always runs; if `rasterio` is present it reads the
real bbox/CRS, otherwise it uses the metadata you pass in.

Run:
    python stac_convert.py            # writes haishao_sample_stac.json
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any


def create_stac_item(
    item_id: str,
    bbox: list[float],
    datetime_iso: str,
    assets: dict[str, str],
    *,
    platform: str = "HaiShao-1",
    instrument: str = "SAR",
    polarizations: list[str] | None = None,
    frequency_band: str = "C",
    gsd: float = 10.0,
    epsg: int = 4326,
) -> dict[str, Any]:
    """Build a STAC Item dict (SAR extension) from basic metadata.

    bbox = [min_lon, min_lat, max_lon, max_lat].
    assets = {"hh": "s3://.../hh.tif", "hv": "..."}.
    """
    polarizations = polarizations or ["HH", "HV"]
    min_lon, min_lat, max_lon, max_lat = bbox
    geometry = {
        "type": "Polygon",
        "coordinates": [[
            [min_lon, min_lat], [max_lon, min_lat],
            [max_lon, max_lat], [min_lon, max_lat], [min_lon, min_lat],
        ]],
    }
    item = {
        "type": "Feature",
        "stac_version": "1.0.0",
        "stac_extensions": [
            "https://stac-extensions.github.io/sar/v1.0.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        ],
        "id": item_id,
        "bbox": bbox,
        "geometry": geometry,
        "properties": {
            "datetime": datetime_iso,
            "platform": platform,
            "instruments": [instrument],
            "gsd": gsd,
            "proj:epsg": epsg,
            # --- SAR extension fields ---
            "sar:instrument_mode": "IW",
            "sar:frequency_band": frequency_band,
            "sar:polarizations": polarizations,
            "sar:product_type": "GRD",
            "sar:observation_direction": "right",
        },
        "assets": {
            name: {
                "href": href,
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "roles": ["data"],
                "sar:polarizations": [name.upper()],
            }
            for name, href in assets.items()
        },
        "links": [],
    }
    return item


def from_raster(path: str, item_id: str, datetime_iso: str) -> dict[str, Any]:
    """Read bbox/EPSG from a real raster if rasterio is available."""
    try:
        import rasterio
        from rasterio.warp import transform_bounds
    except ImportError:
        raise SystemExit("rasterio not installed; use create_stac_item() directly.")
    with rasterio.open(path) as ds:
        b = ds.bounds
        bbox = list(transform_bounds(ds.crs, "EPSG:4326", b.left, b.bottom, b.right, b.top))
        epsg = ds.crs.to_epsg() or 4326
    return create_stac_item(item_id, bbox, datetime_iso,
                            {"hh": path}, epsg=epsg)


if __name__ == "__main__":
    # Synthetic but realistic "HaiShao" SAR scene over the Hainan coast.
    item = create_stac_item(
        item_id="HAISHAO1_SAR_20250118_HAINAN_0001",
        bbox=[109.10, 18.20, 110.05, 19.05],
        datetime_iso=_dt.datetime(2025, 1, 18, 2, 34, 11,
                                  tzinfo=_dt.timezone.utc).isoformat(),
        assets={
            "hh": "s3://haishao-open-data/2025/01/18/HAISHAO1_..._HH.tif",
            "hv": "s3://haishao-open-data/2025/01/18/HAISHAO1_..._HV.tif",
        },
    )
    with open("haishao_sample_stac.json", "w") as f:
        json.dump(item, f, indent=2)
    print(json.dumps(item, indent=2))
    print("\nwrote haishao_sample_stac.json")
