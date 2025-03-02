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
        
        # Render all section
        box = layout.box()
        box.label(text="Render", icon='RENDER_ANIMATION')
        row = box.row()
        row.operator("export.render_all", text="Render All")
        
        # Selective rendering section
        box = layout.box()
        box.label(text="Selective Rendering", icon='SEQUENCE')
        row = box.row(align=True)
        row.operator("export.render_mobile", text="Mobile Only")
        row.operator("export.render_desktop", text="Desktop Only")
        
        # Current project info
        box = layout.box()
        box.label(text="Project Info", icon='INFO')
        
        if bpy.data.filepath:
            blend_filename = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            box.label(text=f"Project: {blend_filename}")
            
            # Output paths
            box.label(text="Output Videos:")
            box.label(text=f"  Mobile: {blend_filename}.mp4", icon='RENDER_RESULT')
            box.label(text=f"  Desktop: {blend_filename}.mp4", icon='RENDER_RESULT')
        else:
            box.label(text="Save file first to see project info", icon='ERROR')