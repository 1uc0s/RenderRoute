import sys
import os
import bpy

def run(addon_path):
    """Test loading the addon in Blender"""
    print(f"Testing addon loading from: {addon_path}")
    
    # Make sure the addon path exists
    if not os.path.exists(addon_path):
        print(f"ERROR: Addon path does not exist: {addon_path}")
        sys.exit(1)
    
    # Try to install the addon
    try:
        bpy.ops.preferences.addon_install(filepath=addon_path)
        print("Addon installed successfully")
    except Exception as e:
        print(f"ERROR: Failed to install addon: {e}")
        sys.exit(1)
    
    # Try to enable the addon
    try:
        bpy.ops.preferences.addon_enable(module="multi_channel_export")
        print("Addon enabled successfully")
    except Exception as e:
        print(f"ERROR: Failed to enable addon: {e}")
        sys.exit(1)
    
    # Check if the addon is actually registered
    if "multi_channel_export" not in bpy.context.preferences.addons:
        print("ERROR: Addon not in enabled addons list")
        sys.exit(1)
    
    # Check if the operators and panels are registered
    try:
        # Check for the pipeline setup operator
        if not hasattr(bpy.ops.export, "setup_pipeline"):
            print("ERROR: setup_pipeline operator not registered")
            sys.exit(1)
        
        # Check for the render operators
        if not hasattr(bpy.ops.export, "render_all"):
            print("ERROR: render_all operator not registered")
            sys.exit(1)
        
        if not hasattr(bpy.ops.export, "render_mobile"):
            print("ERROR: render_mobile operator not registered")
            sys.exit(1)
        
        if not hasattr(bpy.ops.export, "render_desktop"):
            print("ERROR: render_desktop operator not registered")
            sys.exit(1)
        
        if not hasattr(bpy.ops.export, "switch_to_scene"):
            print("ERROR: switch_to_scene operator not registered")
            sys.exit(1)
        
        print("All operators registered successfully")
    except Exception as e:
        print(f"ERROR: Failed to check operators: {e}")
        sys.exit(1)
    
    print("Addon loaded and verified successfully")
    
if __name__ == "__main__":
    # This script is meant to be run from Blender's Python interpreter
    if len(sys.argv) > 1:
        addon_path = sys.argv[1]
        run(addon_path)
    else:
        print("ERROR: No addon path provided")
        sys.exit(1)