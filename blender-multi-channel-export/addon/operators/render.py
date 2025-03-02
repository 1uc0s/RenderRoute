import bpy
import os
import glob
from bpy.props import StringProperty
from bpy.types import Operator

# Import the setup_compositor function from setup.py
# We'll reuse the function that creates the compositor
from .setup import MultiChannelExportPipelineSetup

class RenderAllOperator(Operator):
    """Render all scenes and composites in sequence"""
    bl_idname = "export.render_all"
    bl_label = "Render All Scenes"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Render frames first, then refresh compositors, then render videos
        frame_scenes = [
            "MobileScene",
            "DesktopScene"
        ]
        
        composite_scenes = [
            "MobileScene_Comp",
            "DesktopScene_Comp"
        ]
        
        # Store original scene
        original_scene = context.window.scene.name
        
        # First render all the frame scenes
        self.report({'INFO'}, "--- Rendering Frames ---")
        for scene_name in frame_scenes:
            if scene_name in bpy.data.scenes:
                self.report({'INFO'}, f"Rendering {scene_name}...")
                
                # Switch to the scene
                context.window.scene = bpy.data.scenes[scene_name]
                
                # Force screen update
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                
                # Render animation for this scene
                bpy.ops.render.render(animation=True)
                
                self.report({'INFO'}, f"Finished rendering {scene_name}")
            else:
                self.report({'WARNING'}, f"Scene {scene_name} not found!")
        
        # Now recreate the compositor scenes to make sure they find the frames
        self.report({'INFO'}, "--- Refreshing compositors ---")
        
        # Get the current blend file name and output directories
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
            
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        
        # Get output directory from scene settings
        # Using the ControlScene as reference for settings
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        loop_extend_frames = control_scene.loop_extend_frames
        hold_frames = control_scene.hold_frames
        
        # Use the default output path if not specified
        output_dir = "//Output/"
        
        # Check if frames exist
        mobile_frames_dir = output_dir + "MobileFrames/"
        desktop_frames_dir = output_dir + "DesktopFrames/"
        
        # Manually verify frame existence and report
        mobile_pattern = bpy.path.abspath(mobile_frames_dir + blend_filename + "_*.*")
        desktop_pattern = bpy.path.abspath(desktop_frames_dir + blend_filename + "_*.*")
        
        mobile_frames = glob.glob(mobile_pattern)
        desktop_frames = glob.glob(desktop_pattern)
        
        self.report({'INFO'}, f"Found {len(mobile_frames)} mobile frames")
        self.report({'INFO'}, f"Found {len(desktop_frames)} desktop frames")
        
        # If we have frames, recreate the compositor scenes to ensure they pick up the frames
        if mobile_frames:
            self.report({'INFO'}, "Refreshing MobileScene_Comp")
            # Get active operator
            setup_op = MultiChannelExportPipelineSetup
            # Call setup_compositor function to rebuild the compositor with the right frames
            setup_op.setup_compositor(
                setup_op,
                "MobileScene", 
                mobile_frames_dir, 
                output_dir + "MobileOut/",
                is_mobile=True
            )
        
        if desktop_frames:
            self.report({'INFO'}, "Refreshing DesktopScene_Comp")
            # Get active operator
            setup_op = MultiChannelExportPipelineSetup
            # Call setup_compositor function to rebuild the compositor with the right frames
            setup_op.setup_compositor(
                setup_op,
                "DesktopScene", 
                desktop_frames_dir, 
                output_dir + "DesktopOut/",
                is_mobile=False
            )
        
        # Force scene refresh
        bpy.context.view_layer.update()
        
        # Then render all the composite scenes
        self.report({'INFO'}, "--- Creating Videos ---")
        for scene_name in composite_scenes:
            if scene_name in bpy.data.scenes:
                self.report({'INFO'}, f"Rendering {scene_name}...")
                
                # Switch to the scene
                context.window.scene = bpy.data.scenes[scene_name]
                
                # Force screen update
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                
                # Render animation for this scene
                bpy.ops.render.render(animation=True)
                
                self.report({'INFO'}, f"Finished rendering {scene_name}")
            else:
                self.report({'WARNING'}, f"Scene {scene_name} not found!")
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        self.report({'INFO'}, "All rendering complete!")
        return {'FINISHED'}


