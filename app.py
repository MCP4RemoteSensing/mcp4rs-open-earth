from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

import gradio as gr

from server import (
    SOURCES as _SERVER_SOURCES,
    create_stac_item as _create_stac_item,
    describe_item as _describe_item,
    get_nightlights as _get_nightlights,
    list_sources as _list_sources,
    search_catalog as _search_catalog,
    search_open_data as _search_open_data,
    segment_water as _segment_water,
    spectral_index as _spectral_index,
    toolbox_catalog as _toolbox_catalog,
)


SOURCE_OPTIONS = list(_SERVER_SOURCES)
NIGHTLIGHT_LAYER_OPTIONS = _SERVER_SOURCES["nightlights"]["layers"]

THEME_CSS = """
:root {
  --mcp-ocean: #0B6E8F;
  --mcp-forest: #2E7D32;
  --mcp-earth: #D6A85A;
  --mcp-sky: #F3FAFC;
  --mcp-ink: #17324D;
  --mcp-muted: #5C7285;
}

.gradio-container {
  background: linear-gradient(180deg, var(--mcp-sky), #ffffff 34%);
  color: var(--mcp-ink);
}

.mcp-hero {
  border: 1px solid rgba(11, 110, 143, 0.18);
  border-radius: 8px;
  padding: 18px 20px;
  background: linear-gradient(135deg, rgba(11, 110, 143, 0.10), rgba(46, 125, 50, 0.08));
}

.mcp-badges span {
  display: inline-block;
  margin: 4px 6px 4px 0;
  padding: 4px 9px;
  border-radius: 999px;
  background: rgba(11, 110, 143, 0.10);
  border: 1px solid rgba(11, 110, 143, 0.20);
  color: var(--mcp-ocean);
  font-size: 0.86rem;
  font-weight: 600;
}

.mcp-callout {
  border-left: 4px solid var(--mcp-forest);
  padding: 10px 14px;
  background: rgba(46, 125, 50, 0.07);
  border-radius: 6px;
}

.mcp-small {
  color: var(--mcp-muted);
  font-size: 0.92rem;
}

.mcp-scenario-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
}

.mcp-step {
  border: 1px solid rgba(11, 110, 143, 0.16);
  border-radius: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.72);
}

.mcp-step b {
  color: var(--mcp-ocean);
}
"""


INTRO_MD = """
<div class="mcp-hero">

# MCP4RS Open Earth Chat

Ask a normal geospatial question. The demo shows how a conventional MCP client
such as ChatGPT, Hugging Face Chat, Claude, an IDE assistant, or a scientific
agent can discover MCP tools, read their schemas, call them, and return an answer.

<div class="mcp-badges">
<span>Chat-first MCP demo</span><span>Open Earth</span><span>Remote Sensing</span><span>STAC</span><span>NASA GIBS</span><span>Sentinel</span>
</div>

</div>
"""


LANDING_DEMO_MD = """
## Why MCP for remote sensing?

Traditional geospatial APIs require complex SDKs, STAC/WMS knowledge, collection
names, band names, cloud filters, and geospatial parameters. By wrapping those
capabilities in MCP, an AI client can discover the available tools and execute
the right sequence on behalf of a user.

This landing demo is intentionally lightweight: it behaves like an MCP-aware chat
client, but it does not require an external LLM API key. The buttons below show
several user types and how their requests map to the 9 MCP tools.
"""


LANDING_TOOL_MAP_MD = """
## How the chat demo uses the 9 MCP tools

| MCP tool | What it does | Used in landing demo |
| --- | --- | --- |
| `list_sources` | Shows available Earth-observation sources and resolutions. | Every scenario starts by checking the source registry. |
| `search_open_data` | Searches Sentinel-2 L2A scenes with bbox, dates, and cloud filter. | Environmental analyst water-fraction scenario. |
| `describe_item` | Inspects one returned Sentinel-2 STAC item. | Environmental analyst scene-inspection step. |
| `search_catalog` | Searches or explains any registered source: Sentinel-1, Landsat, NAIP, nightlights, thermal, weather, SST. | City, disaster, agriculture, and source-comparison scenarios. |
| `get_nightlights` | Generates a NASA GIBS nighttime-lights image URL. | City planner and human-activity scenario. |
| `segment_water` | Computes or demos water fraction from red, green, blue, and NIR assets. | Environmental analyst scenario. |
| `spectral_index` | Computes NDVI or NDWI from two band URLs. | Agriculture and vegetation scenario. |
| `toolbox_catalog` | Lists planned remote-sensing model families. | Disaster response and developer scenarios. |
| `create_stac_item` | Converts SAR scene metadata into STAC Item JSON. | SAR data publisher scenario. |
"""


TOOL_EXPLORER_INTRO_MD = """
## What this MCP is about

MCP4RS exposes open Earth-observation discovery, image-access helpers, lightweight
remote-sensing analysis, and SAR-to-STAC conversion as agent-callable tools.

### What users can input

- A geographic bounding box: `[min_lon, min_lat, max_lon, max_lat]`
- A date or date range, such as `2025-01-01/2025-06-30`
- A source key, such as `sentinel-2`, `landsat`, `naip`, or `nightlights`
- Satellite band asset URLs, such as red, green, blue, NIR, HH, or HV files
- SAR scene metadata, such as item ID, acquisition time, platform, and frequency band

### What users can get

- A list of supported open Earth-observation data sources
- STAC search results with scene IDs, cloud cover, dates, and asset URLs
- NASA GIBS nighttime-lights image URLs
- Demo or real water-fraction and spectral-index summaries
- STAC Item JSON for SAR scenes

<div class="mcp-callout">
Suggested path: start with <b>Sources</b>, then use <b>Search Any Catalog</b> or
<b>Search Sentinel-2</b>, inspect a scene, and run <b>Water Fraction</b> or
<b>Spectral Index</b> with the returned asset URLs.
</div>
"""


