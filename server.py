#!/usr/bin/env python3
"""
Open Data with MCP — live-demo MCP server.

Exposes the *Registry of Open Data on AWS* (Sentinel-2 L2A) and a remote-sensing
analysis tool as Model Context Protocol (MCP) tools, so that ANY MCP-capable
LLM client (Claude Desktop, IDEs, custom agents, ...) can discover and call them.

This mirrors the two agents of the Hainan land-sea SAR project:
  - Server A: data standardization & discovery  -> `search_open_data`, `describe_item`
  - Server B: remote-sensing ToolBox            -> `segment_water`

Design goals for a *live* demo:
  - The STAC search hits a REAL AWS-hosted Open Data endpoint (Sentinel-2 on AWS).
  - The segmentation tool runs a real model path if `geoai` is installed, and
    otherwise falls back to a deterministic, dependency-free stub so the demo
    NEVER fails on stage (e.g. no GPU / no network for the model step).

Run:
    pip install "mcp[cli]" pystac-client          # minimal
    # optional, for real inference: pip install geoai-py rasterio numpy
    python server.py                              # stdio transport (for MCP clients)

Talking point: ~100 lines turns open data + a model into agent-ready capabilities.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

# ----------------------------------------------------------------------------
# AWS Open Data endpoint (Sentinel-2 L2A, cloud-optimized, hosted on AWS).
# This is genuinely part of the Registry of Open Data on AWS.
# ----------------------------------------------------------------------------
STAC_ENDPOINT = "https://earth-search.aws.element84.com/v1/"
COLLECTION = "sentinel-2-l2a"

# ----------------------------------------------------------------------------
# Multi-source registry: several POPULAR open satellite catalogs, spanning
# resolutions from ~1 m to ~500 m. Same MCP tool, many data sources.
#   - NAIP           ~0.6-1 m   very-high-res aerial (US)       [Planetary Computer]
#   - Sentinel-2 L2A  10 m      optical                          [AWS Earth Search]
#   - Landsat C2 L2   30 m      long archive (since 1982)        [Planetary Computer]
#   - VIIRS Black Marble ~500 m NIGHTTIME / low-light EO         [NASA Earthdata]
# STAC *search* is open (no auth) for the first three; asset download on
# Planetary Computer needs free signing (pip install planetary-computer).
# ----------------------------------------------------------------------------
SOURCES: dict[str, dict[str, Any]] = {
    "sentinel-2": {
        "title": "Sentinel-2 L2A (optical, 10 m)",
        "endpoint": "https://earth-search.aws.element84.com/v1/",
        "collection": "sentinel-2-l2a",
        "gsd_m": 10, "provider": "AWS Open Data / Element84",
        "cloud_field": "eo:cloud_cover", "requires_signing": False,
        "preview_assets": ["red", "green", "blue", "nir"],
    },
    "naip": {
        "title": "NAIP aerial imagery (very high-res, ~0.6-1 m)",
        "endpoint": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "collection": "naip",
        "gsd_m": 0.6, "provider": "Microsoft Planetary Computer / USDA",
        "cloud_field": None, "requires_signing": True,
        "preview_assets": ["image"],
        "note": "US coverage only; pick a US bbox for this source.",
    },
    "landsat": {
        "title": "Landsat Collection 2 L2 (30 m, archive since 1982)",
        "endpoint": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "collection": "landsat-c2-l2",
        "gsd_m": 30, "provider": "Microsoft Planetary Computer / USGS",
        "cloud_field": "eo:cloud_cover", "requires_signing": True,
        "preview_assets": ["red", "green", "blue", "nir08"],
    },
    "sentinel-1": {
        "title": "Sentinel-1 GRD (SAR, all-weather, 10 m)",
        "endpoint": "https://earth-search.aws.element84.com/v1/",
        "collection": "sentinel-1-grd",
        "gsd_m": 10, "provider": "AWS Open Data / Element84",
        "cloud_field": None, "requires_signing": False,
        "preview_assets": ["vv", "vh"],
        "note": "Synthetic-aperture radar: sees through cloud and at night, "
                "complementing optical. Mirrors the HaiShao SAR program. Also on "
                "Planetary Computer (sentinel-1-rtc) and ALOS PALSAR (L-band).",
    },
    "nightlights": {
        "title": "VIIRS nighttime lights (low-light EO, ~500 m)",
        "endpoint": "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi",
        "collection": "VIIRS_SNPP_DayNightBand_ENCC",
        "gsd_m": 500, "provider": "NASA GIBS (VIIRS DNB / Black Marble)",
        "cloud_field": None, "requires_signing": False, "requires_auth": False,
        "access": "wms",  # imagery via WMS/tiles, not STAC items
        "layers": ["VIIRS_SNPP_DayNightBand_ENCC", "VIIRS_Black_Marble"],
        "note": "Nighttime / low-light EO via NASA GIBS WMS (OPEN, no auth). "
                "Use get_nightlights(bbox, date). Maps city lights, fishing "
                "fleets, power outages, urban growth.",
        "reference": "https://blackmarble.gsfc.nasa.gov/",
    },
    "thermal-lst": {
        "title": "MODIS land surface temperature (thermal IR, 1 km)",
        "endpoint": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "collection": "modis-11A2-061",
        "gsd_m": 1000, "provider": "Microsoft Planetary Computer / NASA MODIS",
        "cloud_field": None, "requires_signing": True,
        "preview_assets": ["LST_Day_1km"],
        "note": "Thermal infrared surface temperature (heat). Scale 0.02 K.",
    },
    "weather-goes": {
        "title": "GOES ABI weather imagery (thermal IR clouds, ~2 km)",
        "endpoint": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "collection": "goes-cmi",
        "gsd_m": 2000, "provider": "Microsoft Planetary Computer / NOAA GOES",
        "cloud_field": None, "requires_signing": True,
        "preview_assets": ["C13_2km"],
        "note": "Geostationary weather (Americas). Band 13 = clean IR window.",
    },
    "sst": {
        "title": "NOAA OISST sea-surface temperature (~25 km)",
        "endpoint": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "collection": "noaa-cdr-sea-surface-temperature-optimum-interpolation",
        "gsd_m": 25000, "provider": "Microsoft Planetary Computer / NOAA",
        "cloud_field": None, "requires_signing": True,
        "preview_assets": ["sst"],
        "note": "Ocean proxy (fronts, warm currents). True current velocity "
                "needs CMEMS (registration) or NOAA OSCAR/HYCOM via ERDDAP. "
                "Solar irradiance: NASA POWER API (open, no registration).",
    },
}

mcp = FastMCP("open-data-mcp")


# ============================================================================
# Server A — Open Data discovery / standardization
# ============================================================================
@mcp.tool()
def search_open_data(
    bbox: list[float],
    datetime_range: str | None = None,
    max_items: int = 5,
    max_cloud_cover: float = 20.0,
) -> dict[str, Any]:
    """Search the Registry of Open Data on AWS (Sentinel-2 L2A) via STAC.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat]. Example (Hainan coast):
              [109.0, 18.0, 111.0, 20.0]
        datetime_range: STAC datetime, e.g. "2025-01-01/2025-06-30". Optional.
        max_items: max scenes to return (default 5).
        max_cloud_cover: keep scenes below this cloud-cover % (default 20).

    Returns a compact, agent-friendly list of scenes (id, datetime, cloud %, assets).
    """
    try:
        from pystac_client import Client
    except ImportError:
        return {
            "error": "pystac-client not installed. Run: pip install pystac-client",
            "hint": "The live demo needs this for the real STAC query.",
        }

    client = Client.open(STAC_ENDPOINT)
    search = client.search(
        collections=[COLLECTION],
        bbox=bbox,
        datetime=datetime_range,
        query={"eo:cloud_cover": {"lt": max_cloud_cover}},
        max_items=max_items,
        sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
    )

    items = []
    for item in search.items():
        items.append(
            {
                "id": item.id,
                "datetime": str(item.datetime),
                "cloud_cover": round(item.properties.get("eo:cloud_cover", -1), 2),
                "assets": {
                    band: item.assets[band].href
                    for band in ("red", "green", "blue", "nir", "swir16", "swir22")
                    if band in item.assets
                },
            }
        )

    return {
        "endpoint": STAC_ENDPOINT,
        "collection": COLLECTION,
        "count": len(items),
        "items": items,
        "note": "Open data on AWS, now discoverable by any MCP client.",
    }


@mcp.tool()
def describe_item(item_id: str, bbox: list[float]) -> dict[str, Any]:
    """Return STAC-style metadata for one scene (standardization preview).

    Demonstrates Server A's 'metadata extraction + STAC standardization' step:
    the same shape we use to publish national SAR ('HaiShao') with a SAR Extension.
    """
    try:
        from pystac_client import Client
    except ImportError:
        return {"error": "pip install pystac-client"}

    client = Client.open(STAC_ENDPOINT)
    search = client.search(collections=[COLLECTION], bbox=bbox, ids=[item_id], max_items=1)
    items = list(search.items())
    if not items:
        return {"error": f"item {item_id} not found in {bbox}"}
    it = items[0]
    item_dict = it.to_dict()
    properties = item_dict.get("properties", it.properties)
    return {
        "stac_version": item_dict.get("stac_version", "1.0.0"),
        "id": item_dict.get("id", it.id),
        "collection": item_dict.get("collection", getattr(it, "collection_id", None)),
        "datetime": properties.get("datetime", str(it.datetime)),
        "bbox": item_dict.get("bbox", it.bbox),
        "properties": {
            k: properties[k]
            for k in ("eo:cloud_cover", "platform", "gsd", "proj:epsg")
            if k in properties
        },
        "n_assets": len(it.assets),
    }


# ============================================================================
# Server A (multi-source) — one MCP tool, many popular open catalogs
# ============================================================================
@mcp.tool()
def list_sources() -> dict[str, Any]:
    """List the open satellite data sources this server can query.

    Lets an agent choose a source by *resolution* (NAIP ~1 m, Sentinel-2 10 m,
    Landsat 30 m, VIIRS nighttime lights ~500 m) or by *phenomenon* (e.g.
    nighttime / low-light EO). Same MCP tool, many data sources.
    """
    return {
        "sources": {
            k: {
                "title": v["title"],
                "gsd_m": v["gsd_m"],
                "provider": v["provider"],
                "collection": v["collection"],
                "requires_signing": v.get("requires_signing", False),
                "requires_auth": v.get("requires_auth", False),
            }
            for k, v in SOURCES.items()
        },
        "note": "From ~1 m aerial to ~500 m nighttime lights, all behind one protocol.",
    }


@mcp.tool()
def search_catalog(
    source: str,
    bbox: list[float],
    datetime_range: str | None = None,
    max_items: int = 5,
    max_cloud_cover: float = 30.0,
) -> dict[str, Any]:
    """Search ANY registered open catalog by name (see `list_sources`).

    Args:
        source: one of the keys from `list_sources` (e.g. "naip", "sentinel-2",
                "landsat", "nightlights").
        bbox: [min_lon, min_lat, max_lon, max_lat]. NAIP needs a US bbox.
        datetime_range: STAC datetime, e.g. "2023-06-01/2023-09-30".
        max_items: max scenes to return.
        max_cloud_cover: cloud filter (ignored for sources without cloud metadata).

    Demonstrates multi-source, multi-resolution discovery through one MCP tool.
    """
    if source not in SOURCES:
        return {"error": f"unknown source '{source}'", "available": list(SOURCES)}
    src = SOURCES[source]

    # WMS/imagery sources (e.g. nighttime lights) are not STAC-searchable.
    if src.get("access") == "wms":
        return {
            "source": source,
            "title": src["title"],
            "native_gsd_m": src["gsd_m"],
            "provider": src["provider"],
            "access": "wms (imagery, not STAC items)",
            "hint": "call get_nightlights(bbox, date) for a ready-to-render image URL",
            "reference": src.get("reference"),
        }

    # Auth-gated sources are advertised, not fetched.
    if src.get("requires_auth"):
        return {
            "source": source,
            "title": src["title"],
            "native_gsd_m": src["gsd_m"],
            "provider": src["provider"],
            "note": src.get("auth_note", "requires provider login"),
            "reference": src.get("reference"),
        }

    try:
        from pystac_client import Client
    except ImportError:
        return {"error": "pip install pystac-client"}

    kwargs: dict[str, Any] = dict(
        collections=[src["collection"]], bbox=bbox,
        datetime=datetime_range, max_items=max_items,
    )
    if src.get("cloud_field"):
        kwargs["query"] = {src["cloud_field"]: {"lt": max_cloud_cover}}
        kwargs["sortby"] = [{"field": f"properties.{src['cloud_field']}", "direction": "asc"}]

    client = Client.open(src["endpoint"])
    search = client.search(**kwargs)

    # Planetary Computer asset hrefs must be signed to download (free token).
    signer = None
    if src.get("requires_signing"):
        try:
            import planetary_computer as pc
            signer = pc.sign
        except ImportError:
            signer = None

    items = []
    for it in search.items():
        assets = {}
        for a in src["preview_assets"]:
            if a in it.assets:
                href = it.assets[a].href
                assets[a] = signer(href) if signer else href
        cloud = it.properties.get(src["cloud_field"]) if src.get("cloud_field") else None
        items.append({
            "id": it.id,
            "datetime": str(it.datetime),
            "gsd_m": it.properties.get("gsd", src["gsd_m"]),
            "cloud_cover": round(cloud, 2) if isinstance(cloud, (int, float)) else None,
            "assets": assets,
        })

    return {
        "source": source,
        "title": src["title"],
        "endpoint": src["endpoint"],
        "collection": src["collection"],
        "native_gsd_m": src["gsd_m"],
        "count": len(items),
        "items": items,
        "signing": ("applied" if signer else
                    ("needed: pip install planetary-computer" if src.get("requires_signing") else "n/a")),
    }


@mcp.tool()
def get_nightlights(
    bbox: list[float],
    date: str = "2023-01-01",
    layer: str = "VIIRS_SNPP_DayNightBand_ENCC",
    width: int = 512,
    height: int = 512,
) -> dict[str, Any]:
    """Fetch an OPEN nighttime-lights image for a bbox from NASA GIBS (no auth).

    Low-light / nighttime Earth observation (VIIRS Day-Night Band, ~500 m).
    Reveals *human activity*: city lights, fishing fleets, gas flares, power
    outages, and urban growth — the "microlight" view of the planet.

    Args:
        bbox: [min_lon, min_lat, max_lon, max_lat]. E.g. Pearl River Delta:
              [113.8, 22.1, 114.5, 22.8].
        date: acquisition date "YYYY-MM-DD".
        layer: "VIIRS_SNPP_DayNightBand_ENCC" (daily) or "VIIRS_Black_Marble".
        width, height: output pixels.

    Returns a ready-to-render PNG URL (NASA GIBS WMS, open, no login).
    """
    import urllib.parse
    if layer not in SOURCES["nightlights"]["layers"]:
        return {"error": f"unknown layer '{layer}'",
                "available": SOURCES["nightlights"]["layers"]}
    min_lon, min_lat, max_lon, max_lat = bbox
    params = {
        "SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap",
        "LAYERS": layer, "SRS": "EPSG:4326",
        "BBOX": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "WIDTH": width, "HEIGHT": height, "FORMAT": "image/png", "TIME": date,
    }
    url = SOURCES["nightlights"]["endpoint"] + "?" + urllib.parse.urlencode(params)
    return {
        "source": "nightlights",
        "layer": layer,
        "date": date,
        "bbox": bbox,
        "native_gsd_m": 500,
        "provider": "NASA GIBS (VIIRS DNB / Black Marble)",
        "image_url": url,
        "format": "image/png",
        "auth": "none (open)",
        "note": "Nighttime / low-light EO; render or download the URL directly.",
    }


# ============================================================================
# Server B — Remote-sensing ToolBox (one of the 5 Hainan models: segmentation)
# ============================================================================
@mcp.tool()
def segment_water(red_href: str, green_href: str, blue_href: str, nir_href: str) -> dict[str, Any]:
    """Water-body segmentation on a Sentinel-2 scene (one ToolBox model).

    Pass the asset hrefs returned by `search_open_data`. If `geoai`/`rasterio`
    are available it runs a real NDWI-based water mask; otherwise it returns a
    deterministic stub so the live demo always succeeds.
    """
    try:
        import rasterio
        from rasterio.enums import Resampling
    except ImportError:
        # ---- graceful stub: keeps the stage demo alive without heavy deps ----
        return {
            "mode": "stub",
            "model": "U-Net / NDWI water segmentation",
            "water_fraction": 0.59,
            "note": "Install rasterio+numpy for real inference; stub used for demo.",
        }

    def _read(href: str, shape: tuple[int, int] | None = None):
        with rasterio.open(href) as ds:
            if shape is None:
                # downsample for a fast on-stage demo
                scale = max(1, ds.width // 512)
                out_shape = (1, ds.height // scale, ds.width // scale)
            else:
                out_shape = (1, shape[0], shape[1])
            arr = ds.read(out_shape=out_shape, resampling=Resampling.bilinear)[0]
            return arr.astype("float32"), (arr.shape[0], arr.shape[1])

    green, shp = _read(green_href)
    nir, _ = _read(nir_href, shape=shp)
    # NDWI = (Green - NIR) / (Green + NIR); > 0 => water (McFeeters, 1996)
    eps = 1e-6
    ndwi = (green - nir) / (green + nir + eps)
    water = ndwi > 0.0
    frac = float(water.mean())
    return {
        "mode": "real",
        "model": "NDWI water segmentation (proxy for U-Net ToolBox model)",
        "resolution": f"{shp[1]}x{shp[0]} (downsampled for demo)",
        "water_fraction": round(frac, 4),
        "note": "Same interface a U-Net/DeepLab model would expose over MCP.",
    }


@mcp.tool()
def spectral_index(index: str, band1_href: str, band2_href: str) -> dict[str, Any]:
    """Compute a normalized spectral index over a scene (a transformation tool).

    Args:
        index: "ndvi" (band1=NIR, band2=Red) reveals vegetation, or
               "ndwi" (band1=Green, band2=NIR) reveals open water.
        band1_href, band2_href: cloud-optimized GeoTIFF asset URLs
               (from `search_open_data`).

    Returns the mean index and the positive-class fraction (vegetation or water).
    Same "acquire -> transform -> present" motif as true/false-colour composites.
    """
    idx = index.lower()
    try:
        import rasterio
        from rasterio.enums import Resampling
    except ImportError:
        return {"mode": "stub", "index": idx, "mean": 0.2,
                "positive_fraction": 0.35,
                "note": "install rasterio+numpy for real computation"}

    def _read(href):
        with rasterio.open(href) as ds:
            scale = max(1, ds.width // 512)
            arr = ds.read(1, out_shape=(1, ds.height // scale, ds.width // scale),
                          resampling=Resampling.bilinear)[0]
            return arr.astype("float32")

    a, b = _read(band1_href), _read(band2_href)
    n, m = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
    a, b = a[:n, :m], b[:n, :m]
    val = (a - b) / (a + b + 1e-6)
    return {
        "mode": "real",
        "index": idx,
        "mean": round(float(val.mean()), 4),
        "positive_fraction": round(float((val > 0).mean()), 4),
        "positive_class": "vegetation" if idx == "ndvi" else "water",
        "note": "Normalized difference index; > 0 marks the positive class.",
    }


@mcp.tool()
def toolbox_catalog() -> dict[str, Any]:
    """List the remote-sensing models available in the ToolBox (Server B)."""
    return {
        "models": [
            {"name": "object_detection", "task": "ships / vehicles / buildings"},
            {"name": "semantic_segmentation", "task": "water / land-use / buildings"},
            {"name": "change_detection", "task": "bi-temporal change"},
            {"name": "scene_classification", "task": "farmland / urban / forest / water"},
            {"name": "super_resolution", "task": "spatial detail enhancement"},
        ],
        "exposed_now": ["semantic_segmentation (segment_water)"],
        "hosting": "Hugging Face / AWS Marketplace (future)",
    }


@mcp.tool()
def create_stac_item(
    item_id: str,
    bbox: list[float],
    datetime_iso: str,
    hh_href: str,
    hv_href: str = "",
    platform: str = "HaiShao-1",
    frequency_band: str = "C",
) -> dict[str, Any]:
    """Auto-convert a raw SAR scene into a STAC Item (with SAR extension).

    This is Server A's core capability: standardize national SAR ("HaiShao") into
    a STAC Item that international platforms (Registry of Open Data on AWS / HF) accept.

    Args:
        item_id: e.g. "HAISHAO1_SAR_20250118_HAINAN_0001".
        bbox: [min_lon, min_lat, max_lon, max_lat].
        datetime_iso: acquisition time, ISO-8601.
        hh_href / hv_href: cloud-optimized GeoTIFF locations (S3).
    Returns a ready-to-publish STAC Item dict.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    assets = {"hh": hh_href}
    if hv_href:
        assets["hv"] = hv_href
    pols = ["HH", "HV"] if hv_href else ["HH"]
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "stac_extensions": [
            "https://stac-extensions.github.io/sar/v1.0.0/schema.json",
            "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        ],
        "id": item_id,
        "bbox": bbox,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [min_lon, min_lat], [max_lon, min_lat],
                [max_lon, max_lat], [min_lon, max_lat], [min_lon, min_lat],
            ]],
        },
        "properties": {
            "datetime": datetime_iso,
            "platform": platform,
            "instruments": ["SAR"],
            "gsd": 10.0,
            "proj:epsg": 4326,
            "sar:instrument_mode": "IW",
            "sar:frequency_band": frequency_band,
            "sar:polarizations": pols,
            "sar:product_type": "GRD",
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


def main() -> None:
    """Console entry point: run the MCP server over stdio transport."""
    mcp.run()


if __name__ == "__main__":
    # stdio transport: works with Claude Desktop and most MCP clients.
    main()
