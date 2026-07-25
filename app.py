import gradio as gr

from server import (
    list_sources as _list_sources,
    search_catalog as _search_catalog,
    get_nightlights as _get_nightlights,
    segment_water as _segment_water,
    create_stac_item as _create_stac_item,
)


def list_remote_sensing_sources() -> dict:
    """List open remote-sensing sources available through this MCP demo."""
    return _list_sources()


def search_open_imagery(
    source: str,
    bbox: list[float],
    datetime_range: str,
    max_items: int,
    max_cloud_cover: float,
) -> dict:
    """Search an open Earth-observation catalog.

    Args:
        source: Data source key, such as sentinel-2, landsat, naip, sentinel-1, or nightlights.
        bbox: Bounding box as [min_lon, min_lat, max_lon, max_lat].
        datetime_range: STAC datetime range, for example 2025-01-01/2025-06-30.
        max_items: Maximum number of scenes to return.
        max_cloud_cover: Maximum cloud cover percentage.

    Returns:
        A JSON object containing matching scenes, metadata, assets, and provenance.
    """
    return _search_catalog(
        source=source,
        bbox=bbox,
        datetime_range=datetime_range or None,
        max_items=int(max_items),
        max_cloud_cover=float(max_cloud_cover),
    )


def get_nightlights_image(
    bbox: list[float],
    date: str,
    width: int,
    height: int,
) -> dict:
    """Fetch an open NASA VIIRS nighttime-lights image URL.

    Args:
        bbox: Bounding box as [min_lon, min_lat, max_lon, max_lat].
        date: Date in YYYY-MM-DD format.
        width: Output image width in pixels.
        height: Output image height in pixels.

    Returns:
        A JSON object with a ready-to-render image URL and provenance metadata.
    """
    return _get_nightlights(bbox=bbox, date=date, width=int(width), height=int(height))


def measure_water_fraction(
    red_href: str,
    green_href: str,
    blue_href: str,
    nir_href: str,
) -> dict:
    """Estimate water fraction from Sentinel-2 asset URLs.

    Args:
        red_href: Red band asset URL.
        green_href: Green band asset URL.
        blue_href: Blue band asset URL.
        nir_href: Near-infrared band asset URL.

    Returns:
        Water-fraction statistics. Uses a deterministic demo stub if rasterio is unavailable.
    """
    return _segment_water(red_href, green_href, blue_href, nir_href)


def create_sar_stac_item(
    item_id: str,
    bbox: list[float],
    datetime_iso: str,
    hh_href: str,
    hv_href: str,
    platform: str,
    frequency_band: str,
) -> dict:
    """Create a STAC Item for a SAR scene.

    Args:
        item_id: Unique SAR scene ID.
        bbox: Bounding box as [min_lon, min_lat, max_lon, max_lat].
        datetime_iso: Acquisition datetime in ISO-8601 format.
        hh_href: HH polarization asset URL.
        hv_href: Optional HV polarization asset URL.
        platform: SAR platform name.
        frequency_band: SAR frequency band, such as C or L.

    Returns:
        A STAC-compliant SAR Item dictionary.
    """
    return _create_stac_item(item_id, bbox, datetime_iso, hh_href, hv_href, platform, frequency_band)


with gr.Blocks(title="Remote Sensing MCP Demo") as demo:
    gr.Markdown("# Remote Sensing MCP Demo")
    gr.Markdown("Open satellite-data discovery and remote-sensing analysis as MCP tools.")

    with gr.Tab("Sources"):
        source_out = gr.JSON(label="Available sources")
        gr.Button("List sources").click(
            list_remote_sensing_sources,
            outputs=source_out,
            api_name="list_remote_sensing_sources",
            queue=False,
        )

    with gr.Tab("Search Imagery"):
        source = gr.Dropdown(
            choices=["sentinel-2", "naip", "landsat", "sentinel-1", "nightlights"],
            value="sentinel-2",
            label="Source",
        )
        bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")
        dates = gr.Textbox(value="2025-01-01/2025-06-30", label="Date range")
        max_items = gr.Number(value=3, precision=0, label="Max items")
        cloud = gr.Number(value=30, label="Max cloud cover")
        search_out = gr.JSON(label="Search results")
        gr.Button("Search").click(
            search_open_imagery,
            inputs=[source, bbox, dates, max_items, cloud],
            outputs=search_out,
            api_name="search_open_imagery",
            queue=False,
        )

    with gr.Tab("Nightlights"):
        night_bbox = gr.JSON(value=[113.8, 22.1, 114.5, 22.8], label="Bounding box")
        night_date = gr.Textbox(value="2023-01-01", label="Date")
        width = gr.Number(value=512, precision=0, label="Width")
        height = gr.Number(value=512, precision=0, label="Height")
        night_out = gr.JSON(label="Nightlights result")
        gr.Button("Get nightlights").click(
            get_nightlights_image,
            inputs=[night_bbox, night_date, width, height],
            outputs=night_out,
            api_name="get_nightlights_image",
            queue=False,
        )

    with gr.Tab("Water Fraction"):
        red = gr.Textbox(label="Red band URL")
        green = gr.Textbox(label="Green band URL")
        blue = gr.Textbox(label="Blue band URL")
        nir = gr.Textbox(label="NIR band URL")
        water_out = gr.JSON(label="Water fraction")
        gr.Button("Measure water").click(
            measure_water_fraction,
            inputs=[red, green, blue, nir],
            outputs=water_out,
            api_name="measure_water_fraction",
            queue=False,
        )

    with gr.Tab("SAR to STAC"):
        item_id = gr.Textbox(value="HAISHAO1_SAR_20250118_HAINAN_0001", label="Item ID")
        sar_bbox = gr.JSON(value=[109.0, 18.0, 111.0, 20.0], label="Bounding box")
        dt = gr.Textbox(value="2025-01-18T03:21:00Z", label="Datetime")
        hh = gr.Textbox(value="s3://example/HH.tif", label="HH asset")
        hv = gr.Textbox(value="s3://example/HV.tif", label="HV asset")
        platform = gr.Textbox(value="HaiShao-1", label="Platform")
        band = gr.Textbox(value="C", label="Frequency band")
        stac_out = gr.JSON(label="STAC item")
        gr.Button("Create STAC Item").click(
            create_sar_stac_item,
            inputs=[item_id, sar_bbox, dt, hh, hv, platform, band],
            outputs=stac_out,
            api_name="create_sar_stac_item",
            queue=False,
        )


if __name__ == "__main__":
    demo.launch(mcp_server=True)