WORKFLOW_MD = """
## User workflow

1. **Choose a source** with `list_sources`.
2. **Search imagery** with `search_catalog` or the Sentinel-2 shortcut `search_open_data`.
3. **Inspect a scene** with `describe_item`.
4. **Run analysis** with `segment_water` or `spectral_index`.
5. **Standardize SAR metadata** with `create_stac_item`.

## How tools connect

```text
list_sources -> search_catalog -> describe_item -> segment_water
                                      |
                                      -> spectral_index

bbox + date -> get_nightlights -> NASA GIBS image URL

SAR metadata + asset URLs -> create_stac_item -> STAC Item JSON
```
"""


SOURCE_GUIDE_MD = """
## Source keys and examples

| Source key | What it is for | Example area | Output |
| --- | --- | --- | --- |
| `sentinel-2` | 10 m optical imagery for land, coast, water, vegetation | Hainan coast bbox `[109.0,18.0,111.0,20.0]` | STAC items with red, green, blue, NIR assets |
| `sentinel-1` | SAR imagery that can observe through clouds and at night | Hainan coast bbox `[109.0,18.0,111.0,20.0]` | STAC items with VV/VH assets |
| `landsat` | 30 m long-term optical archive | Hainan or global land bbox | STAC items with Landsat assets |
| `naip` | Very high resolution US aerial imagery | San Francisco bbox `[-122.55,37.68,-122.35,37.83]` | STAC items with aerial image assets |
| `nightlights` | Nighttime lights and human activity | Pearl River Delta bbox `[113.8,22.1,114.5,22.8]` | Access hint; use `get_nightlights` for image URL |
| `thermal-lst` | MODIS land surface temperature | Urban heat examples | STAC results or access hints |
| `weather-goes` | GOES weather imagery over the Americas | Americas weather examples | STAC results or access hints |
| `sst` | NOAA sea-surface temperature | Ocean temperature examples | STAC results or access hints |
"""


GLOSSARY_MD = """
## Glossary

| Term | Meaning |
| --- | --- |
| MCP | Model Context Protocol, a standard way for AI clients to call external tools and data. |
| MCP server | A program that exposes tools an AI client can call. |
| MCP client | An app or agent that connects to an MCP server. |
| Explorer | This human-facing Gradio interface for trying the MCP tools. |
| Remote sensing | Observing Earth from satellites, aircraft, or sensors without direct contact. |
| Earth observation | Satellite or aerial data about land, water, atmosphere, cities, and oceans. |
| STAC | SpatioTemporal Asset Catalog, a standard for describing geospatial assets. |
| STAC Item | Metadata for one scene, image, or remote-sensing asset. |
| bbox | Bounding box as `[min_lon, min_lat, max_lon, max_lat]`. |
| COG | Cloud Optimized GeoTIFF, a cloud-friendly raster file format. |
| GSD | Ground sample distance, roughly the real-world size of one image pixel. |
| NIR | Near-infrared band, useful for vegetation and water analysis. |
| SAR | Synthetic Aperture Radar, useful through clouds and at night. |
| NDWI | Normalized Difference Water Index, often used to identify open water. |
| NDVI | Normalized Difference Vegetation Index, often used to identify vegetation. |
| WMS | Web Map Service, a standard way to request map images by URL. |
| Asset URL | A link to an image band or data file returned by a catalog search. |
| Demo mode | A stable fallback output used when heavy raster libraries are not installed. |
"""


DEVELOPER_MD = """
## Developer integration

This Space is both a web explorer and a hosted MCP endpoint.

```text
Human UI:
https://zlysunshine-mcp4rs-open-earth.hf.space

MCP endpoint:
https://zlysunshine-mcp4rs-open-earth.hf.space/gradio_api/mcp/

MCP schema:
https://zlysunshine-mcp4rs-open-earth.hf.space/gradio_api/mcp/schema
```

For clients that support remote MCP endpoints directly, use the MCP endpoint URL.
For clients that need a local command bridge, use `mcp-remote`:

```json
{
  "mcpServers": {
    "mcp4rs-open-earth": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://zlysunshine-mcp4rs-open-earth.hf.space/gradio_api/mcp/"
      ]
    }
  }
}
```

For local stdio MCP clients, run the canonical server file:

```json
{
  "mcpServers": {
    "mcp4rs-open-earth-local": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/server.py"]
    }
  }
}
```

Software architecture:

```text
MCP client -> Hugging Face Gradio MCP endpoint -> app.py wrappers
           -> server.py MCP core -> open data APIs and analysis tools
```
"""


ACKNOWLEDGEMENTS_MD = """
## Open data and code acknowledgements

| Source or project | Used for | Verification |
| --- | --- | --- |
| Model Context Protocol | Tool interface for AI clients | https://modelcontextprotocol.io/docs/getting-started/intro |
| MCP Python SDK / FastMCP | Local MCP server implementation | https://github.com/modelcontextprotocol/python-sdk |
| Gradio MCP support | Hosted MCP endpoint for this Space | https://gradio.app/guides/building-mcp-server-with-gradio |
| Hugging Face Spaces MCP | Space-hosted MCP server behavior | https://huggingface.co/docs/hub/en/spaces-mcp-servers |
| OGC STAC | Geospatial metadata model | https://www.ogc.org/standards/stac/ |
| STAC specification | STAC Item and extension conventions | https://stacspec.org/ |
| Element84 Earth Search | STAC API for open Earth-observation search | https://element84.com/earth-search/ |
| Sentinel-2 L2A COGs on AWS | Sentinel-2 optical imagery source | https://registry.opendata.aws/sentinel-2-l2a-cogs/ |
| Sentinel-1 on AWS | Sentinel-1 SAR imagery source | https://registry.opendata.aws/sentinel-1/ |
| Microsoft Planetary Computer | Landsat, NAIP, MODIS, GOES, OISST catalogs | https://planetarycomputer.microsoft.com/catalog |
| NASA GIBS | Open WMS imagery service for nightlights | https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api |
| NASA Black Marble | VIIRS nighttime-lights data context | https://www.earthdata.nasa.gov/data/projects/black-marble |
| PySTAC Client | Python client for STAC API search | https://pystac-client.readthedocs.io/ |
| NDWI | Water index background, McFeeters 1996 | https://doi.org/10.1080/01431169608948714 |
"""


