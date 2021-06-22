"""
Utilities to work with Arcgis online
"""
import tempfile
from arcgis import GIS
from arcgis.features import FeatureLayerCollection


def post_gdf_to_agol(
    gdf,
    username,
    password,
    feature_layer_name,
    folder="/",
    endpoint="https://twiotg.maps.arcgis.com",
    tags=None,
):
    """Post the information of the geodataframe (gdf) to
    the given AGOL instance(endpoint) under the user credentials.
    """
    try:
        gis = GIS(endpoint, username, password)
        ex_item = None
        for item in gis.users.me.items(folder=folder):
            if item.title == feature_layer_name:
                ex_item = item
                break
        with tempfile.NamedTemporaryFile(delete=True, suffix=".geojson") as tmp_geojson:
            gdf.to_file(tmp_geojson, driver="GeoJSON")
            if ex_item is None:
                gis.content.add(
                    item_properties={
                        "type": "GeoJson",
                        "title": feature_layer_name,
                        "typeKeywords": [
                            "Coordinates Type",
                            "CRS",
                            "Feature",
                            "FeatureCollection",
                            "GeoJSON",
                            "Geometry",
                            "GeometryCollection",
                        ],  # this seems to be what manual add will add, works without this as well
                        "description": "Metadata for the datasets on the object storage",
                        "tags": tags,
                        "overwrite": True,
                    },
                    data=tmp_geojson.name,
                    folder=folder,
                )
            else:
                ex_item.update(
                    item_properties={
                        "type": "GeoJson",
                        "title": feature_layer_name,
                        "typeKeywords": [
                            "Coordinates Type",
                            "CRS",
                            "Feature",
                            "FeatureCollection",
                            "GeoJSON",
                            "Geometry",
                            "GeometryCollection",
                        ],  # this seems to be what manual add will add, works without this as well
                        "description": "Metadata for the datasets on the object storage",
                        "tags": tags,
                        "overwrite": True,
                    },
                    data=tmp_geojson.name,
                )
                ex_item.publish(overwrite=True)
    except Exception as _e:
        print(f"error publishing to AGOL {str(_e)}")
