import bpy
import os
import glob
from bpy.props import BoolProperty, StringProperty, IntProperty
from bpy.types import Operator

class MultiChannelExportPipelineSetup(Operator):
    """Setup the multi-channel export pipeline"""
    bl_idname = "export.setup_pipeline"
    bl_label = "Setup Export Pipeline"
    bl_options = {'REGISTER', 'UNDO'}
    
    use_scene_settings: BoolProperty(
        name="Use Existing Scene Settings",
        description="If True, preserves each scene's existing render settings",
        default=False,
    )
    
    base_output_dir: StringProperty(
        name="Output Directory",
        description="Base directory for output files (relative to blend file)",
        default="//Output/",
        subtype='DIR_PATH',
    )
    
    loop_extend_frames: BoolProperty(
        name="Create Loop Animation",
        description="Create a loop by playing forwards, holding last frame, playing backwards, and holding first frame",
        default=False,
    )
    
    hold_frames: IntProperty(
        name="Hold Frames",
        description="Number of frames to hold at the end and beginning for looping",
        default=15,
        min=1,
        max=120,
    )
    
    def setup_compositor(self, scene_name, input_dir, output_dir, is_mobile=True):
        """Set up VSE for compositing frames to video - can be called from other operators"""
        # Get the current blend file name without extension
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return False
            
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        
        # Create a new scene for compositing
        comp_scene_name = scene_name + "_Comp"
        if comp_scene_name in bpy.data.scenes:
            comp_scene = bpy.data.scenes[comp_scene_name]
        else:
            comp_scene = bpy.data.scenes.new(comp_scene_name)
        
        # Setup the scene for video output
        if scene_name in bpy.data.scenes:
            # Copy frame rate and range from source scene
            source_scene = bpy.data.scenes[scene_name]
            comp_scene.render.fps = source_scene.render.fps
            comp_scene.frame_start = source_scene.frame_start
            comp_scene.frame_end = source_scene.frame_end
        else:
            # Default values if source scene doesn't exist
            comp_scene.render.fps = 30
            comp_scene.frame_start = 1
            comp_scene.frame_end = 250
        
        # Set the output path for the video (relative to blend file)
        output_path = output_dir + blend_filename
        comp_scene.render.filepath = output_path
        
        # Set output to FFMPEG video with MPEG-4
        comp_scene.render.image_settings.file_format = 'FFMPEG'
        comp_scene.render.ffmpeg.format = 'MPEG4'
        comp_scene.render.ffmpeg.codec = 'H264'
        
        # Set encoding settings
        comp_scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
        comp_scene.render.ffmpeg.audio_codec = 'AAC'
        comp_scene.render.ffmpeg.gopsize = 18  # Keyframe interval
        comp_scene.render.ffmpeg.video_bitrate = 6000  # Bitrate in kb/s
        comp_scene.render.ffmpeg.maxrate = 9000
        comp_scene.render.ffmpeg.minrate = 0
        comp_scene.render.ffmpeg.buffersize = 1800
        
        # Set up the VSE
        if not comp_scene.sequence_editor:
            comp_scene.sequence_editor_create()
        
        # Clear existing strips
        for strip in comp_scene.sequence_editor.sequences:
            comp_scene.sequence_editor.sequences.remove(strip)
        
        # Add image sequence
        frame_path = input_dir + blend_filename + "_"
        strips = comp_scene.sequence_editor.sequences
        
        # Get the full path to check for existing frames
        frame_pattern = bpy.path.abspath(frame_path + "*.*")
        frames = glob.glob(frame_pattern)
        
        # Print debug info
        print(f"Looking for frames at: {frame_pattern}")
        print(f"Found {len(frames)} frames")
        
        if frames:
            # Sort the frames to ensure correct order
            frames.sort()
            # Find the first frame
            first_frame = frames[0]
            last_frame = frames[-1]
            num_frames = len(frames)
            
            # Calculate new scene end frame for looping if enabled
            loop_extend_frames = bpy.context.scene.loop_extend_frames
            hold_frames = bpy.context.scene.hold_frames
            
            if loop_extend_frames:
                # Forward + hold + reverse + hold
                new_end_frame = (num_frames * 2) + (hold_frames * 2)
                comp_scene.frame_end = new_end_frame
            
            # Create the forward image strip
            forward_strip = strips.new_image(
                name=f"{scene_name}_Forward",
                filepath=first_frame,
                channel=1,
                frame_start=1
            )
            
            # Set the frame duration
            forward_strip.frame_final_duration = num_frames
            
            # If looping is enabled, create the additional parts of the loop
            if loop_extend_frames and num_frames > 1:
                # 1. Hold the last frame
                last_frame_strip = strips.new_image(
                    name=f"{scene_name}_HoldLast",
                    filepath=last_frame,
                    channel=1,
                    frame_start=num_frames + 1
                )
                last_frame_strip.frame_final_duration = hold_frames
                
                # 2. Add reversed sequence
                reverse_strip = strips.new_image(
                    name=f"{scene_name}_Reverse",
                    filepath=last_frame,  # Start with last frame
                    channel=1,
                    frame_start=num_frames + hold_frames + 1
                )
                reverse_strip.frame_final_duration = num_frames
                
                # Now create the reverse sequence
                if hasattr(reverse_strip, "elements"):
                    # Clear existing elements
                    while len(reverse_strip.elements) > 0:
                        reverse_strip.elements.pop()
                    
                    # Add frames in reverse order
                    for i, frame_path in enumerate(reversed(frames)):
                        element = reverse_strip.elements.append(frame_path)
                
                # 3. Hold the first frame
                first_frame_strip = strips.new_image(
                    name=f"{scene_name}_HoldFirst",
                    filepath=first_frame,
                    channel=1,
                    frame_start=num_frames * 2 + hold_frames + 1
                )
                first_frame_strip.frame_final_duration = hold_frames
            
            self.report({'INFO'}, f"Added {num_frames} frames to {comp_scene_name}")
            
            # If looping, update info
            if loop_extend_frames:
                self.report({'INFO'}, f"Created loop animation with {hold_frames} hold frames")
            
            return True
        else:
            self.report({'WARNING'}, f"No frames found at {frame_pattern}. You'll need to render before compositing.")
            
            # Create a text strip with warning message
            text_strip = strips.new_effect(
                name="Warning",
                type='TEXT',
                channel=1,
                frame_start=1,
                frame_end=comp_scene.frame_end
            )
            
            # Set the text directly as a string
            if hasattr(text_strip, "text"):
                text_strip.text = "No frames found - render the scene first"
                # Set text properties for better visibility
                if hasattr(text_strip, "font_size"):
                    text_strip.font_size = 48
                if hasattr(text_strip, "color"):
                    text_strip.color = (1.0, 0.3, 0.3, 1.0)  # Red text
            
            return False
    
    def execute(self, context):
        # Get the current blend file name without extension
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "Please save your file first")
            return {'CANCELLED'}
            
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        
        # Store the loop settings in the scene properties for later reference
        context.scene.loop_extend_frames = self.loop_extend_frames
        context.scene.hold_frames = self.hold_frames
        
        # Create the directory structure if it doesn't exist
        directories = [
            self.base_output_dir + "MobileFrames/",
            self.base_output_dir + "MobileOut/",
            self.base_output_dir + "DesktopFrames/",
            self.base_output_dir + "DesktopOut/"
        ]
        
        for dir_path in directories:
            abs_path = bpy.path.abspath(dir_path)
            if not os.path.exists(abs_path):
                os.makedirs(abs_path)
                self.report({'INFO'}, f"Created directory: {abs_path}")
        
        # Function to set up rendering settings for a scene
        def setup_scene_rendering(scene, is_mobile=True):
            # Set the output path for frames (relative to blend file)
            if is_mobile:
                scene.render.filepath = self.base_output_dir + "MobileFrames/" + blend_filename + "_"
            else:
                scene.render.filepath = self.base_output_dir + "DesktopFrames/" + blend_filename + "_"
            
            # Set frame naming format
            scene.render.use_file_extension = True
            scene.render.use_overwrite = True
            scene.render.use_placeholder = True
            
            # Only modify render settings if we're not using existing scene settings
            if not self.use_scene_settings:
                # Set output to EXR frames
                scene.render.image_settings.file_format = 'OPEN_EXR'
                scene.render.image_settings.color_depth = '32'  # Full float precision
                scene.render.image_settings.exr_codec = 'ZIP'  # Compression method
        
        # Setup workflow for mobile version
        mobile_scene_name = "MobileScene"
        if mobile_scene_name not in bpy.data.scenes:
            mobile_scene = bpy.data.scenes.new(mobile_scene_name)
            self.report({'INFO'}, f"Created new scene: {mobile_scene_name}")
        else:
            mobile_scene = bpy.data.scenes[mobile_scene_name]
            self.report({'INFO'}, f"Using existing scene: {mobile_scene_name}")
        
        setup_scene_rendering(mobile_scene, is_mobile=True)
        self.setup_compositor(
            mobile_scene_name,
            self.base_output_dir + "MobileFrames/",
            self.base_output_dir + "MobileOut/",
            is_mobile=True
        )
        
        # Setup workflow for desktop version
        desktop_scene_name = "DesktopScene"
        if desktop_scene_name not in bpy.data.scenes:
            desktop_scene = bpy.data.scenes.new(desktop_scene_name)
            self.report({'INFO'}, f"Created new scene: {desktop_scene_name}")
        else:
            desktop_scene = bpy.data.scenes[desktop_scene_name]
            self.report({'INFO'}, f"Using existing scene: {desktop_scene_name}")
        
        setup_scene_rendering(desktop_scene, is_mobile=False)
        self.setup_compositor(
            desktop_scene_name,
            self.base_output_dir + "DesktopFrames/",
            self.base_output_dir + "DesktopOut/",
            is_mobile=False
        )
        
        # Create or update the Control scene
        control_scene_name = "ControlScene"
        if control_scene_name not in bpy.data.scenes:
            control_scene = bpy.data.scenes.new(control_scene_name)
            self.report({'INFO'}, f"Created new scene: {control_scene_name}")
        else:
            control_scene = bpy.data.scenes[control_scene_name]
            self.report({'INFO'}, f"Using existing scene: {control_scene_name}")
        
        # Set the control scene as the active scene
        context.window.scene = bpy.data.scenes[control_scene_name]
        
        self.report({'INFO'}, "Pipeline setup complete!")
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Output Settings")
        box.prop(self, "base_output_dir")
        box.prop(self, "use_scene_settings")
        
        box = layout.box()
        box.label(text="Loop Animation")
        row = box.row()
        row.prop(self, "loop_extend_frames")
        sub = box.row()
        sub.enabled = self.loop_extend_frames
        sub.prop(self, "hold_frames")