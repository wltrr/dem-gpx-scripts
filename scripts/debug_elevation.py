from dem_gpx_utils import ElevationTile
from rasterio.crs import CRS
from rasterio.warp import transform

# 1. Load the specific tile that SHOULD cover Potsdamer Platz
tile_path = "dem_files/berlin_dgm1/tile_33388_5818.tif"
print(f"--- Debugging {tile_path} ---")

try:
    tile = ElevationTile(tile_path)

    # 2. Check if CRS is detected
    print(f"Detected CRS: {tile.crs}")

    # 3. Define Potsdamer Platz (Lat, Lon)
    lat, lon = 52.5096, 13.3759
    print(f"\nTarget Location: Lat {lat}, Lon {lon}")

    # 4. Manually transform to check coordinates
    # If CRS is None, default to EPSG:25833 (Berlin Standard) for testing
    target_crs = tile.crs if tile.crs else CRS.from_epsg(25833)

    xs, ys = transform(tile.wgs84, target_crs, [lon], [lat])
    x, y = xs[0], ys[0]

    print(f"Transformed Coords: X={x:.2f}, Y={y:.2f}")
    print(f"Tile Bounds: Left={tile.bounds.left}, Right={tile.bounds.right}, "
          f"Bottom={tile.bounds.bottom}, Top={tile.bounds.top}")

    # 5. Check coverage
    covers = tile.covers_location(lat, lon)
    print(f"\nMethod .covers_location() returns: {covers}")

    if not tile.crs:
        print("\n[!] CRITICAL: The file has no CRS. You must force EPSG:25833 in the code.")

except Exception as e:
    print(f"Error: {e}")