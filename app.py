from __future__ import annotations

import json
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
"""


INTRO_MD = """
<div class="mcp-hero">

# MCP4RS Open Earth Explorer

This Space is a human-friendly explorer for the **MCP4RS remote-sensing MCP server**.
General users can try the tools visually. Developers can connect MCP clients to the
same tool surface.

<div class="mcp-badges">
<span>MCP</span><span>Open Earth</span><span>Remote Sensing</span><span>STAC</span><span>NASA GIBS</span><span>Sentinel</span>
</div>

</div>

### What this MCP is about

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


CHAT_LANDING_MD = """
## MCP client demo

This first tab shows what a normal AI client, such as ChatGPT, Claude, Hugging Face
Chat, an IDE assistant, or a scientific agent, does with the MCP server.

Instead of asking the user to know STAC collections, WMS parameters, band names, or
SAR metadata schemas, the client reads the MCP tool catalog, chooses the right tools,
passes structured inputs, and turns the tool results back into a plain-language answer.

**How to use this tab**

1. Choose one sample user request.
2. Click **Run fixed sample answer** to see a stable answer that will not call an
   external LLM or live geospatial service.
3. Click **Show how the 9 MCP tools connect** to see exactly how the landing demo
   maps user requests to the nine MCP functions exposed by this Space.
"""


TOOL_CONNECTION_MD = """
## How the landing demo uses the 9 MCP tools

| Stage | MCP tool | Main output | Usually feeds into |
| --- | --- | --- | --- |
| Discover data options | `list_sources` | Source keys, providers, resolutions | `search_catalog`, `search_open_data`, `get_nightlights` |
| Search Sentinel-2 directly | `search_open_data` | Scene IDs and red/green/blue/NIR asset URLs | `describe_item`, `segment_water`, `spectral_index` |
| Search a chosen catalog | `search_catalog` | STAC items or source-specific access hints | `describe_item`, `get_nightlights`, SAR workflows |
| Inspect one optical scene | `describe_item` | Compact STAC-style metadata | User answer, report, or next analysis step |
| Fetch nighttime lights | `get_nightlights` | NASA GIBS WMS image URL | City lights, outage, fishing, urban-growth view |
| Estimate water | `segment_water` | Water fraction | Environmental or disaster response answer |
| Compute an index | `spectral_index` | NDVI or NDWI summary | Vegetation or water condition answer |
| Discover analysis models | `toolbox_catalog` | Planned model families | Tool choice explanation and roadmap |
| Standardize SAR metadata | `create_stac_item` | STAC Item JSON with SAR metadata | Publishable SAR catalog record |

### Common chains

| User request | MCP chain |
| --- | --- |
| Find water over Hainan | `list_sources` -> `search_open_data` -> `describe_item` -> `segment_water` |
| Show city nightlights | `list_sources` -> `search_catalog` -> `get_nightlights` |
| Use cloud-safe imagery after a storm | `list_sources` -> `search_catalog` -> `create_stac_item` |
| Compute vegetation condition | `list_sources` -> `search_open_data` -> `spectral_index` -> `toolbox_catalog` |
| Publish a SAR scene | `create_stac_item` |
| Explain how an MCP client uses this Space | all 9 tools are available through the Gradio MCP endpoint |
"""


CHAT_DEMOS: dict[str, dict[str, Any]] = {
    "Water over Hainan": {
        "user_type": "Environmental analyst",
        "prompt": "Find Sentinel-2 imagery over Hainan from last month with under 10% cloud cover, and compute the water fraction.",
        "route": ["list_sources", "search_open_data", "describe_item", "segment_water"],
        "answer": "I would search Sentinel-2 over the Hainan bounding box, select a low-cloud scene, inspect its metadata, then pass the returned red, green, blue, and NIR asset URLs to the water tool. In the lightweight Space, the water step may return the stable demo-mode water fraction when rasterio is not installed.",
    },
    "Nightlights city view": {
        "user_type": "City planner",
        "prompt": "Show a nighttime-lights view for the Pearl River Delta and explain which open source provides it.",
        "route": ["list_sources", "search_catalog", "get_nightlights"],
        "answer": "I would identify the nightlights source, confirm that it is a NASA GIBS WMS source rather than a STAC catalog, then build a ready-to-render nighttime-lights image URL for the requested bounding box and date.",
    },
    "Cloud-safe SAR": {
        "user_type": "Disaster responder",
        "prompt": "I need cloud-safe imagery near Hainan after a storm. Which source should I use, and how would it become a standard catalog item?",
        "route": ["list_sources", "search_catalog", "create_stac_item"],
        "answer": "I would choose Sentinel-1 SAR because radar can observe through clouds and at night. After finding or receiving SAR asset URLs, the metadata can be converted into a STAC Item so downstream clients can index and reuse it.",
    },
    "Vegetation index": {
        "user_type": "Agriculture researcher",
        "prompt": "Find recent Sentinel-2 imagery for an agricultural area and compute a vegetation index summary.",
        "route": ["list_sources", "search_open_data", "spectral_index", "toolbox_catalog"],
        "answer": "I would search Sentinel-2 because it provides optical red and NIR bands, then call the spectral-index tool as NDVI. The toolbox catalog explains how this lightweight index relates to the broader analysis-model roadmap.",
    },
    "SAR to STAC": {
        "user_type": "Data publisher",
        "prompt": "Convert a SAR scene with HH and HV files into a STAC Item that other platforms can understand.",
        "route": ["create_stac_item"],
        "answer": "I would package the scene ID, acquisition time, bounding box, platform, frequency band, and HH/HV asset URLs into a STAC Item with SAR and Projection extension metadata.",
    },
    "Client setup": {
        "user_type": "MCP developer",
        "prompt": "How would a conventional MCP client discover and use this Space?",
        "route": [
            "list_sources",
            "search_open_data",
            "search_catalog",
            "describe_item",
            "get_nightlights",
            "segment_water",
            "spectral_index",
            "toolbox_catalog",
            "create_stac_item",
        ],
        "answer": "The client connects to the Gradio MCP endpoint, reads the tool catalog and JSON schemas, selects the relevant tools for the user request, sends structured arguments, and combines the returned JSON into a final response.",
    },
}


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


