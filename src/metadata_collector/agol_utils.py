from arcgis import GeoAccessor, GIS
import geopandas as gpd


def post_gdf_to_agol(
    gdf,
    username,
    password,
    feature_layer_name,
    column_name="geometry",
    folder="/",
    endpoint="https://twiotg.maps.arcgis.com",
    tags=None,
):
    """Post the information of the geodataframe (gdf) to
    the given AGOL instance(endpoint) under the user credentials.
    """
    try:
        arcgis_ga = GeoAccessor.from_geodataframe(gdf, column_name=column_name)
        gis = GIS(endpoint, username, password)
        arcgis_ga.spatial.to_featurelayer(
            feature_layer_name, tags=tags, folder=folder, gis=gis
        )
    except Exception as e:
        print(f"error publishing to AGOL {str(e)}")
