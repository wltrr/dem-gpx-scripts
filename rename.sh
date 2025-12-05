#!/usr/bin/env fish

# 1. Rename Berlin Files
# Format: dgm1_33_388_5818_2_be.tif -> tile_33388_5818.tif
# We combine Zone (33) and Easting (388) to match the likely projection prefix
echo "Renaming Berlin files..."
cd dem_files/berlin_dgm1
for file in dgm1_*.tif
    # Match: dgm1_33_388_5818...
    set matches (string match -r 'dgm1_(33)_(\d+)_(\d+)_.*\.tif' $file)
    if set -q matches[2]
        # matches[2]=33, matches[3]=388, matches[4]=5818
        set new_name "tile_"$matches[2]$matches[3]"_"$matches[4]".tif"
        mv $file $new_name
    end
end
cd ../..

# 2. Rename Baden-Württemberg Files
# Format: dgm025_32_505_5324_1_bw_2022.tif -> tile_32505_5324.tif
echo "Renaming BW files..."
cd dem_files/bw_dgm025
for file in dgm025_*.tif
    set matches (string match -r 'dgm025_(32)_(\d+)_(\d+)_.*\.tif' $file)
    if set -q matches[2]
        set new_name "tile_"$matches[2]$matches[3]"_"$matches[4]".tif"
        mv $file $new_name
    end
end
cd ../..

# 3. Rename Swiss Files
# Format: swissalti3d_2024_2622-1094_0.5_2056_5728.tif -> tile_2622_1094.tif
echo "Renaming Swiss files..."
cd dem_files/swissalti3d
for file in swissalti3d_*.tif
    # Match: ..._2622-1094_...
    set matches (string match -r 'swissalti3d_\d+_(\d+)-(\d+)_.*\.tif' $file)
    if set -q matches[2]
        set new_name "tile_"$matches[2]"_"$matches[3]".tif"
        mv $file $new_name
    end
end
cd ../..

echo "All done!"