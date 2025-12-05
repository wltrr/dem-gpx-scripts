import rasterio
from rasterio.warp import transform
from rasterio.crs import CRS
import numpy as np
from scipy.interpolate import interpn


class ElevationTile:
    def __init__(self, file_path):
        """
        Initialize with a path to a .tif file.
        Loads the ENTIRE dataset into memory and pre-calculates grid coordinates
        for fast interpolation.
        """
        self.file_path = file_path
        self.dataset = rasterio.open(file_path)
        self.bounds = self.dataset.bounds
        self.crs = self.dataset.crs
        self.wgs84 = CRS.from_epsg(4326)

        # 1. Load the full elevation array into memory
        # Reading band 1. Shape is (height, width) -> (rows, cols)
        self.data = self.dataset.read(1)

        # 2. Pre-calculate the real-world coordinates for pixel centers
        # We need these to define the 'grid' for scipy.interpolate.interpn
        height, width = self.data.shape
        aff = self.dataset.transform

        # Generate array of column indices (0 to width-1) and row indices
        cols = np.arange(width)
        rows = np.arange(height)

        # Calculate x coordinates (cols) and y coordinates (rows) for pixel centers
        # Affine transform: x_geo = a * col + b * row + x_off
        # We use +0.5 to shift from top-left corner to pixel center
        self.xs = aff.c + (cols + 0.5) * aff.a
        self.ys = aff.f + (rows + 0.5) * aff.e

        # Note: GeoTIFFs often have descending Y coordinates (top to bottom).
        # scipy.interpn handles strictly descending coordinates correctly.

    def covers_location(self, lat, lon):
        """
        Check if the specific lat/lon (WGS84) falls within the tile bounds.
        """
        src_crs = self.crs if self.crs else CRS.from_epsg(25833)
        xs, ys = transform(self.wgs84, src_crs, [lon], [lat])
        x, y = xs[0], ys[0]

        min_x, max_x = sorted((self.bounds.left, self.bounds.right))
        min_y, max_y = sorted((self.bounds.bottom, self.bounds.top))

        return (min_x <= x <= max_x and min_y <= y <= max_y)

    def get_elevation(self, lat, lon, method='linear'):
        """
        Retrieve elevation at the specific lat/lon using interpolation.

        Parameters:
        - method: 'nearest', 'linear', 'cubic', 'quintic'
        """
        # Quick bounds check
        if not self.covers_location(lat, lon):
            return None

        src_crs = self.crs if self.crs else CRS.from_epsg(25833)

        # Transform WGS84 (lon, lat) -> Project CRS (x, y)
        proj_xs, proj_ys = transform(self.wgs84, src_crs, [lon], [lat])
        target_x, target_y = proj_xs[0], proj_ys[0]

        # Interpolate
        # Points tuple must match data shape: (rows/y, cols/x)
        # Query point must match that order: (target_y, target_x)
        try:
            result = interpn(
                (self.ys, self.xs),  # The grid points (y-axis, x-axis)
                self.data,  # The values
                np.array([target_y, target_x]),  # The query point
                method=method,
                bounds_error=False,  # Return nan instead of crashing on edges
                fill_value=np.nan
            )
            return result[0]
        except ValueError:
            # Fallback if specific interpolation math fails (rare with bounds_error=False)
            return None

    def close(self):
        """Close the file handle."""
        self.dataset.close()
        # Optional: Clear large data from memory if object persists but is 'closed'
        self.data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()