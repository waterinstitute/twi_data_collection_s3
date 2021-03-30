"""
Collect the metadata from AWS S3 (or similar) datastores
and generates the feature class with it.
"""
import glob
import json
from hashlib import sha3_256
from urllib.parse import urlparse

import boto3  # aws client api
import geopandas
import pandas as pd
import yaml
from botocore.client import Config

# to work with maps:
from shapely import ops, wkt

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
_TEST_ENDPOINT = "http://localhost:9000"
_DEFAULT_BUCKETS = {
    "GLO": ["glo-data"],
    "LWI": ["lwi-common", *[f"lwi-region{x}" for x in range(1, 8)]],
    "TEST": ["test-bucket"],
}


def huc2geometry(huc_code, hucs_gdf):
    """
    If the code is huc_8 returns the geometry from the hucs_gdf.
    If it is a huc 4 or 6, it returns the union of the geometries of the matching rows.
    params:
        x: a string or an number representing the huc.
        hucs_gdf: a geodataframe with the necessary hucs
        it needs to have.
    """
    if pd.isna(huc_code):
        return None
    huc_s = str(int(huc_code))
    huc_type = len(huc_s)
    if huc_type == 8:
        return hucs_gdf.loc[hucs_gdf.HUC_8 == huc_s].geometry.values[0]
    values = hucs_gdf.loc[hucs_gdf[f"HUC_{huc_type}"] == huc_s].geometry.values
    return ops.unary_union(values)


def hash_doc(doc):
    """
    Return the sha3 hash for the given document
    params:
        doc: a serializable object (usually a dictionary)
    """
    return sha3_256(json.dumps(doc, default=str).encode("utf-8")).hexdigest()


def get_metadata_from_buckets(project, process_all=True, buckets=None):
    """
    get the data from the buckets of the project
    """
    boto3.setup_default_session(profile_name=project)
    kargs = {}
    if project == "TEST":
        kargs["endpoint_url"] = _TEST_ENDPOINT
        kargs["config"] = Config(signature_version="s3v4")
    if not buckets:
        buckets = _DEFAULT_BUCKETS[project]
    already_seen = []
    if not process_all:
        hash_files = glob.glob("processed_hash_*")
        if hash_files:
            _pdf = pd.concat(map(pd.read_csv, hash_files))
            already_seen = _pdf.metadata_hash.to_list()
    s3 = boto3.resource("s3", **kargs)
    metadata_list = []
    metadata_files = []
    for _b in buckets:
        try:
            s3_bucket = s3.Bucket(_b)
            metadata_files.extend(
                [
                    f"{x.key}"
                    for x in s3_bucket.objects.all()
                    if any(
                        map(
                            x.key.__contains__,
                            [
                                "metadata.yml",
                                "metadata-external.yml",
                                "metadata.yaml",
                                "metadata-external.yaml",
                            ],
                        )
                    )
                ]
            )
        except Exception:
            print(f"Error reading {_b}")

    for mfile in metadata_files:
        obj = s3_bucket.Object(mfile).get()
        content = obj["Body"].read()
        metadata_gen = yaml.load_all(content, Loader=Loader)
        folder = f"s3://{s3_bucket.name}.s3.amazonaws.com/{s3_bucket.name}/{mfile[:mfile.rfind('/')+1]}"
        try:
            for document in metadata_gen:
                if isinstance(document, list):
                    for _d in document:
                        _d["metadata_hash"] = hash_doc(_d)
                        _d["metadata_folder"] = folder
                    metadata_list.extend(document)
                else:
                    document["metadata_hash"] = hash_doc(document)
                    document["metadata_folder"] = folder
                    metadata_list.append(document)
        except yaml.error.YAMLError:
            print(
                f"Invalid syntax on s3://{s3_bucket.name}{mfile}, the dataset(s) defined on it will be ignored"
            )
            continue
    metadata_df = pd.json_normalize(metadata_list)
    metadata_df.drop(
        metadata_df[metadata_df.metadata_hash.isin(already_seen)].index, inplace=True
    )

    # If all the datasets has been already seen, exit.
    return metadata_df


def generate_geodataframe(
    project: str, hucs_gdf=None, process_all=True, metadata_df=None
):
    """
    Generate a geodataframe for all the buckets of a given project
    param:
        project: project name (str), mandatory if metadata_df is not provided.
        process_all: either process all the documents or only the ones we have not seen (bool)
        metadata_df: optional, do not collect the data from s3, use this dataframe instead.
    """
    metadata_df = (
        get_metadata_from_buckets(project, process_all)
        if not metadata_df
        else metadata_df
    )
    metadata_df["limits"] = (
        metadata_df.bounds_wkt.apply(lambda x: wkt.loads(x) if pd.notnull(x) else None)
        if "bounds_wkt" in metadata_df
        else None
    )
    if "bounds_huc" in metadata_df and hucs_gdf is not None and not hucs_gdf.empty:
        metadata_df["limits"] = metadata_df.apply(
            lambda row: huc2geometry(row.bounds_huc, hucs_gdf)
            if pd.notnull(row.bounds_huc)
            else row.limits,
            axis=1,
        )
    metadata_df.index_location = metadata_df.apply(
        lambda x: x.index_location
        if bool(urlparse(x.index_location).netloc)
        else f"{x.metadata_folder}{x.index_location}",
        axis=1,
    )
    metadata_df["name"] = metadata_df["global_attributes.title"]
    metadata_gdf = geopandas.GeoDataFrame(metadata_df, geometry=metadata_df.limits)
    metadata_gdf = metadata_gdf.drop(
        columns=["limits", "bounds_wkt"], errors="ignore"
    )  # ignore if they don't exists
    metadata_gdf = metadata_gdf.set_crs(crs="EPSG:4326")
    if "measurements" in metadata_gdf:
        metadata_gdf["measurements"] = metadata_gdf["measurements"].apply(
            lambda x: json.dumps(x, default=str) if x is not None else None
        )
    for col in metadata_gdf:
        metadata_gdf[col] = metadata_gdf[col].apply(
            lambda x: x if not isinstance(x, list) else json.dumps(x, default=str)
        )
    return metadata_gdf


def load_gdb(gdb):
    """
    Load the geodatabase with the region boundaries
    """
    gdf = geopandas.read_file(gdb)
    if gdf.empty:  # probably is using the USGS dataset
        gdf = geopandas.read_file(gdb, layer="WBDHU8")
        gdf = gdf.rename(columns={"HUC8": "HUC_8"})
    return gdf
