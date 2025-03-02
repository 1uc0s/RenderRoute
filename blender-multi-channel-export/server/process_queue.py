#!/usr/bin/env python3
"""
Process queue for Blender Multi-Channel Export Pipeline

This script monitors a directory for new Blender files, processes them
using the Multi-Channel Export Pipeline addon, and outputs the results.
"""

import os
import sys
import time
import argparse
import subprocess
import shutil
import logging
import glob
from pathlib import Path
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("process_queue.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("ProcessQueue")

class BlenderProcessQueue:
    def __init__(self, input_dir, output_dir, blender_path, addon_path, workers=1):
        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.blender_path = blender_path
        self.addon_path = addon_path
        self.workers = workers
        self.processed_files = set()
        self.processing_files = set()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load previously processed files if any
        self.processed_log = os.path.join(self.output_dir, "processed_files.json")
        if os.path.exists(self.processed_log):
            try:
                with open(self.processed_log, 'r') as f:
                    data = json.load(f)
                    self.processed_files = set(data.get("processed_files", []))
                    logger.info(f"Loaded {len(self.processed_files)} previously processed files")
            except Exception as e:
                logger.error(f"Failed to load processed files log: {e}")
        
    def save_processed_files(self):
        """Save the list of processed files to a JSON file"""
        try:
            with open(self.processed_log, 'w') as f:
                json.dump({
                    "processed_files": list(self.processed_files),
                    "last_updated": datetime.now().isoformat()
                }, f)
            logger.info(f"Saved {len(self.processed_files)} processed files to log")
        except Exception as e:
            logger.error(f"Failed to save processed files log: {e}")
    
    def get_pending_files(self):
        """Get list of .blend files that need processing"""
        all_files = glob.glob(os.path.join(self.input_dir, "*.blend"))
        pending = [f for f in all_files 
                   if f not in self.processed_files 
                   and f not in self.processing_files]
        return pending
    
    def process_file(self, blend_file):
        """Process a single Blender file with the addon"""
        logger.info(f"Processing file: {blend_file}")
        self.processing_files.add(blend_file)
        
        # Create output directory for this file
        file_name = os.path.basename(blend_file)
        base_name = os.path.splitext(file_name)[0]
        file_output_dir = os.path.join(self.output_dir, base_name)
        os.makedirs(file_output_dir, exist_ok=True)
        
        # Copy the .blend file to the output directory
        output_blend = os.path.join(file_output_dir, file_name)
        shutil.copy2(blend_file, output_blend)
        
        # Create Python script to run within Blender
        script_path = os.path.join(file_output_dir, "process.py")
        with open(script_path, 'w') as f:
            f.write(f"""
import bpy

# Make sure addon is enabled
addon_name = "multi_channel_export"
if addon_name not in bpy.context.preferences.addons:
    bpy.ops.preferences.addon_install(filepath="{self.addon_path}")
    bpy.ops.preferences.addon_enable(module=addon_name)

# Setup the pipeline
bpy.ops.export.setup_pipeline(
    use_scene_settings=False,
    base_output_dir="//{base_name}_Output/",
    loop_extend_frames=True,
    hold_frames=15
)

# Render everything
bpy.ops.export.render_all()

# Save the file
bpy.ops.wm.save_as_mainfile(filepath="{output_blend}")
""")
        
        # Run Blender with the script
        cmd = [
            self.blender_path,
            "-b",  # Background mode
            output_blend,  # Use the copied file
            "--python", script_path
        ]
        
        try:
            # Run Blender process
            logger.info(f"Running Blender with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Check for success
            if result.returncode == 0:
                logger.info(f"Successfully processed {blend_file}")
                
                # Copy output files to the final output directory
                output_files_path = os.path.join(file_output_dir, f"{base_name}_Output")
                if os.path.exists(output_files_path):
                    # List all generated video files
                    mobile_video = glob.glob(os.path.join(output_files_path, "MobileOut", "*.mp4"))
                    desktop_video = glob.glob(os.path.join(output_files_path, "DesktopOut", "*.mp4"))
                    
                    # Copy videos with descriptive names
                    for video in mobile_video:
                        dest = os.path.join(file_output_dir, f"{base_name}_mobile.mp4")
                        shutil.copy2(video, dest)
                        logger.info(f"Copied mobile video to {dest}")
                    
                    for video in desktop_video:
                        dest = os.path.join(file_output_dir, f"{base_name}_desktop.mp4")
                        shutil.copy2(video, dest)
                        logger.info(f"Copied desktop video to {dest}")
                
                # Add to processed files
                self.processed_files.add(blend_file)
                self.save_processed_files()
            else:
                logger.error(f"Failed to process {blend_file}")
                logger.error(f"Blender output: {result.stdout}")
                logger.error(f"Blender error: {result.stderr}")
                
                # Write log files for debugging
                with open(os.path.join(file_output_dir, "blender_stdout.log"), 'w') as f:
                    f.write(result.stdout)
                with open(os.path.join(file_output_dir, "blender_stderr.log"), 'w') as f:
                    f.write(result.stderr)
                
        except Exception as e:
            logger.exception(f"Error processing {blend_file}: {e}")
        finally:
            # Always remove from processing list
            self.processing_files.remove(blend_file)
    
    def run(self):
        """Main processing loop"""
        logger.info(f"Starting processing queue")
        logger.info(f"Monitoring input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Blender path: {self.blender_path}")
        logger.info(f"Addon path: {self.addon_path}")
        
        try:
            while True:
                pending = self.get_pending_files()
                if pending:
                    logger.info(f"Found {len(pending)} files to process")
                    for blend_file in pending:
                        self.process_file(blend_file)
                        # Process one file at a time for now
                        # TODO: Implement proper worker threads for parallel processing
                else:
                    logger.info("No files to process, waiting...")
                
                # Sleep before checking again
                time.sleep(10)
        except KeyboardInterrupt:
            logger.info("Interrupted, shutting down...")
        finally:
            self.save_processed_files()

def main():
    parser = argparse.ArgumentParser(description="Blender Multi-Channel Export Processing Queue")
    parser.add_argument("--input", required=True, help="Directory to monitor for .blend files")
    parser.add_argument("--output", required=True, help="Directory to store output files")
    parser.add_argument("--blender", required=True, help="Path to Blender executable")
    parser.add_argument("--addon", required=True, help="Path to addon .zip file")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    
    args = parser.parse_args()
    
    queue = BlenderProcessQueue(
        input_dir=args.input,
        output_dir=args.output,
        blender_path=args.blender,
        addon_path=args.addon,
        workers=args.workers
    )
    
    queue.run()

if __name__ == "__main__":
    main()