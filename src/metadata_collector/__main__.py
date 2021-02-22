#!/usr/env python
import os
import click
import json
import matplotlib.pyplot as plt
import contextily as ctx
from functools import partial

from metadata_collector.metadata_collector import (
    generate_geodataframe,
    get_metadata_from_buckets,
    load_gdb,
)
from metadata_collector.agol_utils import post_gdf_to_agol

click.option = partial(click.option, show_default=True)


@click.command()
@click.option("--project", default="TEST", help="Id of the project, default: TEST")
@click.option(
    "--process_all",
    is_flag=True,
    help="Process all the documents, ignoring the already seen lists",
)
@click.option(
    "--bucket",
    "-b",
    "buckets",
    multiple=True,
    help="""the bucket to scan (optional if you provide the project name),
 you can use multiple buckets using: -b bucket1 -b bucket2 ...""",
)
@click.option(
    "--output_format",
    "-o",
    default="GeoJSON",
    type=click.Choice(["GeoJSON", "GPKG", "Shapefile", "CSV"], case_sensitive=False),
)
@click.option(
    "--output_name",
    default="output",
    help="output name without extension (will be added according to the format)",
)
@click.option("--generate_plot", is_flag=True, help="generate a plot of the map")
@click.option("--hucs_gdb", default="./data/hucs.gdb", type=click.Path(exists=True))
@click.option(
    "--agol_credentials",
    default=None,
    help="""
a json including
username,
password,
endpoint (optional, will use the twiotg instance by default),
folder (optional, will use / by default), and
tags (optional).
example:

--agol_credentials '{
  "username": "theUsername",
  "password": "thePassword",
  "endpoint": "https://theagolinstance.maps.arcmap.com",
  "folder": "/",
  "tags": ["map", "metadata"]
}'
""",
)
def metadata_collector(
    project,
    process_all,
    buckets,
    output_name,
    output_format,
    generate_plot,
    hucs_gdb,
    agol_credentials,
):
    """
    This app will collect the metadata from the buckets for a project
    and create the feature-class map with them.
    """
    metadata_df = None
    if not project:
        if buckets:
            metadata_df = get_metadata_from_buckets(None, process_all, buckets=buckets)
        else:
            click.echo("you must provide either the project name or the buckets list")
    metadata_gdf = generate_geodataframe(
        project,
        process_all=process_all,
        metadata_df=metadata_df,
        hucs_gdf=load_gdb(hucs_gdb),
    )
    if output_format == "Shapefile":
        file_extension = "shp"
        output_format = "ESRI Shapefile"
    else:
        file_extension = output_format.lower()
    metadata_gdf.to_file(f"{output_name}.{file_extension}", driver=output_format)
    if generate_plot:
        # all the rows should have the same projection,
        # so this change should be either enforced by policy or made beforehand
        tmp = metadata_gdf.set_crs(crs="EPSG:4326")
        # to match with the ctx map, we should use web mercator projection:
        ax = tmp.to_crs(epsg=3857).plot(figsize=(100, 100), alpha=0.5)
        ctx.add_basemap(ax)
        plt.savefig(f"{output_name}.png")
    if agol_credentials:
        try:
            credentials = json.loads(agol_credentials)
            post_gdf_to_agol(
                gdf=metadata_gdf, feature_layer_name="datasets_metadata", **credentials
            )
        except json.decoder.JSONDecodeError:
            click.echo(
                f"""
            There was an error reading the
            agol_credentials
            {agol_credentials}"""
            )


metadata_collector()
