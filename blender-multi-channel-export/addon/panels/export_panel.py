import bpy
import os
from bpy.types import Panel

class MultiChannelExportPanel(Panel):
    """Panel for Multi-Channel Export"""
    bl_label = "Multi-Channel Export"
    bl_idname = "RENDER_PT_multi_channel_export"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def draw(self, context):
        layout = self.layout
        
        # Setup pipeline section
        box = layout.box()
        box.label(text="Pipeline Setup", icon='MODIFIER')
        box.operator("export.setup_pipeline", text="Setup Export Pipeline")
        
        # Looping controls section
        box = layout.box()
        box.label(text="Animation Loop Settings", icon='LOOP_FORWARDS')
        
        # Get the control scene for looping settings
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        
        row = box.row()
        row.prop(control_scene, "loop_extend_frames", text="Create Loop Animation")
        
        # Only enable hold frames control if looping is enabled
        sub = box.row()
        sub.enabled = control_scene.loop_extend_frames
        sub.prop(control_scene, "hold_frames", text="Hold Frames")
        
        # Add description of the looping process
        if control_scene.loop_extend_frames:
            info_box = box.box()
            info_box.label(text="Loop sequence:")
            col = info_box.column(align=True)
            col.label(text="1. Play animation forward")
            col.label(text=f"2. Hold last frame for {control_scene.hold_frames} frames")
            col.label(text="3. Play animation backward")
            col.label(text=f"4. Hold first frame for {control_scene.hold_frames} frames")
        
        # 