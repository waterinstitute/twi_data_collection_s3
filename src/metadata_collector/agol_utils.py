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
    arcgis_ga = GeoAccessor.from_geodataframe(gdf, column_name=column_name)
    gis = GIS("https://twiotg.maps.arcgis.com", "<username>", "<password>")
    arcgis_ga.spatial.to_featurelayer(
        feature_layer_name, tags=tags, folder=folder, gis=gis
    )
