import requests
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from shapely.geometry import Point

api_url = "https://services1.arcgis.com/RbMX0mRVOFNTdLzd/arcgis/rest/services/MaineFacilitiesStructuresNG911/FeatureServer/6/query"
params = {
    "where": "1=1",
    "outFields": "*",
    "f": "geojson"
}

response = requests.get(api_url, params=params)
hospital_json = response.json()

hospitals = gpd.GeoDataFrame.from_features(hospital_json["features"])
print("✅ Loaded hospitals:", len(hospitals))

if hospitals.crs is None:
    hospitals.set_crs("EPSG:4326", allow_override=True, inplace=True)

towns = gpd.read_file("Maine_Hospitals_E911.shp")
towns["centroid"] = towns.geometry.centroid
towns = towns.set_geometry("centroid")

hospitals = hospitals.to_crs("EPSG:4326").to_crs("EPSG:3857")
towns = towns.to_crs("EPSG:4326").to_crs("EPSG:3857")

def nearest_distance(point, gdf_targets):
    return gdf_targets.distance(point).min()

towns["nearest_hosp_dist_m"] = towns.geometry.apply(lambda x: nearest_distance(x, hospitals))
towns["nearest_hosp_dist_km"] = towns["nearest_hosp_dist_m"] / 1000

fig1, ax1 = plt.subplots(figsize=(12, 10))
towns.plot(
    column="nearest_hosp_dist_km",
    cmap="YlOrRd",
    legend=True,
    ax=ax1,
    edgecolor="black",
    alpha=0.6
)
hospitals.plot(ax=ax1, color="blue", markersize=20, label="Hospitals")
ctx.add_basemap(ax1, source=ctx.providers.OpenStreetMap.Mapnik, crs=towns.crs)

ax1.set_title("Distance from Each Maine Town to Nearest Hospital (km)")
ax1.set_xlabel("Easting (meters)")
ax1.set_ylabel("Northing (meters)")
ax1.legend()
ax1.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

fig2, ax2 = plt.subplots(figsize=(12, 10))
hospitals.plot(ax=ax2, color="darkred", markersize=15, label="Hospitals")
ctx.add_basemap(ax2, source=ctx.providers.OpenStreetMap.Mapnik, crs=hospitals.crs)

ax2.set_title("All Hospital Locations in Maine")
ax2.set_xlabel("Easting (meters)")
ax2.set_ylabel("Northing (meters)")
ax2.legend()
ax2.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()

plt.show()

towns[["NAME", "nearest_hosp_dist_km"]].sort_values("nearest_hosp_dist_km").to_csv("output/town_hospital_distances.csv", index=False)