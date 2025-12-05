import argparse
import logging
from pathlib import Path
import gpxpy
from tqdm import tqdm
from dem_gpx_utils import ElevationTile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def load_dem_tiles(dem_folder: Path):
    """
    Scans the folder for .tif files and returns a list of ElevationTile objects.
    """
    tiles = []
    tif_files = list(dem_folder.glob("*.tif"))

    if not tif_files:
        logging.warning(f"No .tif files found in {dem_folder}")
        return tiles

    logging.info(f"Loading {len(tif_files)} DEM tiles from {dem_folder}...")

    for tif_path in tqdm(tif_files, desc="Initializing Tiles"):
        try:
            tile = ElevationTile(tif_path)
            tiles.append(tile)
        except Exception as e:
            logging.error(f"Failed to load {tif_path}: {e}")

    return tiles


def process_gpx(gpx_path: Path, tiles: list[ElevationTile], output_path: Path):
    """
    Parses GPX, updates elevation for all track points, and saves the result.
    """
    with open(gpx_path, 'r') as f:
        gpx = gpxpy.parse(f)

    updated_count = 0
    total_points = 0

    # Count total points for progress bar
    for track in gpx.tracks:
        for segment in track.segments:
            total_points += len(segment.points)

    logging.info(f"Processing {total_points} points in {gpx_path.name}...")

    # Iterate through all tracks, segments, and points
    with tqdm(total=total_points, desc="Correcting Elevation") as pbar:
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    elevation_found = False
                    # Check which tile covers this point
                    for tile in tiles:

                        if tile.covers_location(point.latitude, point.longitude):
                            elev = tile.get_elevation(point.latitude, point.longitude)
                            if elev is not None:
                                point.elevation = elev
                                updated_count += 1
                                elevation_found = True
                                break  # Stop searching tiles once found

                    pbar.update(1)

    # Save the modified GPX
    with open(output_path, 'w') as f:
        f.write(gpx.to_xml())

    logging.info(f"Done. Updated {updated_count}/{total_points} points.")
    logging.info(f"Saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Correct GPX elevation using local DEM (.tif) files.")
    parser.add_argument("gpx_file", type=Path, help="Path to the input GPX file")
    parser.add_argument("dem_folder", type=Path, help="Folder containing .tif DEM files")
    parser.add_argument("--output", "-o", type=Path, help="Path for the output GPX file (optional)")

    args = parser.parse_args()

    if not args.gpx_file.exists():
        logging.error(f"GPX file not found: {args.gpx_file}")
        return

    if not args.dem_folder.exists():
        logging.error(f"DEM folder not found: {args.dem_folder}")
        return

    # Determine output path if not provided
    if args.output:
        output_path = args.output
    else:
        # Default: input_name_corrected.gpx
        output_path = args.gpx_file.with_name(f"{args.gpx_file.stem}_corrected{args.gpx_file.suffix}")

    # 1. Load Tiles
    tiles = load_dem_tiles(args.dem_folder)

    if not tiles:
        logging.error("No valid tiles loaded. Exiting.")
        return

    try:
        # 2. Process GPX
        process_gpx(args.gpx_file, tiles, output_path)
    finally:
        # 3. Cleanup: Close all open file handles
        for tile in tiles:
            tile.close()


if __name__ == "__main__":
    main()