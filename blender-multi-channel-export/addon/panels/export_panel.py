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
        
        # Display version number at the top
        row = layout.row()
        box = row.box()
        box.label(text=f"Version: {context.scene.mce_addon_version}", icon='PLUGIN')
        
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
        
        # Render all section
        box = layout.box()
        box.label(text="Render", icon='RENDER_ANIMATION')
        row = box.row()
        row.operator("export.render_all", text="Render All")
        row = box.row()
        row.operator("export.advanced_render_settings", text="Advanced Settings", icon='PREFERENCES')
        
        # Selective rendering section
        box = layout.box()
        box.label(text="Selective Rendering", icon='SEQUENCE')
        row = box.row(align=True)
        row.operator("export.render_mobile", text="Mobile Only")
        row.operator("export.render_desktop", text="Desktop Only")
        
        # Scene navigation section
        box = layout.box()
        box.label(text="Scene Navigation", icon='SCENE_DATA')
        grid = box.grid_flow(row_major=True, columns=2, even_columns=True)
        
        # Add buttons for each scene
        scenes_to_show = ["ControlScene", "MobileScene", "DesktopScene", 
                         "MobileScene_Comp", "DesktopScene_Comp"]
        
        for scene_name in scenes_to_show:
            if scene_name in bpy.data.scenes:
                op = grid.operator("export.switch_to_scene", text=scene_name)
                op.scene_name = scene_name
        
        # Current project info
        box = layout.box()
        box.label(text="Project Info", icon='INFO')
        
        if bpy.data.filepath:
            blend_filename = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
            box.label(text=f"Project: {blend_filename}")
            
            # Output paths
            box.label(text="Output Videos:")
            row = box.row()
            row.label(text=f"Mobile: {blend_filename}.mp4", icon='RENDER_RESULT')
            
            row = box.row()
            row.label(text=f"Desktop: {blend_filename}.mp4", icon='RENDER_RESULT')
            
            # Add directory info
            output_dir = "//Output/"
            abs_output_dir = bpy.path.abspath(output_dir)
            box.label(text=f"Output Directory:")
            box.label(text=f"{abs_output_dir}")
        else:
            box.label(text="Save file first to see project info", icon='ERROR')