class RenderMobileOnlyOperator(Operator):
    """Render only the mobile scenes"""
    bl_idname = "export.render_mobile"
    bl_label = "Render Mobile Only"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # First render frames, then refresh compositor, then render video
        
        # Store original scene
        original_scene = context.window.scene.name
        
        # Step 1: Render the main scene
        scene_name = "MobileScene"
        if scene_name in bpy.data.scenes:
            self.report({'INFO'}, f"Rendering {scene_name}...")
            
            # Switch to the scene
            context.window.scene = bpy.data.scenes[scene_name]
            
            # Force screen update
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # Render animation for this scene
            bpy.ops.render.render(animation=True)
            
            self.report({'INFO'}, f"Finished rendering {scene_name}")
        else:
            self.report({'WARNING'}, f"Scene {scene_name} not found!")
        
        # Step 2: Refresh the compositor scene
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
            
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        output_dir = "//Output/"
        mobile_frames_dir = output_dir + "MobileFrames/"
        
        # Manually verify frame existence and report
        mobile_pattern = bpy.path.abspath(mobile_frames_dir + blend_filename + "_*.*")
        mobile_frames = glob.glob(mobile_pattern)
        self.report({'INFO'}, f"Found {len(mobile_frames)} mobile frames")
        
        # If we have frames, refresh the compositor scene
        if mobile_frames:
            self.report({'INFO'}, "Refreshing MobileScene_Comp")
            # Get active operator
            setup_op = MultiChannelExportPipelineSetup
            # Call setup_compositor function to rebuild the compositor with the right frames
            setup_op.setup_compositor(
                setup_op,
                "MobileScene", 
                mobile_frames_dir, 
                output_dir + "MobileOut/",
                is_mobile=True
            )
        
        # Force scene refresh
        bpy.context.view_layer.update()
        
        # Step 3: Render the compositor scene
        comp_scene_name = "MobileScene_Comp"
        if comp_scene_name in bpy.data.scenes:
            self.report({'INFO'}, f"Rendering {comp_scene_name}...")
            
            # Switch to the scene
            context.window.scene = bpy.data.scenes[comp_scene_name]
            
            # Force screen update
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # Render animation for this scene
            bpy.ops.render.render(animation=True)
            
            self.report({'INFO'}, f"Finished rendering {comp_scene_name}")
        else:
            self.report({'WARNING'}, f"Scene {comp_scene_name} not found!")
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        self.report({'INFO'}, "Mobile rendering complete!")
        return {'FINISHED'}


class RenderDesktopOnlyOperator(Operator):
    """Render only the desktop scenes"""
    bl_idname = "export.render_desktop"
    bl_label = "Render Desktop Only"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # First render frames, then refresh compositor, then render video
        
        # Store original scene
        original_scene = context.window.scene.name
        
        # Step 1: Render the main scene
        scene_name = "DesktopScene"
        if scene_name in bpy.data.scenes:
            self.report({'INFO'}, f"Rendering {scene_name}...")
            
            # Switch to the scene
            context.window.scene = bpy.data.scenes[scene_name]
            
            # Force screen update
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # Render animation for this scene
            bpy.ops.render.render(animation=True)
            
            self.report({'INFO'}, f"Finished rendering {scene_name}")
        else:
            self.report({'WARNING'}, f"Scene {scene_name} not found!")
        
        # Step 2: Refresh the compositor scene
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
            
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        output_dir = "//Output/"
        desktop_frames_dir = output_dir + "DesktopFrames/"
        
        # Manually verify frame existence and report
        desktop_pattern = bpy.path.abspath(desktop_frames_dir + blend_filename + "_*.*")
        desktop_frames = glob.glob(desktop_pattern)
        self.report({'INFO'}, f"Found {len(desktop_frames)} desktop frames")
        
        # If we have frames, refresh the compositor scene
        if desktop_frames:
            self.report({'INFO'}, "Refreshing DesktopScene_Comp")
            # Get active operator
            setup_op = MultiChannelExportPipelineSetup
            # Call setup_compositor function to rebuild the compositor with the right frames
            setup_op.setup_compositor(
                setup_op,
                "DesktopScene", 
                desktop_frames_dir, 
                output_dir + "DesktopOut/",
                is_mobile=False
            )
        
        # Force scene refresh
        bpy.context.view_layer.update()
        
        # Step 3: Render the compositor scene
        comp_scene_name = "DesktopScene_Comp"
        if comp_scene_name in bpy.data.scenes:
            self.report({'INFO'}, f"Rendering {comp_scene_name}...")
            
            # Switch to the scene
            context.window.scene = bpy.data.scenes[comp_scene_name]
            
            # Force screen update
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # Render animation for this scene
            bpy.ops.render.render(animation=True)
            
            self.report({'INFO'}, f"Finished rendering {comp_scene_name}")
        else:
            self.report({'WARNING'}, f"Scene {comp_scene_name} not found!")
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        self.report({'INFO'}, "Desktop rendering complete!")
        return {'FINISHED'}


class SwitchToSceneOperator(Operator):
    """Switch to the specified scene"""
    bl_idname = "export.switch_to_scene"
    bl_label = "Switch To Scene"
    bl_options = {'REGISTER'}
    
    scene_name: StringProperty(
        name="Scene Name",
        description="Name of the scene to switch to",
        default=""
    )
    
    def execute(self, context):
        if self.scene_name in bpy.data.scenes:
            context.window.scene = bpy.data.scenes[self.scene_name]
            self.report({'INFO'}, f"Switched to {self.scene_name}")
        else:
            self.report({'ERROR'}, f"Scene {self.scene_name} not found!")
        return {'FINISHED'}