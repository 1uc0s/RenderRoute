#!/usr/bin/env python3
"""
Build script for the Blender Multi-Channel Export Pipeline addon.
Creates a distributable ZIP file that can be installed in Blender.
"""

import os
import sys
import zipfile
import shutil
import argparse
from datetime import datetime

def build_addon(version=None):
    """Build the addon as a distributable ZIP file"""
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    addon_dir = os.path.join(base_dir, "addon")
    
    # Create dist directory if it doesn't exist
    dist_dir = os.path.join(base_dir, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    
    # Set version
    if version is None:
        # Use current date as version if not specified
        now = datetime.now()
        version = f"{now.year}.{now.month}.{now.day}"
    
    # Create temporary directory for build
    build_dir = os.path.join(base_dir, "build")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    # Copy addon files to build directory
    shutil.copytree(addon_dir, os.path.join(build_dir, "multi_channel_export"))
    
    # Zip the addon
    zip_file = os.path.join(dist_dir, f"multi_channel_export_{version}.zip")
    with zipfile.ZipFile(zip_file, 'w') as zf:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith(".py") or file.endswith(".txt"):
                    file_path = os.path.join(root, file)
                    # Get relative path for ZIP
                    rel_path = os.path.relpath(file_path, build_dir)
                    zf.write(file_path, rel_path)
    
    # Clean up build directory
    shutil.rmtree(build_dir)
    
    print(f"Build completed: {zip_file}")
    return zip_file

def main():
    parser = argparse.ArgumentParser(description="Build the Blender Multi-Channel Export Pipeline addon")
    parser.add_argument("--version", help="Version number for the build")
    
    args = parser.parse_args()
    build_addon(args.version)

if __name__ == "__main__":
    main()