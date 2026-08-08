---
title: MCP4RS Open Earth Explorer
emoji: 🛰️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: "6.20.0"
python_version: "3.11"
app_file: app.py
pinned: false
tags:
  - mcp
  - remote-sensing
  - earth-observation
  - stac
  - geospatial
---

# MCP4RS: Open Earth Remote Sensing MCP [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21851165.svg)](https://doi.org/10.5281/zenodo.21851165)

Ask the Earth a question: discover, analyze, and explain open satellite data through MCP.

> **Provenance & attribution.** The MCP server in this repository is derived from the
> original remote-sensing MCP server authored by **Dongping Liu** (from the Hainan
> land-sea SAR project), developed with **Luyao Zhang**. It is MIT-licensed; the original
> copyright notice is retained in [LICENSE](LICENSE), and authorship is noted in the
> [server.py](server.py) header.

## Overview

This repository provides two local run modes:

1. Gradio web app with MCP endpoint, launched from [app.py](app.py).
2. MCP stdio server for local MCP clients, launched from [server.py](server.py).

Use the app mode if you want a browser UI. Use stdio mode if you want to connect tools directly from an MCP client.

## Local deployment prerequisites

- Linux, macOS, or Windows with Python 3.11+.
- `pip` available in your shell.
- Network access for remote open-data catalogs (STAC/NASA GIBS).

## 1) Set up a local Python environment

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optional quick syntax check:

```bash
python -m py_compile app.py server.py stac_convert.py
```

## 2) Run the Gradio app locally

Start the app:

```bash
python app.py
```

By default, Gradio serves locally (typically on `http://127.0.0.1:7860`).

This app launches with `mcp_server=True`, so you get both:

- Web UI for interactive use.
- MCP HTTP endpoint exposed by Gradio at:
  - `http://127.0.0.1:7860/gradio_api/mcp/`
  - `http://127.0.0.1:7860/gradio_api/mcp/schema`

## 3) Run the MCP stdio server locally

If your MCP client expects a local command-based server, run:

```bash
python server.py
```

This starts the FastMCP server over stdio (no browser UI).

Example MCP client config:

```json
{
  "mcpServers": {
    "mcp4rs-open-earth-local": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/TO/mcp4rs-open-earth/server.py"]
    }
  }
}
```

## 4) Validate local deployment

After launching `python app.py`:

1. Open the local URL shown in terminal (usually `http://127.0.0.1:7860`).
2. In the UI, run `Sources` to confirm tool invocation works.
3. Test a simple query in `Search Sentinel-2` with a known bbox/date.

For stdio mode (`python server.py`), validate by connecting from your MCP client and calling `list_sources`.

## 5) Optional extra dependencies for real raster computation

The analysis tools have stub fallbacks when heavy raster libs are missing.
To enable real raster-based execution for `segment_water` and `spectral_index`, install:

```bash
python -m pip install rasterio numpy
```

## Troubleshooting

- `ModuleNotFoundError: pystac_client`:
  - Re-run `python -m pip install -r requirements.txt`.
- Port already in use:
  - Stop the previous process or run in a clean terminal session.
- Empty search results:
  - Use a valid bbox/date range and relax cloud-cover threshold.
- Planetary Computer signed URLs not applied:
  - Install optional package: `python -m pip install planetary-computer`.

## Production note

This repository is configured for Hugging Face Spaces with Gradio MCP support, but the commands above are the recommended path for local deployment and testing.
