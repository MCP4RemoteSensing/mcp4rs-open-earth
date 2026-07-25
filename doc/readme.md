# Major Updates for server.py

This document tracks the major updates introduced in `server.py`.

## Summary

The server evolved from a single-source Sentinel-2 demo into a broader multi-source, multi-tool MCP server for remote-sensing workflows.

## server.py Update Log (Date + Commit)

Use this table to record every material update to server.py.

| Date | Commit | Change summary |
| --- | --- | --- |
| 2026-07-25 | 5da604f | Baseline major update introducing multi-source catalog support and expanded MCP tool surface. |

### How to add new entries

1. After modifying server.py, get the latest commit touching the file:

	`git log -n 1 --date=short --pretty=format:'%h|%ad|%s' -- server.py`

2. Append a new row at the top of the table with:

	- Date (YYYY-MM-DD)
	- Commit short hash
	- One-line summary of what changed in server.py

3. Keep this log focused on behavior or API-surface changes (not tiny formatting edits).

## Major Updates

### 1) Multi-Source Open Data Registry

Added a unified `SOURCES` registry to support multiple catalogs and modalities:

- `sentinel-2` (10 m optical)
- `naip` (~0.6-1 m aerial)
- `landsat` (30 m archive)
- `sentinel-1` (10 m SAR)
- `nightlights` (VIIRS low-light, ~500 m)
- `thermal-lst` (MODIS LST, 1 km)
- `weather-goes` (GOES thermal IR, ~2 km)
- `sst` (NOAA OISST, ~25 km)

This enables one MCP interface to expose several popular open satellite data sources.

### 2) New Source Discovery Tool

Added `list_sources()` to provide an agent-friendly source catalog including:

- title
- native resolution (`gsd_m`)
- provider
- collection
- signing/auth requirements

### 3) Generalized Catalog Search

Added `search_catalog(...)` to query any registered source by name.

Notable behavior:

- STAC search for supported sources
- automatic cloud filtering when metadata is available
- signed asset URLs for Planetary Computer sources when signer is available
- graceful response for WMS-based non-STAC sources

### 4) Nighttime Lights Access (WMS)

Added `get_nightlights(...)` for open NASA GIBS nighttime imagery.

Returns a ready-to-render PNG URL for the requested bbox/date/layer. This extends support to low-light/nighttime Earth observation use cases.

### 5) Expanded Remote-Sensing ToolBox

Beyond `segment_water(...)`, the server now includes:

- `spectral_index(...)` for NDVI/NDWI-style transformations
- `toolbox_catalog()` for discoverable model/task capabilities

### 6) STAC Item Auto-Generation for SAR

Added `create_stac_item(...)` to standardize SAR scenes into STAC Item format with SAR + Projection extensions. This supports publication-ready metadata workflows.

### 7) Resilient Live-Demo Behavior

Kept fallback/stub behavior for heavy dependencies (e.g., raster processing paths) so the server remains demo-safe in constrained environments.

## Existing Core Tools Retained

These tools remain part of the server and continue to provide core functionality:

- `search_open_data(...)`
- `describe_item(...)`
- `segment_water(...)`

## Notes

- This file is intended as a high-level change log for major server evolution.
- For minor fixes, update this document only when behavior or API surface changes materially.

## Glossary

| Term | Meaning |
| --- | --- |
| MCP | Model Context Protocol, a standard way for AI clients to call external tools and data. |
| MCP server | A program that exposes tools an AI client can call. |
| MCP client | An app or agent that connects to an MCP server. |
| Explorer | The human-facing Gradio interface for trying the MCP tools. |
| Remote sensing | Observing Earth from satellites, aircraft, or sensors without direct contact. |
| Earth observation | Satellite or aerial data about land, water, atmosphere, cities, and oceans. |
| STAC | SpatioTemporal Asset Catalog, a standard for describing geospatial assets. |
| STAC Item | Metadata for one scene, image, or remote-sensing asset. |
| bbox | Bounding box as [min_lon, min_lat, max_lon, max_lat]. |
| COG | Cloud Optimized GeoTIFF, a cloud-friendly raster file format. |
| GSD | Ground sample distance, roughly the real-world size of one image pixel. |
| NIR | Near-infrared band, useful for vegetation and water analysis. |
| SAR | Synthetic Aperture Radar, useful through clouds and at night. |
| NDWI | Normalized Difference Water Index, often used to identify open water. |
| NDVI | Normalized Difference Vegetation Index, often used to identify vegetation. |
| WMS | Web Map Service, a standard way to request map images by URL. |
| Asset URL | A link to an image band or data file returned by a catalog search. |
| Demo mode | A stable fallback output used when heavy raster libraries are not installed. |

## Developer Integration

This project is available as both a web explorer and a hosted MCP endpoint.

Human UI:
https://zlysunshine-mcp4rs-open-earth.hf.space

MCP endpoint:
https://zlysunshine-mcp4rs-open-earth.hf.space/gradio_api/mcp/

MCP schema:
https://zlysunshine-mcp4rs-open-earth.hf.space/gradio_api/mcp/schema

For clients that support remote MCP endpoints directly, use the MCP endpoint URL.
For clients that need a local command bridge, use mcp-remote:

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

## Acknowledgements

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
