bl_info = {
    "name": "Multi-Channel Export Pipeline",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Export Tab",
    "description": "Creates a one-click pipeline for exporting scenes to frames and videos",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
from bpy.props import BoolProperty, IntProperty

# Import all operators and panels
from .operators.setup import MultiChannelExportPipelineSetup
from .operators.render import (
    RenderAllOperator,
    RenderMobileOnlyOperator,
    RenderDesktopOnlyOperator,
    SwitchToSceneOperator
)
from .panels.export_panel import MultiChannelExportPanel

# Registration
classes = (
    MultiChannelExportPipelineSetup,
    RenderAllOperator,
    RenderMobileOnlyOperator,
    RenderDesktopOnlyOperator,
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

def unregister():
    # Remove custom properties
    del bpy.types.Scene.loop_extend_frames
    del bpy.types.Scene.hold_frames
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()