LANDING_SCENARIOS: dict[str, dict[str, str]] = {
    "Environmental analyst": {
        "button": "Water over Hainan",
        "prompt": "Find Sentinel-2 imagery over Hainan from last month with under 10% cloud cover, and compute the water fraction.",
        "route": "`list_sources` -> `search_open_data` -> `describe_item` -> `segment_water`",
    },
    "City planner": {
        "button": "Nightlights city view",
        "prompt": "Show nighttime lights over the Pearl River Delta and explain what human-activity signal the MCP returns.",
        "route": "`list_sources` -> `search_catalog` -> `get_nightlights`",
    },
    "Disaster responder": {
        "button": "Cloud-safe SAR",
        "prompt": "I need imagery that can still work through clouds for a coastal disaster-response workflow.",
        "route": "`list_sources` -> `search_catalog(source='sentinel-1')` -> `toolbox_catalog`",
    },
    "Agriculture researcher": {
        "button": "Vegetation index",
        "prompt": "Search for open imagery that can support vegetation monitoring and compute a simple NDVI-style index.",
        "route": "`list_sources` -> `search_catalog(source='landsat')` -> `spectral_index`",
    },
    "SAR data publisher": {
        "button": "SAR to STAC",
        "prompt": "Convert a HaiShao SAR scene with HH and HV assets into a publishable STAC Item.",
        "route": "`create_stac_item`",
    },
    "MCP developer": {
        "button": "Client setup",
        "prompt": "Explain how ChatGPT, Hugging Face Chat, Claude, or another MCP client would discover and call these 9 tools.",
        "route": "`/tools` discovery -> JSON schemas -> selected MCP tool calls",
    },
}

SCENARIO_OPTIONS = list(LANDING_SCENARIOS)


def _clean_text(value: str | None) -> str:
    return (value or "").strip()


def _optional_text(value: str | None) -> str | None:
    cleaned = _clean_text(value)
    return cleaned or None


def _as_bbox(value: Any) -> list[float]:
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list) or len(value) != 4:
        raise gr.Error("Bounding box must be a list: [min_lon, min_lat, max_lon, max_lat].")
    try:
        return [float(part) for part in value]
    except (TypeError, ValueError) as exc:
        raise gr.Error("Bounding box values must be numbers.") from exc