def _tool_trace_step(tool_name: str, position: int) -> dict[str, Any]:
    tool_notes = {
        "list_sources": {
            "input": "none",
            "output": "source registry with provider, collection, resolution, and access notes",
        },
        "search_open_data": {
            "input": "bbox, datetime_range, max_items, max_cloud_cover",
            "output": "Sentinel-2 scene IDs plus red, green, blue, NIR, SWIR asset URLs",
        },
        "search_catalog": {
            "input": "source key, bbox, datetime_range, max_items, optional cloud filter",
            "output": "STAC items or an access hint for non-STAC sources such as nightlights",
        },
        "describe_item": {
            "input": "item_id and bbox",
            "output": "compact STAC-style metadata for one Sentinel-2 scene",
        },
        "get_nightlights": {
            "input": "bbox, date, layer, width, height",
            "output": "NASA GIBS WMS image URL",
        },
        "segment_water": {
            "input": "red, green, blue, and NIR asset URLs",
            "output": "water fraction and model mode",
        },
        "spectral_index": {
            "input": "index name plus two band asset URLs",
            "output": "mean normalized index and positive-class fraction",
        },
        "toolbox_catalog": {
            "input": "none",
            "output": "remote-sensing model families and currently exposed analysis tools",
        },
        "create_stac_item": {
            "input": "SAR item ID, bbox, datetime, HH/HV asset URLs, platform, frequency band",
            "output": "STAC Item JSON with SAR and Projection extension metadata",
        },
    }
    note = tool_notes.get(tool_name, {"input": "structured JSON", "output": "tool result"})
    return {"step": position, "tool": tool_name, **note}


def _format_demo_reply(label: str, request_text: str, demo: dict[str, Any]) -> str:
    route = " -> ".join(f"`{tool}`" for tool in demo["route"])
    steps = "\n".join(
        f"| {idx} | `{tool}` | {_tool_trace_step(tool, idx)['input']} | {_tool_trace_step(tool, idx)['output']} |"
        for idx, tool in enumerate(demo["route"], start=1)
    )
    return f"""## Fixed sample answer: {label}

**User request:** {request_text}

**User type:** {demo["user_type"]}

**Selected MCP route:** {route}

**How the client uses the tools:**

| Step | MCP tool | Input passed by the client | Output returned to the client |
| --- | --- | --- | --- |
{steps}

**Plain-language answer:**

{demo["answer"]}

**Why this does not error:** this landing-page answer is deterministic Markdown.
It does not call an external LLM, live STAC service, or raster library. The detailed
tabs below still run the actual MCP tool wrappers one by one.
"""


def run_chat_demo(label: str, user_prompt: str) -> str:
    """Return a stable Markdown sample answer without registering another public MCP tool."""
    try:
        demo = CHAT_DEMOS.get(label) or CHAT_DEMOS["Water over Hainan"]
        request_text = _clean_text(user_prompt) or demo["prompt"]
        return _format_demo_reply(label, request_text, demo)
    except Exception as exc:
        return f"""## Fixed sample answer

The landing-page demo could not format the selected scenario, but the app is still
running and the nine MCP tools below are unchanged.

**Fallback request:** Find Sentinel-2 imagery over Hainan and compute water fraction.

**Fallback MCP route:** `list_sources` -> `search_open_data` -> `describe_item` -> `segment_water`

**Fallback answer:** The client discovers available sources, searches Sentinel-2,
inspects a returned item, and passes red/green/blue/NIR asset URLs to the water
fraction tool.

**Internal formatting error:** `{type(exc).__name__}: {exc}`
"""


