import bpy
import os
import glob
from bpy.props import StringProperty
from bpy.types import Operator

class RenderAllOperator(Operator):
    """Render all scenes and composites in sequence"""
    bl_idname = "export.render_all"
    bl_label = "Render All Scenes"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Render frames first, then render videos
        frame_scenes = [
            "MobileScene",
            "DesktopScene"
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
        
        # Get the current blend file name and output directories
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
        
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        
        # Use the default output path if not specified
        output_dir = "//Output/"
        
        # Check if frames exist
        mobile_frames_dir = output_dir + "MobileFrames/"
        desktop_frames_dir = output_dir + "DesktopFrames/"
        
        # Manually set up the composition scenes
        self.report({'INFO'}, "--- Setting up composition scenes ---")
        
        # Mobile composition setup
        mobile_pattern = bpy.path.abspath(mobile_frames_dir + blend_filename + "_*.*")
        mobile_frames = glob.glob(mobile_pattern)
        self.report({'INFO'}, f"Found {len(mobile_frames)} mobile frames")
        
        if mobile_frames and len(mobile_frames) > 0:
            # Make sure output directory exists
            mobile_out_dir = bpy.path.abspath(output_dir + "MobileOut/")
            os.makedirs(mobile_out_dir, exist_ok=True)
            
            # Set up the mobile composition scene
            self.setup_simple_composition(
                "MobileScene", 
                mobile_frames, 
                output_dir + "MobileOut/" + blend_filename + ".mp4"
            )
        
        # Desktop composition setup
        desktop_pattern = bpy.path.abspath(desktop_frames_dir + blend_filename + "_*.*")
        desktop_frames = glob.glob(desktop_pattern)
        self.report({'INFO'}, f"Found {len(desktop_frames)} desktop frames")
        
        if desktop_frames and len(desktop_frames) > 0:
            # Make sure output directory exists
            desktop_out_dir = bpy.path.abspath(output_dir + "DesktopOut/")
            os.makedirs(desktop_out_dir, exist_ok=True)
            
            # Set up the desktop composition scene
            self.setup_simple_composition(
                "DesktopScene", 
                desktop_frames, 
                output_dir + "DesktopOut/" + blend_filename + ".mp4"
            )
        
        # Force scene refresh
        bpy.context.view_layer.update()
        
        # Render the composition scenes
        self.report({'INFO'}, "--- Creating Videos ---")
        
        # Render mobile composition
        if "MobileScene_Comp" in bpy.data.scenes and len(mobile_frames) > 0:
            self.report({'INFO'}, "Rendering MobileScene_Comp...")
            context.window.scene = bpy.data.scenes["MobileScene_Comp"]
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            try:
                bpy.ops.render.render(animation=True)
                self.report({'INFO'}, "Finished rendering MobileScene_Comp")
            except Exception as e:
                self.report({'ERROR'}, f"Error rendering MobileScene_Comp: {str(e)}")
        
        # Render desktop composition
        if "DesktopScene_Comp" in bpy.data.scenes and len(desktop_frames) > 0:
            self.report({'INFO'}, "Rendering DesktopScene_Comp...")
            context.window.scene = bpy.data.scenes["DesktopScene_Comp"]
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            try:
                bpy.ops.render.render(animation=True)
                self.report({'INFO'}, "Finished rendering DesktopScene_Comp")
            except Exception as e:
                self.report({'ERROR'}, f"Error rendering DesktopScene_Comp: {str(e)}")
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        self.report({'INFO'}, "All rendering complete!")
        return {'FINISHED'}
    
    def setup_simple_composition(self, scene_name, frames, output_path):
        """Set up a simple composition scene with frames"""
        if not frames:
            self.report({'WARNING'}, f"No frames found for {scene_name}")
            return False
        
        # Create or get the composition scene
        comp_scene_name = f"{scene_name}_Comp"
        if comp_scene_name in bpy.data.scenes:
            comp_scene = bpy.data.scenes[comp_scene_name]
            self.report({'INFO'}, f"Using existing scene: {comp_scene_name}")
        else:
            comp_scene = bpy.data.scenes.new(comp_scene_name)
            self.report({'INFO'}, f"Created new scene: {comp_scene_name}")
        
        # Copy settings from source scene if it exists
        if scene_name in bpy.data.scenes:
            source_scene = bpy.data.scenes[scene_name]
            comp_scene.render.fps = source_scene.render.fps
            comp_scene.frame_start = 1
            comp_scene.frame_end = len(frames)
        else:
            comp_scene.render.fps = 30
            comp_scene.frame_start = 1
            comp_scene.frame_end = len(frames)
        
        # Set up FFMPEG output
        comp_scene.render.filepath = output_path
        comp_scene.render.image_settings.file_format = 'FFMPEG'
        comp_scene.render.ffmpeg.format = 'MPEG4'
        comp_scene.render.ffmpeg.codec = 'H264'
        comp_scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
        comp_scene.render.ffmpeg.audio_codec = 'AAC'
        
        # Set up VSE
        if not comp_scene.sequence_editor:
            comp_scene.sequence_editor_create()
        
        # Clear existing strips
        for strip in comp_scene.sequence_editor.sequences:
            comp_scene.sequence_editor.sequences.remove(strip)
        
        # Sort frames to ensure they're in order
        frames.sort()
        
        # Add the image sequence
        strips = comp_scene.sequence_editor.sequences
        first_frame = frames[0]  # Use the first frame
        
        # Create image strip
        try:
            image_strip = strips.new_image(
                name=f"{scene_name}_Sequence",
                filepath=first_frame,
                channel=1,
                frame_start=1
            )
            
            # Make it use the sequence of frames
            image_strip.use_sequence = True
            image_strip.frame_final_duration = len(frames)
            
            self.report({'INFO'}, f"Added image sequence with {len(frames)} frames")
            
            return True
        except Exception as e:
            self.report({'ERROR'}, f"Error setting up composition: {str(e)}")
            return False


class RenderMobileOnlyOperator(Operator):
    """Render only the mobile scenes"""
    bl_idname = "export.render_mobile"
    bl_label = "Render Mobile Only"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Store original scene
        original_scene = context.window.scene.name
        
        # Get the current blend file name
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
        
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        output_dir = "//Output/"
        
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
        
        # Step 2: Check for frames and set up composition
        mobile_frames_dir = output_dir + "MobileFrames/"
        mobile_pattern = bpy.path.abspath(mobile_frames_dir + blend_filename + "_*.*")
        mobile_frames = glob.glob(mobile_pattern)
        
        self.report({'INFO'}, f"Found {len(mobile_frames)} mobile frames")
        
        if mobile_frames and len(mobile_frames) > 0:
            # Make sure output directory exists
            mobile_out_dir = bpy.path.abspath(output_dir + "MobileOut/")
            os.makedirs(mobile_out_dir, exist_ok=True)
            
            # Set up the composition scene
            all_renderer = RenderAllOperator()
            all_renderer.report = self.report
            
            success = all_renderer.setup_simple_composition(
                "MobileScene",
                mobile_frames,
                output_dir + "MobileOut/" + blend_filename + ".mp4"
            )
            
            if success:
                # Step 3: Render the composition scene
                self.report({'INFO'}, "Rendering MobileScene_Comp...")
                context.window.scene = bpy.data.scenes["MobileScene_Comp"]
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                
                try:
                    bpy.ops.render.render(animation=True)
                    self.report({'INFO'}, "Finished rendering MobileScene_Comp")
                except Exception as e:
                    self.report({'ERROR'}, f"Error rendering MobileScene_Comp: {str(e)}")
        
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
        # Store original scene
        original_scene = context.window.scene.name
        
        # Get the current blend file name
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
        
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        output_dir = "//Output/"
        
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
        
        # Step 2: Check for frames and set up composition
        desktop_frames_dir = output_dir + "DesktopFrames/"
        desktop_pattern = bpy.path.abspath(desktop_frames_dir + blend_filename + "_*.*")
        desktop_frames = glob.glob(desktop_pattern)
        
        self.report({'INFO'}, f"Found {len(desktop_frames)} desktop frames")
        
        if desktop_frames and len(desktop_frames) > 0:
            # Make sure output directory exists
            desktop_out_dir = bpy.path.abspath(output_dir + "DesktopOut/")
            os.makedirs(desktop_out_dir, exist_ok=True)
            
            # Set up the composition scene
            all_renderer = RenderAllOperator()
            all_renderer.report = self.report
            
            success = all_renderer.setup_simple_composition(
                "DesktopScene",
                desktop_frames,
                output_dir + "DesktopOut/" + blend_filename + ".mp4"
            )
            
            if success:
                # Step 3: Render the composition scene
                self.report({'INFO'}, "Rendering DesktopScene_Comp...")
                context.window.scene = bpy.data.scenes["DesktopScene_Comp"]
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                
                try:
                    bpy.ops.render.render(animation=True)
                    self.report({'INFO'}, "Finished rendering DesktopScene_Comp")
                except Exception as e:
                    self.report({'ERROR'}, f"Error rendering DesktopScene_Comp: {str(e)}")
        
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