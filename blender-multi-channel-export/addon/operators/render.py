import bpy
import os
import glob
import re
import subprocess
import shutil
import tempfile
from bpy.props import StringProperty, IntProperty, FloatProperty, EnumProperty, BoolProperty
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
        
        # Get looping settings from control scene
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        loop_extend_frames = control_scene.loop_extend_frames
        hold_frames = control_scene.hold_frames
        
        # Use the source scene's FPS
        mobile_fps = bpy.data.scenes.get("MobileScene", context.scene).render.fps
        desktop_fps = bpy.data.scenes.get("DesktopScene", context.scene).render.fps
        
        # Generate videos using FFmpeg
        self.report({'INFO'}, "--- Generating Videos with FFmpeg ---")
        
        # Mobile video
        success_mobile = self.create_video_with_ffmpeg(
            frames_dir=mobile_frames_dir,
            output_file=output_dir + "MobileOut/" + blend_filename + ".mp4",
            blend_filename=blend_filename,
            fps=mobile_fps,
            loop=loop_extend_frames,
            hold_frames=hold_frames
        )
        
        # Desktop video
        success_desktop = self.create_video_with_ffmpeg(
            frames_dir=desktop_frames_dir,
            output_file=output_dir + "DesktopOut/" + blend_filename + ".mp4",
            blend_filename=blend_filename,
            fps=desktop_fps,
            loop=loop_extend_frames,
            hold_frames=hold_frames
        )
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        
        if success_mobile or success_desktop:
            self.report({'INFO'}, "All rendering complete!")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No frames were found to render!")
            return {'CANCELLED'}
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed and available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True,
                                  check=False)
            
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.report({'INFO'}, f"Found FFmpeg: {version_line}")
                return True
            else:
                self.report({'ERROR'}, "FFmpeg is not available. Please install FFmpeg.")
                return False
        except Exception as e:
            self.report({'ERROR'}, f"Error checking FFmpeg: {e}")
            return False
    
    def find_frames(self, frames_dir, blend_filename):
        """Find all frames in the directory and return sorted list"""
        # Make sure we're using the right path format for Blender
        abs_frames_dir = bpy.path.abspath(frames_dir)
        
        # Look for files matching pattern like "filename_####.ext"
        patterns = [
            os.path.join(abs_frames_dir, f"{blend_filename}_*.png"),
            os.path.join(abs_frames_dir, f"{blend_filename}_*.jpg"),
            os.path.join(abs_frames_dir, f"{blend_filename}_*.jpeg"),
            os.path.join(abs_frames_dir, f"{blend_filename}_*.exr"),
            os.path.join(abs_frames_dir, f"{blend_filename}_*.tif"),
            os.path.join(abs_frames_dir, f"{blend_filename}_*.tiff")
        ]
        
        all_frames = []
        for pattern in patterns:
            self.report({'INFO'}, f"Looking for frames with pattern: {pattern}")
            frames = glob.glob(pattern)
            all_frames.extend(frames)
        
        if not all_frames:
            self.report({'WARNING'}, f"No frames found in {abs_frames_dir}")
            return []
        
        # Sort frames to ensure correct order
        # We need to sort numerically by the frame number
        def get_frame_number(filepath):
            # Extract frame number from filename like "name_001.ext"
            basename = os.path.basename(filepath)
            match = re.search(r'_(\d+)\.', basename)
            if match:
                return int(match.group(1))
            return 0
        
        all_frames.sort(key=get_frame_number)
        
        # Log some frames for debugging
        if len(all_frames) > 0:
            self.report({'INFO'}, f"Found {len(all_frames)} frames in total")
            self.report({'INFO'}, f"First frame: {all_frames[0]}")
            if len(all_frames) > 1:
                self.report({'INFO'}, f"Second frame: {all_frames[1]}")
            self.report({'INFO'}, f"Last frame: {all_frames[-1]}")
        
        return all_frames
    
    def prepare_frames_for_ffmpeg(self, frames, temp_dir, loop=False, hold_frames=15):
        """Copy and organize frames for FFmpeg to process including loops and holds"""
        frame_count = len(frames)
        if frame_count == 0:
            return 0
            
        self.report({'INFO'}, f"Preparing {frame_count} frames in {temp_dir}")
        
        # Get file extension from the first frame
        _, ext = os.path.splitext(frames[0])
        
        # For simple forward animation (no loop)
        if not loop or frame_count <= 1:
            # Copy all frames with sequential numbering for ffmpeg
            for i, frame_path in enumerate(frames):
                new_name = f"frame_{i+1:04d}{ext}"
                shutil.copy2(frame_path, os.path.join(temp_dir, new_name))
            return frame_count
        
        # For loop animation (forward + hold + reverse + hold)
        total_frames = 0
        
        # 1. Forward animation
        for i, frame_path in enumerate(frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(frame_path, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        # 2. Hold last frame
        last_frame = frames[-1]
        for i in range(hold_frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(last_frame, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        # 3. Reverse animation
        for frame_path in reversed(frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(frame_path, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        # 4. Hold first frame
        first_frame = frames[0]
        for i in range(hold_frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(first_frame, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        self.report({'INFO'}, f"Prepared total of {total_frames} frames for FFmpeg")
        return total_frames
    
    def create_video_with_ffmpeg(self, frames_dir, output_file, blend_filename, fps=30, 
                               loop=False, hold_frames=15, quality="high", crf=23):
        """Use FFmpeg to create video from frames"""
        # Check if FFmpeg is available
        if not self.check_ffmpeg():
            self.report({'ERROR'}, "FFmpeg is required but not found. Please install FFmpeg.")
            return False
        
        # Find frames
        frames = self.find_frames(frames_dir, blend_filename)
        if not frames or len(frames) == 0:
            self.report({'WARNING'}, f"No frames found in {frames_dir}")
            return False
        
        # Create temporary directory for frame processing
        with tempfile.TemporaryDirectory() as temp_dir:
            self.report({'INFO'}, f"Created temporary directory: {temp_dir}")
            
            # Prepare frames (copy/rename for FFmpeg and handle looping)
            total_frames = self.prepare_frames_for_ffmpeg(
                frames, 
                temp_dir, 
                loop=loop, 
                hold_frames=hold_frames
            )
            
            if total_frames == 0:
                self.report({'ERROR'}, "No frames were prepared for FFmpeg")
                return False
            
            # Determine quality settings
            if quality == "high":
                video_codec = "libx264"
                crf_value = "18"
                pixel_format = "yuv420p"
                preset = "slow"
            elif quality == "medium":
                video_codec = "libx264"
                crf_value = "23"
                pixel_format = "yuv420p"
                preset = "medium"
            else:  # low
                video_codec = "libx264"
                crf_value = "28"
                pixel_format = "yuv420p"
                preset = "fast"
            
            # Make sure output directory exists
            abs_output_file = bpy.path.abspath(output_file)
            os.makedirs(os.path.dirname(abs_output_file), exist_ok=True)
            
            # Build FFmpeg command with extensive options
            cmd = [
                'ffmpeg', '-y',  # Overwrite output file if it exists
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, 'frame_%04d' + os.path.splitext(frames[0])[1]),
                '-c:v', video_codec,
                '-preset', preset,
                '-crf', crf_value,
                '-pix_fmt', pixel_format,
                # Add additional FFmpeg options for high quality
                '-profile:v', 'high',
                '-level', '4.2',
                '-movflags', '+faststart',  # Optimize for web streaming
                abs_output_file
            ]
            
            # Execute FFmpeg command
            self.report({'INFO'}, f"Running FFmpeg command: {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    self.report({'INFO'}, f"FFmpeg successfully created video: {output_file}")
                    return True
                else:
                    self.report({'ERROR'}, f"FFmpeg error: {result.stderr}")
                    return False
            except Exception as e:
                self.report({'ERROR'}, f"Error running FFmpeg: {str(e)}")
                return False


class RenderMobileOnlyOperator(Operator):
    """Render only the mobile scenes"""
    bl_idname = "export.render_mobile"
    bl_label = "Render Mobile Only"
    bl_options = {'REGISTER'}
    
    # Add additional FFmpeg options
    quality: EnumProperty(
        name="Quality",
        description="Video quality",
        items=[
            ('high', "High", "High quality (larger file)"),
            ('medium', "Medium", "Medium quality (balanced)"),
            ('low', "Low", "Low quality (smaller file)")
        ],
        default='high'
    )
    
    custom_fps: IntProperty(
        name="Frame Rate",
        description="Custom frame rate for the video (0 = use scene settings)",
        min=0, max=120,
        default=0
    )
    
    custom_crf: IntProperty(
        name="CRF Value",
        description="Constant Rate Factor (lower = higher quality, higher = smaller file)",
        min=0, max=51,
        default=23
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "quality")
        layout.prop(self, "custom_fps")
        layout.prop(self, "custom_crf")
    
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
        
        # Step 2: Create video from the frames
        # Get looping settings from control scene
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        loop_extend_frames = control_scene.loop_extend_frames
        hold_frames = control_scene.hold_frames
        
        # Determine FPS
        fps = self.custom_fps
        if fps == 0:
            # Use scene FPS
            fps = bpy.data.scenes.get(scene_name, context.scene).render.fps
        
        # Use the all renderer to create video
        all_renderer = RenderAllOperator()
        all_renderer.report = self.report
        
        success = all_renderer.create_video_with_ffmpeg(
            frames_dir=output_dir + "MobileFrames/",
            output_file=output_dir + "MobileOut/" + blend_filename + ".mp4",
            blend_filename=blend_filename,
            fps=fps,
            loop=loop_extend_frames,
            hold_frames=hold_frames,
            quality=self.quality,
            crf=self.custom_crf
        )
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        
        if success:
            self.report({'INFO'}, "Mobile rendering complete!")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Mobile rendering encountered issues")
            return {'CANCELLED'}


class RenderDesktopOnlyOperator(Operator):
    """Render only the desktop scenes"""
    bl_idname = "export.render_desktop"
    bl_label = "Render Desktop Only"
    bl_options = {'REGISTER'}
    
    # Add additional FFmpeg options
    quality: EnumProperty(
        name="Quality",
        description="Video quality",
        items=[
            ('high', "High", "High quality (larger file)"),
            ('medium', "Medium", "Medium quality (balanced)"),
            ('low', "Low", "Low quality (smaller file)")
        ],
        default='high'
    )
    
    custom_fps: IntProperty(
        name="Frame Rate",
        description="Custom frame rate for the video (0 = use scene settings)",
        min=0, max=120,
        default=0
    )
    
    custom_crf: IntProperty(
        name="CRF Value",
        description="Constant Rate Factor (lower = higher quality, higher = smaller file)",
        min=0, max=51,
        default=23
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "quality")
        layout.prop(self, "custom_fps")
        layout.prop(self, "custom_crf")
    
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
        
        # Step 2: Create video from the frames
        # Get looping settings from control scene
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        loop_extend_frames = control_scene.loop_extend_frames
        hold_frames = control_scene.hold_frames
        
        # Determine FPS
        fps = self.custom_fps
        if fps == 0:
            # Use scene FPS
            fps = bpy.data.scenes.get(scene_name, context.scene).render.fps
        
        # Use the all renderer to create video
        all_renderer = RenderAllOperator()
        all_renderer.report = self.report
        
        success = all_renderer.create_video_with_ffmpeg(
            frames_dir=output_dir + "DesktopFrames/",
            output_file=output_dir + "DesktopOut/" + blend_filename + ".mp4",
            blend_filename=blend_filename,
            fps=fps,
            loop=loop_extend_frames,
            hold_frames=hold_frames,
            quality=self.quality,
            crf=self.custom_crf
        )
        
        # Return to original scene
        context.window.scene = bpy.data.scenes[original_scene]
        
        if success:
            self.report({'INFO'}, "Desktop rendering complete!")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Desktop rendering encountered issues")
            return {'CANCELLED'}


class AdvancedRenderSettingsOperator(Operator):
    """Configure advanced render settings"""
    bl_idname = "export.advanced_render_settings"
    bl_label = "Advanced Render Settings"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Video quality settings
    video_codec: EnumProperty(
        name="Video Codec",
        description="Video codec to use",
        items=[
            ('libx264', "H.264", "Standard H.264 codec"),
            ('libx265', "H.265/HEVC", "More efficient but slower encoding"),
            ('libvpx-vp9', "VP9", "Open format with good compression"),
        ],
        default='libx264'
    )
    
    preset: EnumProperty(
        name="Encoding Preset",
        description="Encoding speed/quality tradeoff",
        items=[
            ('ultrafast', "Ultrafast", "Fastest encoding, largest file size"),
            ('superfast', "Superfast", "Very fast encoding"),
            ('veryfast', "Veryfast", "Fast encoding"),
            ('faster', "Faster", "Fairly fast encoding"),
            ('fast', "Fast", "Moderate encoding speed"),
            ('medium', "Medium", "Balanced encoding (default)"),
            ('slow', "Slow", "Slow encoding with good quality"),
            ('slower', "Slower", "Very slow encoding with better quality"),
            ('veryslow', "Veryslow", "Extremely slow encoding with best quality")
        ],
        default='medium'
    )
    
    crf: IntProperty(
        name="CRF Value",
        description="Constant Rate Factor (lower = higher quality, higher = smaller file)",
        min=0, max=51,
        default=23
    )
    
    # Loop settings
    create_loop: BoolProperty(
        name="Create Loop Animation",
        description="Create a looping animation",
        default=True
    )
    
    forward_hold_frames: IntProperty(
        name="Hold Last Frame",
        description="Number of frames to hold the last frame before reversing",
        min=0, max=120,
        default=15
    )
    
    reverse_hold_frames: IntProperty(
        name="Hold First Frame",
        description="Number of frames to hold the first frame after reversing",
        min=0, max=120,
        default=15
    )
    
    # Output options
    output_format: EnumProperty(
        name="Output Format",
        description="Video output format",
        items=[
            ('mp4', "MP4", "Standard MP4 container"),
            ('webm', "WebM", "WebM format for web use"),
            ('mov', "MOV", "QuickTime format")
        ],
        default='mp4'
    )
    
    fps: IntProperty(
        name="Frame Rate",
        description="Frames per second for the output video",
        min=1, max=120,
        default=30
    )
    
    pixel_format: EnumProperty(
        name="Pixel Format",
        description="Pixel format for video encoding",
        items=[
            ('yuv420p', "YUV 420P", "Standard format for wide compatibility"),
            ('yuv422p', "YUV 422P", "Better quality, less compression"),
            ('yuv444p', "YUV 444P", "Best quality, least compression")
        ],
        default='yuv420p'
    )
    
    def invoke(self, context, event):
        # Initialize with current scene settings
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        self.create_loop = control_scene.loop_extend_frames
        self.forward_hold_frames = control_scene.hold_frames
        self.reverse_hold_frames = control_scene.hold_frames
        
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def draw(self, context):
        layout = self.layout
        
        # Video quality settings
        box = layout.box()
        box.label(text="Video Quality", icon='RENDER_STILL')
        box.prop(self, "video_codec")
        box.prop(self, "preset")
        box.prop(self, "crf")
        box.prop(self, "pixel_format")
        
        # Loop settings
        box = layout.box()
        box.label(text="Loop Settings", icon='LOOP_FORWARDS')
        box.prop(self, "create_loop")
        
        # Only enable hold frames if looping is enabled
        sub = box.column()
        sub.enabled = self.create_loop
        sub.prop(self, "forward_hold_frames")
        sub.prop(self, "reverse_hold_frames")
        
        # Output options
        box = layout.box()
        box.label(text="Output Options", icon='OUTPUT')
        box.prop(self, "output_format")
        box.prop(self, "fps")
    
    def execute(self, context):
        # Save settings to scene properties
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        if control_scene:
            control_scene.loop_extend_frames = self.create_loop
            control_scene.hold_frames = self.forward_hold_frames
            
            # Add custom properties for additional settings
            if not hasattr(control_scene, "ffmpeg_video_codec"):
                control_scene['ffmpeg_video_codec'] = self.video_codec
                control_scene['ffmpeg_preset'] = self.preset
                control_scene['ffmpeg_crf'] = self.crf
                control_scene['ffmpeg_pixel_format'] = self.pixel_format
                control_scene['ffmpeg_output_format'] = self.output_format
                control_scene['ffmpeg_fps'] = self.fps
                control_scene['ffmpeg_reverse_hold_frames'] = self.reverse_hold_frames
            else:
                control_scene['ffmpeg_video_codec'] = self.video_codec
                control_scene['ffmpeg_preset'] = self.preset
                control_scene['ffmpeg_crf'] = self.crf
                control_scene['ffmpeg_pixel_format'] = self.pixel_format
                control_scene['ffmpeg_output_format'] = self.output_format
                control_scene['ffmpeg_fps'] = self.fps
                control_scene['ffmpeg_reverse_hold_frames'] = self.reverse_hold_frames
        
        self.report({'INFO'}, "Advanced render settings saved")
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