def show_tool_connections() -> str:
    """Explain the nine MCP tools through a plain Markdown output."""
    return TOOL_CONNECTION_MD


def load_chat_prompt(label: str) -> str:
    demo = CHAT_DEMOS.get(label) or CHAT_DEMOS["Water over Hainan"]
    return demo["prompt"]


def _first_item_id(search_result: Any) -> str:
    if not isinstance(search_result, dict):
        return ""

    candidates = (
        search_result.get("items")
        or search_result.get("features")
        or search_result.get("results")
        or []
    )

    if isinstance(candidates, dict):
        candidates = list(candidates.values())

    if not isinstance(candidates, list):
        return ""

    for item in candidates:
        if isinstance(item, dict):
            item_id = item.get("id") or item.get("item_id")
            if item_id:
                return str(item_id)

    return ""


def use_first_sentinel2_item(search_result: Any, bbox: list[float]) -> tuple[str, list[float]]:
    item_id = _first_item_id(search_result)
    if not item_id:
        raise gr.Error("Run Search Sentinel-2 first, then use this button to fill the returned item ID.")
    return item_id, _as_bbox(bbox)


def search_and_select_sentinel2_item(
    bbox: list[float],
    datetime_range: str | None = None,
    max_items: int = 5,
    max_cloud_cover: float = 20.0,
) -> tuple[dict[str, Any], str, list[float]]:
    result = search_open_data(bbox, datetime_range, max_items, max_cloud_cover)
    item_id = _first_item_id(result)
    if not item_id:
        raise gr.Error("The Sentinel-2 search returned no item IDs. Try a wider date range or higher cloud cover.")
    return result, item_id, _as_bbox(bbox)


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


with gr.Blocks(
    title="MCP4RS Open Earth Explorer",
    theme=gr.themes.Soft(primary_hue="blue", secondary_hue="green"),
    css=THEME_CSS,
) as demo:
    gr.Markdown(INTRO_MD)

    with gr.Tab("Chat Demo"):
        gr.Markdown(CHAT_LANDING_MD)
        with gr.Row():
            chat_label = gr.Dropdown(
                choices=list(CHAT_DEMOS),
                value="Water over Hainan",
                label="Choose a user type or request pattern",
            )
        chat_prompt = gr.Textbox(
            value=CHAT_DEMOS["Water over Hainan"]["prompt"],
            label="Ask as a normal MCP client user",
            lines=2,
        )
        chat_label.change(
            load_chat_prompt,
            inputs=chat_label,
            outputs=chat_prompt,
            api_name=False,
            queue=False,
        )

        gr.Markdown(
            """
            Click the buttons below. They only format fixed Markdown examples, so this
            landing demo is safe even when the Space has no LLM key, no raster stack,
            or no live catalog response.
            """
        )
        sample_answer = gr.Markdown(
            value="Click **Run fixed sample answer** to show how an MCP client would answer this request.",
            label="Fixed sample answer",
        )
        tool_connection_out = gr.Markdown(
            value="Click **Show how the 9 MCP tools connect** to display the tool-chain map.",
            label="9-tool connection map",
        )
        with gr.Row():
            gr.Button("Run fixed sample answer", variant="primary").click(
                run_chat_demo,
                inputs=[chat_label, chat_prompt],
                outputs=sample_answer,
                api_name=False,
                queue=False,
            )
            gr.Button("Show how the 9 MCP tools connect", variant="secondary").click(
                show_tool_connections,
                outputs=tool_connection_out,
                api_name=False,
                queue=False,
            )

    with gr.Tab("Start Here"):
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
        gr.Button("Search Sentinel-2", variant="primary").click(
            search_open_data,
            inputs=[s2_bbox, s2_dates, s2_max_items, s2_cloud],
            outputs=s2_out,
            api_name="search_open_data",
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
            then click **Use first returned item ID** here. If you want a fresh scene, click
            **Regenerate search and use first ID**.
            """
        )
        item_id = gr.Textbox(
            value="",
            placeholder="Click a button below to fill this from Search Sentinel-2",
            label="Selected Sentinel-2 item ID",
            info="This should be the `id` field returned by Search Sentinel-2.",
        )
        describe_bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")

        with gr.Row():
            gr.Button("Use first returned item ID").click(
                use_first_sentinel2_item,
                inputs=[s2_out, s2_bbox],
                outputs=[item_id, describe_bbox],
                api_name=False,
                queue=False,
            )
            gr.Button("Regenerate search and use first ID").click(
                search_and_select_sentinel2_item,
                inputs=[s2_bbox, s2_dates, s2_max_items, s2_cloud],
                outputs=[s2_out, item_id, describe_bbox],
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