def _as_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _as_float(value: Any, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _from_json_component(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _candidate_items(search_result: Any) -> list[Any]:
    search_result = _from_json_component(search_result)
    if not isinstance(search_result, dict):
        return []

    candidates = (
        search_result.get("items")
        or search_result.get("features")
        or search_result.get("results")
        or search_result.get("scenes")
        or search_result.get("matches")
        or []
    )

    if isinstance(candidates, dict):
        candidates = list(candidates.values())

    if not isinstance(candidates, list):
        return []

    return candidates


def _first_item(search_result: Any) -> dict[str, Any]:
    for item in _candidate_items(search_result):
        if isinstance(item, dict):
            return item
    return {}


def _first_item_id(search_result: Any) -> str:
    for item in _candidate_items(search_result):
        if isinstance(item, dict):
            item_id = item.get("id") or item.get("item_id")
            if item_id:
                return str(item_id)
    return ""


def _previous_month_range() -> str:
    first_this_month = date.today().replace(day=1)
    last_previous_month = first_this_month - timedelta(days=1)
    first_previous_month = last_previous_month.replace(day=1)
    return f"{first_previous_month.isoformat()}/{last_previous_month.isoformat()}"


def _safe_tool_call(name: str, fn: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        result = fn(*args, **kwargs)
        if isinstance(result, dict):
            return result
        return {"result": result}
    except Exception as exc:
        return {
            "mode": "fallback",
            "tool": name,
            "error": str(exc),
            "note": "The landing demo kept running and used a readable fallback summary.",
        }


def _trace_step(name: str, purpose: str, result: dict[str, Any]) -> dict[str, Any]:
    compact = {
        "count": result.get("count"),
        "id": result.get("id"),
        "source": result.get("source"),
        "mode": result.get("mode"),
        "water_fraction": result.get("water_fraction"),
        "index": result.get("index"),
        "positive_fraction": result.get("positive_fraction"),
        "image_url": result.get("image_url"),
        "error": result.get("error"),
        "note": result.get("note"),
    }
    return {
        "tool": name,
        "purpose": purpose,
        "output_summary": {k: v for k, v in compact.items() if v is not None},
    }


def _selected_item_status(item_id: str) -> str:
    return f"Selected item ID: `{item_id}`"


def store_sentinel2_search(search_result: Any) -> Any:
    return _from_json_component(search_result)


def use_first_sentinel2_item(search_result: Any, bbox: list[float]) -> tuple[str, list[float], str]:
    item_id = _first_item_id(search_result)
    if not item_id:
        raise gr.Error("No item ID is saved yet. Click 'Search now and fill first item ID' or run Search Sentinel-2 first.")
    return item_id, _as_bbox(bbox), _selected_item_status(item_id)


def search_and_select_sentinel2_item(
    bbox: list[float],
    datetime_range: str | None = None,
    max_items: int = 5,
    max_cloud_cover: float = 20.0,
) -> tuple[dict[str, Any], dict[str, Any], str, list[float], str]:
    result = search_open_data(bbox, datetime_range, max_items, max_cloud_cover)
    item_id = _first_item_id(result)
    if not item_id:
        raise gr.Error("The Sentinel-2 search returned no item IDs. Try a wider date range or higher cloud cover.")
    return result, result, item_id, _as_bbox(bbox), _selected_item_status(item_id)


def list_sources() -> dict[str, Any]:
    """List the open satellite data sources this MCP server can query."""
    return _list_sources()


def search_open_data(
    bbox: list[float],
    datetime_range: str | None = None,
    max_items: int = 5,
    max_cloud_cover: float = 20.0,
) -> dict[str, Any]:
    """Search Sentinel-2 L2A scenes on AWS Earth Search."""
    return _search_open_data(
        bbox=_as_bbox(bbox),
        datetime_range=_optional_text(datetime_range),
        max_items=_as_int(max_items, 5),
        max_cloud_cover=_as_float(max_cloud_cover, 20.0),
    )


def describe_item(item_id: str, bbox: list[float]) -> dict[str, Any]:
    """Describe one Sentinel-2 scene as compact STAC-style metadata."""
    item_id = _clean_text(item_id)
    if not item_id:
        return {
            "error": "Choose an item ID first.",
            "workflow": "Run Search Sentinel-2, then click Use first returned item ID.",
        }
    return _describe_item(item_id=item_id, bbox=_as_bbox(bbox))


def search_catalog(
    source: str,
    bbox: list[float],
    datetime_range: str | None = None,
    max_items: int = 5,
    max_cloud_cover: float = 30.0,
) -> dict[str, Any]:
    """Search a registered open Earth-observation catalog by source key."""
    return _search_catalog(
        source=_clean_text(source),
        bbox=_as_bbox(bbox),
        datetime_range=_optional_text(datetime_range),
        max_items=_as_int(max_items, 5),
        max_cloud_cover=_as_float(max_cloud_cover, 30.0),
    )


def get_nightlights(
    bbox: list[float],
    date: str = "2023-01-01",
    layer: str = "VIIRS_SNPP_DayNightBand_ENCC",
    width: int = 512,
    height: int = 512,
) -> dict[str, Any]:
    """Fetch an open nighttime-lights image URL from NASA GIBS."""
    return _get_nightlights(
        bbox=_as_bbox(bbox),
        date=_clean_text(date) or "2023-01-01",
        layer=_clean_text(layer) or "VIIRS_SNPP_DayNightBand_ENCC",
        width=_as_int(width, 512),
        height=_as_int(height, 512),
    )


def segment_water(
    red_href: str,
    green_href: str,
    blue_href: str,
    nir_href: str,
) -> dict[str, Any]:
    """Estimate water fraction from Sentinel-2 red, green, blue, and NIR URLs."""
    hrefs = [_clean_text(red_href), _clean_text(green_href), _clean_text(blue_href), _clean_text(nir_href)]
    if not all(hrefs):
        return {
            "error": "Provide red, green, blue, and NIR asset URLs.",
            "workflow": "Run Search Sentinel-2 first, then paste the returned band URLs here.",
            "demo_tip": "The prefilled demo:// URLs are enough to show stub mode in the lightweight Space.",
        }
    return _segment_water(*hrefs)


def spectral_index(index: str, band1_href: str, band2_href: str) -> dict[str, Any]:
    """Compute a normalized spectral index over two satellite band URLs."""
    href1 = _clean_text(band1_href)
    href2 = _clean_text(band2_href)
    if not href1 or not href2:
        return {
            "error": "Provide both band URLs.",
            "examples": {
                "ndvi": "band1=NIR, band2=Red",
                "ndwi": "band1=Green, band2=NIR",
            },
        }
    return _spectral_index(index=_clean_text(index).lower(), band1_href=href1, band2_href=href2)


def toolbox_catalog() -> dict[str, Any]:
    """List planned remote-sensing ToolBox model families."""
    return _toolbox_catalog()


def create_stac_item(
    item_id: str,
    bbox: list[float],
    datetime_iso: str,
    hh_href: str,
    hv_href: str = "",
    platform: str = "HaiShao-1",
    frequency_band: str = "C",
) -> dict[str, Any]:
    """Create a STAC Item for a SAR scene."""
    if not _clean_text(item_id):
        return {"error": "Provide a SAR item ID."}
    if not _clean_text(hh_href):
        return {"error": "Provide at least an HH polarization asset URL."}
    return _create_stac_item(
        item_id=_clean_text(item_id),
        bbox=_as_bbox(bbox),
        datetime_iso=_clean_text(datetime_iso) or "2025-01-18T03:21:00Z",
        hh_href=_clean_text(hh_href),
        hv_href=_clean_text(hv_href),
        platform=_clean_text(platform) or "HaiShao-1",
        frequency_band=_clean_text(frequency_band) or "C",
    )


def _select_landing_scenario(message: str, selected_label: str) -> str:
    text = _clean_text(message).lower()
    if any(word in text for word in ("night", "lights", "city", "urban", "outage", "human activity")):
        return "City planner"
    if any(word in text for word in ("cloud", "disaster", "sar", "radar", "storm", "flood")):
        return "Disaster responder"
    if any(word in text for word in ("vegetation", "crop", "agriculture", "ndvi", "farm")):
        return "Agriculture researcher"
    if any(word in text for word in ("stac item", "haishao", "hh", "hv", "publish", "sar scene")):
        return "SAR data publisher"
    if any(word in text for word in ("chatgpt", "claude", "hugging face", "client", "schema", "json-rpc", "endpoint")):
        return "MCP developer"
    if any(word in text for word in ("water", "sentinel-2", "hainan", "cloud cover", "ndwi")):
        return "Environmental analyst"
    return selected_label if selected_label in LANDING_SCENARIOS else "Environmental analyst"


def _scenario_header(label: str, prompt: str) -> list[str]:
    scenario = LANDING_SCENARIOS[label]
    return [
        f"**User type:** {label}",
        f"**User request:** {prompt}",
        f"**MCP route:** {scenario['route']}",
    ]


def _format_trace_table(trace: list[dict[str, Any]]) -> str:
    rows = ["| Step | Tool | What the app does |", "| --- | --- | --- |"]
    for idx, step in enumerate(trace, start=1):
        rows.append(f"| {idx} | `{step['tool']}` | {step['purpose']} |")
    return "\n".join(rows)


def _run_water_landing(prompt: str) -> tuple[str, dict[str, Any]]:
    bbox = [109.0, 18.0, 111.0, 20.0]
    dynamic_dates = _previous_month_range()
    trace: list[dict[str, Any]] = []

    sources = _safe_tool_call("list_sources", list_sources)
    trace.append(_trace_step("list_sources", "Discover that Sentinel-2 is available for 10 m optical imagery.", sources))

    search_result = _safe_tool_call("search_open_data", search_open_data, bbox, dynamic_dates, 5, 10.0)
    item = _first_item(search_result)
    if not item:
        search_result = _safe_tool_call("search_open_data", search_open_data, bbox, "2025-01-01/2025-06-30", 5, 20.0)
        item = _first_item(search_result)
    trace.append(_trace_step("search_open_data", "Search Sentinel-2 scenes by bbox, date range, and cloud-cover filter.", search_result))

    item_id = str(item.get("id") or "demo-sentinel-2-item")
    if item.get("id"):
        item_details = _safe_tool_call("describe_item", describe_item, item_id, bbox)
    else:
        item_details = {
            "id": item_id,
            "mode": "fallback",
            "note": "No live STAC item was returned, so the landing demo used a demo item label.",
        }
    trace.append(_trace_step("describe_item", "Inspect the selected scene metadata before analysis.", item_details))

    assets = item.get("assets", {}) if isinstance(item, dict) else {}
    water_result = _safe_tool_call(
        "segment_water",
        segment_water,
        assets.get("red", "demo://sentinel-2/red.tif"),
        assets.get("green", "demo://sentinel-2/green.tif"),
        assets.get("blue", "demo://sentinel-2/blue.tif"),
        assets.get("nir", "demo://sentinel-2/nir.tif"),
    )
    trace.append(_trace_step("segment_water", "Use red, green, blue, and NIR asset URLs to estimate water fraction.", water_result))

    water_fraction = water_result.get("water_fraction", "available in the JSON result")
    response = "\n\n".join(
        _scenario_header("Environmental analyst", prompt)
        + [
            _format_trace_table(trace),
            (
                "**Final answer:** I selected a Sentinel-2 workflow for Hainan, "
                f"used `{item_id}` as the scene ID, and computed a water-fraction "
                f"summary of **{water_fraction}**. In this lightweight Space, the "
                "analysis may run in demo mode if raster libraries are not installed."
            ),
        ]
    )
    return response, {"scenario": "Environmental analyst", "trace": trace, "result": water_result}


def _run_city_landing(prompt: str) -> tuple[str, dict[str, Any]]:
    bbox = [113.8, 22.1, 114.5, 22.8]
    trace: list[dict[str, Any]] = []
    sources = _safe_tool_call("list_sources", list_sources)
    trace.append(_trace_step("list_sources", "Discover that nightlights are available as a NASA GIBS WMS source.", sources))
    catalog = _safe_tool_call("search_catalog", search_catalog, "nightlights", bbox, "2023-01-01/2023-01-01", 1, 30.0)
    trace.append(_trace_step("search_catalog", "Recognize that nightlights use WMS imagery rather than STAC scene items.", catalog))
    nightlights = _safe_tool_call("get_nightlights", get_nightlights, bbox, "2023-01-01", "VIIRS_SNPP_DayNightBand_ENCC", 512, 512)
    trace.append(_trace_step("get_nightlights", "Generate a ready-to-render nighttime-lights image URL.", nightlights))

    image_url = nightlights.get("image_url", "available in the JSON result")
    response = "\n\n".join(
        _scenario_header("City planner", prompt)
        + [
            _format_trace_table(trace),
            (
                "**Final answer:** I used the nightlights source for a human-activity view "
                "over the Pearl River Delta. The MCP returns a NASA GIBS image URL that a "
                f"client can render directly: `{image_url}`."
            ),
        ]
    )
    return response, {"scenario": "City planner", "trace": trace, "result": nightlights}


def _run_disaster_landing(prompt: str) -> tuple[str, dict[str, Any]]:
    bbox = [109.0, 18.0, 111.0, 20.0]
    trace: list[dict[str, Any]] = []
    sources = _safe_tool_call("list_sources", list_sources)
    trace.append(_trace_step("list_sources", "Find all-weather radar sources for cloudy coastal conditions.", sources))
    sar_search = _safe_tool_call("search_catalog", search_catalog, "sentinel-1", bbox, "2025-01-01/2025-06-30", 3, 30.0)
    trace.append(_trace_step("search_catalog", "Search Sentinel-1 SAR scenes that can complement optical imagery.", sar_search))
    toolbox = _safe_tool_call("toolbox_catalog", toolbox_catalog)
    trace.append(_trace_step("toolbox_catalog", "Check which downstream model families can support response workflows.", toolbox))

    response = "\n\n".join(
        _scenario_header("Disaster responder", prompt)
        + [
            _format_trace_table(trace),
            (
                "**Final answer:** For clouds, smoke, or nighttime response, the app chooses "
                "`sentinel-1` SAR through `search_catalog`, then checks the ToolBox catalog "
                "for segmentation, detection, and change-detection model families."
            ),
        ]
    )
    return response, {"scenario": "Disaster responder", "trace": trace, "result": sar_search}


def _run_agriculture_landing(prompt: str) -> tuple[str, dict[str, Any]]:
    bbox = [109.0, 18.0, 111.0, 20.0]
    trace: list[dict[str, Any]] = []
    sources = _safe_tool_call("list_sources", list_sources)
    trace.append(_trace_step("list_sources", "Discover optical sources suitable for vegetation monitoring.", sources))
    catalog = _safe_tool_call("search_catalog", search_catalog, "landsat", bbox, "2025-01-01/2025-06-30", 3, 30.0)
    trace.append(_trace_step("search_catalog", "Search Landsat as a long-archive vegetation-monitoring source.", catalog))
    ndvi = _safe_tool_call("spectral_index", spectral_index, "ndvi", "demo://landsat/nir.tif", "demo://landsat/red.tif")
    trace.append(_trace_step("spectral_index", "Compute an NDVI-style normalized difference index.", ndvi))

    response = "\n\n".join(
        _scenario_header("Agriculture researcher", prompt)
        + [
            _format_trace_table(trace),
            (
                "**Final answer:** I selected an optical catalog route and used `spectral_index` "
                "for an NDVI-style vegetation summary. The same pattern can switch to NDWI for "
                "water or to Sentinel-2 for higher-resolution optical monitoring."
            ),
        ]
    )
    return response, {"scenario": "Agriculture researcher", "trace": trace, "result": ndvi}


def _run_publisher_landing(prompt: str) -> tuple[str, dict[str, Any]]:
    bbox = [109.0, 18.0, 111.0, 20.0]
    trace: list[dict[str, Any]] = []
    stac = _safe_tool_call(
        "create_stac_item",
        create_stac_item,
        "HAISHAO1_SAR_20250118_HAINAN_0001",
        bbox,
        "2025-01-18T03:21:00Z",
        "s3://example/HH.tif",
        "s3://example/HV.tif",
        "HaiShao-1",
        "C",
    )
    trace.append(_trace_step("create_stac_item", "Turn raw SAR metadata and HH/HV asset links into STAC Item JSON.", stac))

    response = "\n\n".join(
        _scenario_header("SAR data publisher", prompt)
        + [
            _format_trace_table(trace),
            (
                "**Final answer:** I converted the SAR scene into a STAC Item with geometry, "
                "bbox, datetime, SAR extension metadata, and HH/HV assets. This is the data "
                "standardization side of the MCP."
            ),
        ]
    )
    return response, {"scenario": "SAR data publisher", "trace": trace, "result": stac}


def _run_developer_landing(prompt: str) -> tuple[str, dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    sources = _safe_tool_call("list_sources", list_sources)
    trace.append(_trace_step("list_sources", "Show how a client first discovers available data sources.", sources))
    toolbox = _safe_tool_call("toolbox_catalog", toolbox_catalog)
    trace.append(_trace_step("toolbox_catalog", "Show how a client discovers available analysis model families.", toolbox))

    response = "\n\n".join(
        _scenario_header("MCP developer", prompt)
        + [
            (
                "| MCP client action | What happens |\n"
                "| --- | --- |\n"
                "| Connect to endpoint | The client opens `/gradio_api/mcp/`. |\n"
                "| Discover tools | It reads the tool catalog and JSON schemas. |\n"
                "| Choose a route | It maps the natural-language request to one or more tools. |\n"
                "| Execute calls | It sends structured arguments such as bbox, date range, source, or asset URLs. |\n"
                "| Compose answer | It turns returned JSON into a readable response. |"
            ),
            (
                "**Final answer:** The landing chat is a stable simulation of that MCP-client "
                "behavior. The detailed tabs still expose exactly the 9 callable tools for "
                "manual testing and schema discovery."
            ),
        ]
    )
    return response, {"scenario": "MCP developer", "trace": trace, "result": {"endpoint": "/gradio_api/mcp/"}}


def run_landing_demo(
    message: str,
    selected_label: str,
    history: list[tuple[str, str]] | None,
) -> tuple[list[tuple[str, str]], dict[str, Any]]:
    default_scenario = LANDING_SCENARIOS.get(selected_label, LANDING_SCENARIOS["Environmental analyst"])
    prompt = _clean_text(message) or default_scenario["prompt"]
    label = _select_landing_scenario(prompt, selected_label)
    runners = {
        "Environmental analyst": _run_water_landing,
        "City planner": _run_city_landing,
        "Disaster responder": _run_disaster_landing,
        "Agriculture researcher": _run_agriculture_landing,
        "SAR data publisher": _run_publisher_landing,
        "MCP developer": _run_developer_landing,
    }
    response, trace = runners[label](prompt)
    updated_history = list(history or [])
    updated_history.append((prompt, response))
    return updated_history, trace


def set_landing_scenario(label: str) -> tuple[str, str]:
    scenario = LANDING_SCENARIOS[label]
    return label, scenario["prompt"]


with gr.Blocks(
    title="MCP4RS Open Earth Explorer",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="green"),
    css=THEME_CSS,
) as demo:
    latest_s2_result = gr.State(value=None)

    gr.Markdown(INTRO_MD)

    with gr.Tab("Chat Demo"):
        gr.Markdown(LANDING_DEMO_MD)
        landing_scenario = gr.Dropdown(
            choices=SCENARIO_OPTIONS,
            value="Environmental analyst",
            label="Choose a user type",
        )
        landing_prompt = gr.Textbox(
            value=LANDING_SCENARIOS["Environmental analyst"]["prompt"],
            label="Ask as a normal MCP client user",
            lines=2,
        )
        with gr.Row():
            gr.Button(LANDING_SCENARIOS["Environmental analyst"]["button"]).click(
                lambda: set_landing_scenario("Environmental analyst"),
                outputs=[landing_scenario, landing_prompt],
                api_name=False,
                queue=False,
            )
            gr.Button(LANDING_SCENARIOS["City planner"]["button"]).click(
                lambda: set_landing_scenario("City planner"),
                outputs=[landing_scenario, landing_prompt],
                api_name=False,
                queue=False,
            )
            gr.Button(LANDING_SCENARIOS["Disaster responder"]["button"]).click(
                lambda: set_landing_scenario("Disaster responder"),
                outputs=[landing_scenario, landing_prompt],
                api_name=False,
                queue=False,
            )
        with gr.Row():
            gr.Button(LANDING_SCENARIOS["Agriculture researcher"]["button"]).click(
                lambda: set_landing_scenario("Agriculture researcher"),
                outputs=[landing_scenario, landing_prompt],
                api_name=False,
                queue=False,
            )
            gr.Button(LANDING_SCENARIOS["SAR data publisher"]["button"]).click(
                lambda: set_landing_scenario("SAR data publisher"),
                outputs=[landing_scenario, landing_prompt],
                api_name=False,
                queue=False,
            )
            gr.Button(LANDING_SCENARIOS["MCP developer"]["button"]).click(
                lambda: set_landing_scenario("MCP developer"),
                outputs=[landing_scenario, landing_prompt],
                api_name=False,
                queue=False,
            )

        landing_chat = gr.Chatbot(label="MCP-aware client response", height=430)
        landing_trace = gr.JSON(label="Structured tool trace")
        landing_run = gr.Button("Run chat demo", variant="primary")
        landing_run.click(
            run_landing_demo,
            inputs=[landing_prompt, landing_scenario, landing_chat],
            outputs=[landing_chat, landing_trace],
            api_name=False,
            queue=False,
        )
        landing_prompt.submit(
            run_landing_demo,
            inputs=[landing_prompt, landing_scenario, landing_chat],
            outputs=[landing_chat, landing_trace],
            api_name=False,
            queue=False,
        )

        with gr.Accordion("How the 9 tools connect in the landing demo", open=False):
            gr.Markdown(LANDING_TOOL_MAP_MD)

    with gr.Tab("Tool Explorer Guide"):
        gr.Markdown(TOOL_EXPLORER_INTRO_MD)
        gr.Markdown(WORKFLOW_MD)
        gr.Markdown(SOURCE_GUIDE_MD)

    with gr.Tab("1. Sources"):
        gr.Markdown(
            """
            ## `list_sources`

            **Use for:** discovering which open Earth-observation sources this MCP can query.

            **Input:** none.

            **Output:** a source registry with title, provider, collection, resolution, and access notes.
            """
        )
        source_out = gr.JSON(label="Available sources")
        gr.Button("List sources", variant="primary").click(
            list_sources,
            outputs=source_out,
            api_name="list_sources",
            queue=False,
        )

    with gr.Tab("2. Search Sentinel-2"):
        gr.Markdown(
            """
            ## `search_open_data`

            **Use for:** the simplest optical-imagery workflow. It searches Sentinel-2 L2A scenes
            on AWS Earth Search and returns scene IDs plus band asset URLs.

            **Try this:** Hainan coast, `2025-01-01/2025-06-30`, max cloud cover `20`.

            **Connects to:** use the returned item ID in `describe_item`, or copy red/green/blue/NIR
            asset URLs into `segment_water` and `spectral_index`.
            """
        )
        s2_bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")
        s2_dates = gr.Textbox(value="2025-01-01/2025-06-30", label="Date range")
        s2_max_items = gr.Number(value=5, precision=0, label="Max items")
        s2_cloud = gr.Number(value=20, label="Max cloud cover (%)")
        s2_out = gr.JSON(label="Sentinel-2 search results")
        s2_search_event = gr.Button("Search Sentinel-2", variant="primary").click(
            search_open_data,
            inputs=[s2_bbox, s2_dates, s2_max_items, s2_cloud],
            outputs=s2_out,
            api_name="search_open_data",
            queue=False,
        )
        s2_search_event.then(
            store_sentinel2_search,
            inputs=s2_out,
            outputs=latest_s2_result,
            api_name=False,
            queue=False,
        )

    with gr.Tab("3. Search Any Catalog"):
        gr.Markdown(
            """
            ## `search_catalog`

            **Use for:** choosing among optical, SAR, aerial, nightlights, thermal, weather,
            and ocean-temperature sources.

            **Input:** source key, bbox, date range, max items, and optional cloud filter.

            **Output:** source metadata and matching STAC items, or access hints for non-STAC sources.
            """
        )
        with gr.Row():
            catalog_source = gr.Dropdown(
                choices=SOURCE_OPTIONS,
                value="sentinel-2",
                label="Source",
            )
            catalog_dates = gr.Textbox(value="2025-01-01/2025-06-30", label="Date range")
        catalog_bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")
        with gr.Row():
            catalog_max_items = gr.Number(value=5, precision=0, label="Max items")
            catalog_cloud = gr.Number(value=30, label="Max cloud cover (%)")
        catalog_out = gr.JSON(label="Catalog search results")
        gr.Button("Search catalog", variant="primary").click(
            search_catalog,
            inputs=[catalog_source, catalog_bbox, catalog_dates, catalog_max_items, catalog_cloud],
            outputs=catalog_out,
            api_name="search_catalog",
            queue=False,
        )

    with gr.Tab("4. Describe STAC Item"):
        gr.Markdown(
            """
            ## `describe_item`

            **Use for:** inspecting one Sentinel-2 scene selected from `search_open_data`.

            You do not need to manually search through the JSON. First run **Search Sentinel-2**,
            then click **Use latest search result** here. If you want a fresh scene, click
            **Search now and fill first item ID**.
            """
        )
        item_id = gr.Textbox(
            value="",
            placeholder="Click 'Use latest search result' or 'Search now and fill first item ID'",
            label="Selected Sentinel-2 item ID",
            info="This should be the `id` field returned by Search Sentinel-2.",
        )
        describe_bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")
        selected_item_status = gr.Markdown("No item ID selected yet.")
        with gr.Row():
            gr.Button("Use latest search result").click(
                use_first_sentinel2_item,
                inputs=[latest_s2_result, s2_bbox],
                outputs=[item_id, describe_bbox, selected_item_status],
                api_name=False,
                queue=False,
            )
            gr.Button("Search now and fill first item ID").click(
                search_and_select_sentinel2_item,
                inputs=[s2_bbox, s2_dates, s2_max_items, s2_cloud],
                outputs=[s2_out, latest_s2_result, item_id, describe_bbox, selected_item_status],
                api_name=False,
                queue=False,
            )

        describe_out = gr.JSON(label="Item metadata")
        gr.Button("Describe selected item", variant="primary").click(
            describe_item,
            inputs=[item_id, describe_bbox],
            outputs=describe_out,
            api_name="describe_item",
            queue=False,
        )

    with gr.Tab("5. Nightlights"):
        gr.Markdown(
            """
            ## `get_nightlights`

            **Use for:** city lights, fishing fleets, gas flares, power outages, urban growth,
            and other nighttime human-activity patterns.

            **Input:** bbox, date, NASA GIBS layer, width, and height.

            **Output:** a ready-to-render NASA GIBS WMS image URL.
            """
        )
        night_bbox = gr.JSON(value=[113.8, 22.1, 114.5, 22.8], label="Bounding box")
        with gr.Row():
            night_date = gr.Textbox(value="2023-01-01", label="Date")
            night_layer = gr.Dropdown(
                choices=NIGHTLIGHT_LAYER_OPTIONS,
                value="VIIRS_SNPP_DayNightBand_ENCC",
                label="Layer",
            )
        with gr.Row():
            night_width = gr.Number(value=512, precision=0, label="Width")
            night_height = gr.Number(value=512, precision=0, label="Height")
        night_out = gr.JSON(label="Nightlights result")
        gr.Button("Get nightlights", variant="primary").click(
            get_nightlights,
            inputs=[night_bbox, night_date, night_layer, night_width, night_height],
            outputs=night_out,
            api_name="get_nightlights",
            queue=False,
        )

    with gr.Tab("6. Water Fraction"):
        gr.Markdown(
            """
            ## `segment_water`

            **Use for:** estimating water fraction from Sentinel-2 band URLs.

            **Input:** red, green, blue, and NIR asset URLs. In the real workflow,
            copy these from `search_open_data` or `search_catalog`.

            **Output:** water fraction and mode metadata. The current lightweight Space
            returns a stable demo output unless rasterio is installed.
            """
        )
        red = gr.Textbox(value="demo://sentinel-2/red.tif", label="Red band URL")
        green = gr.Textbox(value="demo://sentinel-2/green.tif", label="Green band URL")
        blue = gr.Textbox(value="demo://sentinel-2/blue.tif", label="Blue band URL")
        nir = gr.Textbox(value="demo://sentinel-2/nir.tif", label="NIR band URL")
        water_out = gr.JSON(label="Water fraction")
        gr.Button("Measure water fraction", variant="primary").click(
            segment_water,
            inputs=[red, green, blue, nir],
            outputs=water_out,
            api_name="segment_water",
            queue=False,
        )

    with gr.Tab("7. Spectral Index"):
        gr.Markdown(
            """
            ## `spectral_index`

            **Use for:** compact NDVI or NDWI summaries from two satellite band URLs.

            **Input examples:**

            - NDVI: `band1=NIR`, `band2=Red`
            - NDWI: `band1=Green`, `band2=NIR`

            **Output:** mean normalized index and positive-class fraction.
            """
        )
        index = gr.Dropdown(choices=["ndvi", "ndwi"], value="ndwi", label="Index")
        band1 = gr.Textbox(value="demo://sentinel-2/green.tif", label="Band 1 URL")
        band2 = gr.Textbox(value="demo://sentinel-2/nir.tif", label="Band 2 URL")
        index_out = gr.JSON(label="Spectral index result")
        gr.Button("Compute spectral index", variant="primary").click(
            spectral_index,
            inputs=[index, band1, band2],
            outputs=index_out,
            api_name="spectral_index",
            queue=False,
        )

    with gr.Tab("8. Toolbox Catalog"):
        gr.Markdown(
            """
            ## `toolbox_catalog`

            **Use for:** explaining the current and planned remote-sensing model families.

            **Input:** none.

            **Output:** model-family catalog and currently exposed analysis tools.
            """
        )
        toolbox_out = gr.JSON(label="Toolbox catalog")
        gr.Button("List toolbox models", variant="primary").click(
            toolbox_catalog,
            outputs=toolbox_out,
            api_name="toolbox_catalog",
            queue=False,
        )

    with gr.Tab("9. SAR to STAC"):
        gr.Markdown(
            """
            ## `create_stac_item`

            **Use for:** converting a SAR scene description into a STAC Item JSON record.

            **Input:** item ID, bbox, acquisition datetime, HH/HV asset URLs, platform,
            and frequency band.

            **Output:** STAC Item JSON with SAR and Projection extension metadata.
            """
        )
        sar_item_id = gr.Textbox(value="HAISHAO1_SAR_20250118_HAINAN_0001", label="Item ID")
        sar_bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")
        sar_datetime = gr.Textbox(value="2025-01-18T03:21:00Z", label="Datetime")
        hh = gr.Textbox(value="s3://example/HH.tif", label="HH asset URL")
        hv = gr.Textbox(value="s3://example/HV.tif", label="HV asset URL")
        with gr.Row():
            platform = gr.Textbox(value="HaiShao-1", label="Platform")
            frequency_band = gr.Textbox(value="C", label="Frequency band")
        stac_out = gr.JSON(label="STAC Item")
        gr.Button("Create SAR STAC Item", variant="primary").click(
            create_stac_item,
            inputs=[sar_item_id, sar_bbox, sar_datetime, hh, hv, platform, frequency_band],
            outputs=stac_out,
            api_name="create_stac_item",
            queue=False,
        )

    with gr.Tab("Glossary"):
        gr.Markdown(GLOSSARY_MD)

    with gr.Tab("Developers"):
        gr.Markdown(DEVELOPER_MD)

    with gr.Tab("Acknowledgements"):
        gr.Markdown(ACKNOWLEDGEMENTS_MD)


if __name__ == "__main__":
    demo.launch(mcp_server=True, ssr_mode=False, show_error=True)
