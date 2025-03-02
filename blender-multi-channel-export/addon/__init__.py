bl_info = {
    "name": "Multi-Channel Export Pipeline",
    "author": "Your Name",
    "version": (1, 3, 0),  # Increment this when making changes (major, minor, patch)
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Export Tab",
    "description": "Creates a one-click pipeline for exporting scenes to frames and videos",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty

# Import all operators and panels
from .operators.setup import MultiChannelExportPipelineSetup
from .panels.export_panel import MultiChannelExportPanel

# Import render operators directly 
from .operators.render import (
    RenderAllOperator,
    RenderMobileOnlyOperator,
    RenderDesktopOnlyOperator,
    AdvancedRenderSettingsOperator,
    SwitchToSceneOperator
)

# Define addon version as string for display
__version__ = ".".join(str(v) for v in bl_info["version"])

# Registration
classes = (
    MultiChannelExportPipelineSetup,
    RenderAllOperator,
    RenderMobileOnlyOperator,
    RenderDesktopOnlyOperator,
    AdvancedRenderSettingsOperator,
    SwitchToSceneOperator,
    MultiChannelExportPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Add custom properties to store loop settings
    bpy.types.Scene.loop_extend_frames = BoolProperty(
        name="Create Loop Animation",
        description="Create a loop by playing forwards, holding last frame, playing backwards, and holding first frame",
        default=False
    )
    
    bpy.types.Scene.hold_frames = IntProperty(
        name="Hold Frames",
        description="Number of frames to hold at the end and beginning for looping",
        default=15,
        min=1,
        max=120
    )
    
    # Store version for UI display
    bpy.types.Scene.mce_addon_version = StringProperty(
        name="Addon Version",
        description="Current version of the Multi-Channel Export Pipeline addon",
        default=__version__,
        options={'HIDDEN'}
    )

def unregister():
    # Remove custom properties
    del bpy.types.Scene.loop_extend_frames
    del bpy.types.Scene.hold_frames
    del bpy.types.Scene.mce_addon_version
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()