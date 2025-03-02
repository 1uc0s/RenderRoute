import bpy
import os
import sys
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
        # Enhanced debugging
        self.report({'INFO'}, f"🏁 Starting multi-channel export render process")
        self.report({'INFO'}, f"📄 Current Blender version: {bpy.app.version_string}")
        
        # Get the current blend file name and path
        blend_filepath = bpy.data.filepath
        if not blend_filepath:
            self.report({'ERROR'}, "❌ Please save your file first")
            return {'CANCELLED'}
        
        blend_dir = os.path.dirname(blend_filepath)
        blend_filename = os.path.splitext(os.path.basename(blend_filepath))[0]
        self.report({'INFO'}, f"📄 Blend file: {blend_filepath}")
        self.report({'INFO'}, f"📁 Working directory: {blend_dir}")
        
        # Render frames first, then render videos
        frame_scenes = [
            "MobileScene",
            "DesktopScene"
        ]
        
        # Store original scene
        original_scene = context.window.scene.name
        self.report({'INFO'}, f"🔄 Original scene: {original_scene}")
        
        # First render all the frame scenes
        self.report({'INFO'}, "🎬 --- Rendering Frames ---")
        for scene_name in frame_scenes:
            if scene_name in bpy.data.scenes:
                scene = bpy.data.scenes[scene_name]
                self.report({'INFO'}, f"🎬 Preparing to render {scene_name}")
                self.report({'INFO'}, f"🔄 Output path: {scene.render.filepath}")
                self.report({'INFO'}, f"🔄 Absolute output path: {bpy.path.abspath(scene.render.filepath)}")
                self.report({'INFO'}, f"🔄 Format: {scene.render.image_settings.file_format}")
                
                # Check if output directory exists
                output_dir = os.path.dirname(bpy.path.abspath(scene.render.filepath))
                if not os.path.exists(output_dir):
                    self.report({'WARNING'}, f"⚠️ Output directory doesn't exist, creating: {output_dir}")
                    os.makedirs(output_dir, exist_ok=True)
                
                # Switch to the scene
                context.window.scene = bpy.data.scenes[scene_name]
                self.report({'INFO'}, f"🔄 Switched to scene: {context.window.scene.name}")
                
                # Force screen update
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
                
                # Render animation for this scene
                self.report({'INFO'}, f"🎬 Starting render for {scene_name}...")
                bpy.ops.render.render(animation=True)
                
                self.report({'INFO'}, f"✅ Finished rendering {scene_name}")
            else:
                self.report({'WARNING'}, f"⚠️ Scene {scene_name} not found!")
        
        # Use the default output path if not specified
        output_dir = "//Output/"
        self.report({'INFO'}, f"📁 Using output directory: {output_dir}")
        self.report({'INFO'}, f"📁 Absolute output path: {bpy.path.abspath(output_dir)}")
        
        # Check if frames exist
        mobile_frames_dir = output_dir + "MobileFrames/"
        desktop_frames_dir = output_dir + "DesktopFrames/"
        
        # Get looping settings from control scene
        control_scene = bpy.data.scenes.get("ControlScene", context.scene)
        if not control_scene:
            self.report({'WARNING'}, "⚠️ ControlScene not found, using current scene")
            control_scene = context.scene
        
        # Safe attribute access
        loop_extend_frames = getattr(control_scene, "loop_extend_frames", False)
        hold_frames = getattr(control_scene, "hold_frames", 15)
        self.report({'INFO'}, f"🔄 Loop settings: loop={loop_extend_frames}, hold_frames={hold_frames}")
        
        # Use the source scene's FPS
        mobile_scene = bpy.data.scenes.get("MobileScene")
        desktop_scene = bpy.data.scenes.get("DesktopScene")
        
        mobile_fps = mobile_scene.render.fps if mobile_scene else 30
        desktop_fps = desktop_scene.render.fps if desktop_scene else 30
        self.report({'INFO'}, f"🔄 FPS settings: mobile={mobile_fps}, desktop={desktop_fps}")
        
        # Generate videos using FFmpeg
        self.report({'INFO'}, "🎞️ --- Generating Videos with FFmpeg ---")
        
        # Mobile video
        self.report({'INFO'}, "🎞️ Creating mobile video...")
        success_mobile = self.create_video_with_ffmpeg(
            frames_dir=mobile_frames_dir,
            output_file=output_dir + "MobileOut/" + blend_filename + ".mp4",
            blend_filename=blend_filename,
            fps=mobile_fps,
            loop=loop_extend_frames,
            hold_frames=hold_frames
        )
        
        # Desktop video
        self.report({'INFO'}, "🎞️ Creating desktop video...")
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
        self.report({'INFO'}, f"🔄 Returned to original scene: {original_scene}")
        
        if success_mobile or success_desktop:
            self.report({'INFO'}, "✅ All rendering complete!")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "❌ No frames were found to render!")
            return {'CANCELLED'}
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed and available with enhanced path detection"""
        try:
            self.report({'INFO'}, "🔍 Checking for FFmpeg installation...")
            
            # List of common FFmpeg locations on macOS
            mac_ffmpeg_paths = [
                '/usr/local/bin/ffmpeg',                    # Homebrew (Intel)
                '/opt/homebrew/bin/ffmpeg',                 # Homebrew (Apple Silicon)
                '/usr/bin/ffmpeg',                          # System
                '/Applications/FFmpeg/bin/ffmpeg',          # Manual install
                os.path.expanduser('~/bin/ffmpeg'),         # User bin
                os.path.expanduser('~/.local/bin/ffmpeg')   # User local
            ]
            
            # List of common FFmpeg locations on Windows
            windows_ffmpeg_paths = [
                'C:\\Program Files\\FFmpeg\\bin\\ffmpeg.exe',
                'C:\\FFmpeg\\bin\\ffmpeg.exe'
            ]
            
            # Try with direct paths first
            ffmpeg_paths = []
            if sys.platform == 'darwin':  # macOS
                ffmpeg_paths = mac_ffmpeg_paths
            elif sys.platform == 'win32':  # Windows
                ffmpeg_paths = windows_ffmpeg_paths
            
            # Check each path
            for path in ffmpeg_paths:
                if os.path.exists(path):
                    self.report({'INFO'}, f"🔍 Found FFmpeg at: {path}")
                    result = subprocess.run([path, '-version'],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True,
                                         check=False)
                    
                    if result.returncode == 0:
                        version_line = result.stdout.split('\n')[0]
                        self.report({'INFO'}, f"✅ FFmpeg found at {path}: {version_line}")
                        
                        # Store the path for future use
                        self.ffmpeg_path = path
                        return True
            
            # If we get here, try using PATH
            self.report({'INFO'}, "🔍 Checking for FFmpeg in PATH...")
            
            # Get the current PATH environment variable and print it for debugging
            current_path = os.environ.get('PATH', '')
            self.report({'INFO'}, f"🔍 Current PATH: {current_path}")
            
            # Try to run ffmpeg using the PATH
            try:
                result = subprocess.run(['ffmpeg', '-version'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True,
                                      check=False)
                
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    self.report({'INFO'}, f"✅ FFmpeg found in PATH: {version_line}")
                    self.ffmpeg_path = 'ffmpeg'  # Use command name since it's in PATH
                    return True
                else:
                    self.report({'ERROR'}, f"❌ FFmpeg check failed with error: {result.stderr}")
            except FileNotFoundError:
                self.report({'ERROR'}, "❌ FFmpeg not found in PATH")
            
            # As a last resort, try to find ffmpeg using the 'which' command on macOS/Linux
            if sys.platform != 'win32':
                try:
                    result = subprocess.run(['which', 'ffmpeg'],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=True,
                                          check=False)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        ffmpeg_path = result.stdout.strip()
                        self.report({'INFO'}, f"🔍 Found FFmpeg via 'which' at: {ffmpeg_path}")
                        
                        # Verify it works
                        verify = subprocess.run([ffmpeg_path, '-version'],
                                              stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE,
                                              text=True,
                                              check=False)
                        
                        if verify.returncode == 0:
                            version_line = verify.stdout.split('\n')[0]
                            self.report({'INFO'}, f"✅ FFmpeg verified at {ffmpeg_path}: {version_line}")
                            self.ffmpeg_path = ffmpeg_path
                            return True
                except Exception as e:
                    self.report({'ERROR'}, f"❌ Error checking for FFmpeg with 'which': {str(e)}")
            
            # We've exhausted all options
            self.report({'ERROR'}, "❌ FFmpeg not found. Please install FFmpeg or update the PATH.")
            self.report({'ERROR'}, "ℹ️ You might need to restart Blender after installing FFmpeg.")
            
            # Offer guidance based on platform
            if sys.platform == 'darwin':
                self.report({'ERROR'}, "ℹ️ On macOS, you can install FFmpeg with: brew install ffmpeg")
            elif sys.platform == 'win32':
                self.report({'ERROR'}, "ℹ️ On Windows, download FFmpeg from https://ffmpeg.org/download.html")
            else:
                self.report({'ERROR'}, "ℹ️ On Linux, use: sudo apt install ffmpeg or equivalent")
            
            return False
        except Exception as e:
            self.report({'ERROR'}, f"❌ Error checking FFmpeg: {str(e)}")
            return False
    
    def convert_exr_to_png(self, frames_dir, blend_filename):
        """Convert EXR files to PNG with proper color management for better video encoding"""
        self.report({'INFO'}, f"🎨 Converting EXR files to PNG for proper color management")
        
        # Find EXR frames
        exr_frames = self.find_frames(frames_dir, blend_filename)
        if not exr_frames:
            self.report({'WARNING'}, f"⚠️ No EXR frames found to convert")
            return []
        
        # Create a temporary directory for PNG frames
        png_dir = os.path.join(bpy.path.abspath(frames_dir), "png_temp")
        os.makedirs(png_dir, exist_ok=True)
        self.report({'INFO'}, f"📁 Created PNG conversion directory: {png_dir}")
        
        # Create a temporary Blender scene for EXR to PNG conversion with proper color management
        temp_scene = bpy.data.scenes.new("__temp_convert_scene")
        
        # Set up proper color management
        temp_scene.view_settings.view_transform = 'Filmic'  # or 'Standard' depending on your preference
        temp_scene.view_settings.look = 'None'
        temp_scene.display_settings.display_device = 'sRGB'
        
        # Set up rendering settings
        temp_scene.render.image_settings.file_format = 'PNG'
        temp_scene.render.image_settings.color_mode = 'RGBA'
        temp_scene.render.image_settings.color_depth = '8'
        
        png_frames = []
        
        try:
            # Process each EXR frame
            for i, exr_path in enumerate(exr_frames):
                if i % 10 == 0 or i == len(exr_frames) - 1:  # Log progress every 10 frames and the last frame
                    self.report({'INFO'}, f"🔄 Converting frame {i+1}/{len(exr_frames)}")
                
                # Get frame number from filename
                basename = os.path.basename(exr_path)
                match = re.search(r'_(\d+)\.', basename)
                if not match:
                    self.report({'WARNING'}, f"⚠️ Could not extract frame number from {basename}")
                    continue
                    
                frame_num = match.group(1)
                
                # Create output PNG path
                png_path = os.path.join(png_dir, f"{blend_filename}_{frame_num}.png")
                
                # Skip if PNG already exists
                if os.path.exists(png_path):
                    self.report({'INFO'}, f"✅ PNG already exists: {png_path}")
                    png_frames.append(png_path)
                    continue
                
                # Load the EXR image
                img_name = f"temp_convert_{i}"
                if img_name in bpy.data.images:
                    bpy.data.images.remove(bpy.data.images[img_name])
                
                try:
                    img = bpy.data.images.load(exr_path)
                    img.name = img_name
                except Exception as e:
                    self.report({'ERROR'}, f"❌ Error loading EXR {exr_path}: {str(e)}")
                    continue
                
                # Set color space explicitly
                img.colorspace_settings.name = 'Linear'
                
                # Save as PNG with color management applied
                img.filepath_raw = png_path
                img.file_format = 'PNG'
                
                try:
                    img.save_render(png_path, scene=temp_scene)
                    self.report({'INFO'}, f"✅ Saved PNG: {png_path}")
                except Exception as e:
                    self.report({'ERROR'}, f"❌ Error saving PNG {png_path}: {str(e)}")
                    continue
                
                # Add to list of PNG frames
                png_frames.append(png_path)
                
                # Clean up
                bpy.data.images.remove(img)
        
        except Exception as e:
            self.report({'ERROR'}, f"❌ Error during EXR to PNG conversion: {str(e)}")
        
        finally:
            # Clean up the temporary scene
            bpy.data.scenes.remove(temp_scene)
        
        self.report({'INFO'}, f"✅ Converted {len(png_frames)}/{len(exr_frames)} EXR frames to PNG")
        return png_frames
    
    def find_frames(self, frames_dir, blend_filename):
        """Find all frames in the directory and return sorted list"""
        # Make sure we're using the right path format for Blender
        abs_frames_dir = bpy.path.abspath(frames_dir)
        
        self.report({'INFO'}, f"🔍 Looking for frames in directory: {abs_frames_dir}")
        
        # Check if directory exists
        if not os.path.exists(abs_frames_dir):
            self.report({'ERROR'}, f"❌ Frames directory does not exist: {abs_frames_dir}")
            return []
        
        # List all files in the directory for debugging
        try:
            existing_files = os.listdir(abs_frames_dir)
            self.report({'INFO'}, f"📁 Directory contains {len(existing_files)} files")
            if existing_files:
                self.report({'INFO'}, f"📁 First few files: {existing_files[:5]}")
        except Exception as e:
            self.report({'ERROR'}, f"❌ Error listing directory contents: {str(e)}")
        
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
            self.report({'INFO'}, f"🔍 Looking for frames with pattern: {pattern}")
            frames = glob.glob(pattern)
            self.report({'INFO'}, f"🔍 Found {len(frames)} frames with pattern {os.path.basename(pattern)}")
            all_frames.extend(frames)
        
        if not all_frames:
            self.report({'WARNING'}, f"⚠️ No frames found matching filename pattern '{blend_filename}_*' in {abs_frames_dir}")
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
            self.report({'INFO'}, f"✅ Found {len(all_frames)} frames in total")
            self.report({'INFO'}, f"📄 First frame: {os.path.basename(all_frames[0])}")
            if len(all_frames) > 1:
                self.report({'INFO'}, f"📄 Second frame: {os.path.basename(all_frames[1])}")
            self.report({'INFO'}, f"📄 Last frame: {os.path.basename(all_frames[-1])}")
        
        return all_frames
    
    def prepare_frames_for_ffmpeg(self, frames, temp_dir, loop=False, hold_frames=15):
        """Copy and organize frames for FFmpeg to process including loops and holds"""
        frame_count = len(frames)
        if frame_count == 0:
            self.report({'ERROR'}, "❌ No frames to prepare for FFmpeg")
            return 0
            
        self.report({'INFO'}, f"🔄 Preparing {frame_count} frames in {temp_dir}")
        
        # Get file extension from the first frame
        _, ext = os.path.splitext(frames[0])
        
        # For simple forward animation (no loop)
        if not loop or frame_count <= 1:
            self.report({'INFO'}, "🔄 Creating simple forward animation (no loop)")
            # Copy all frames with sequential numbering for ffmpeg
            for i, frame_path in enumerate(frames):
                new_name = f"frame_{i+1:04d}{ext}"
                new_path = os.path.join(temp_dir, new_name)
                shutil.copy2(frame_path, new_path)
                if i % 10 == 0 or i == frame_count - 1:  # Report progress every 10 frames and the last frame
                    self.report({'INFO'}, f"🔄 Copied frame {i+1}/{frame_count}")
            return frame_count
        
        # For loop animation (forward + hold + reverse + hold)
        self.report({'INFO'}, f"🔄 Creating loop animation (forward + hold + reverse + hold)")
        total_frames = 0
        
        # 1. Forward animation
        self.report({'INFO'}, f"🔄 Adding forward animation ({len(frames)} frames)")
        for i, frame_path in enumerate(frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(frame_path, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        # 2. Hold last frame
        last_frame = frames[-1]
        self.report({'INFO'}, f"🔄 Adding hold on last frame ({hold_frames} frames)")
        for i in range(hold_frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(last_frame, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        # 3. Reverse animation
        self.report({'INFO'}, f"🔄 Adding reverse animation ({len(frames)} frames)")
        for frame_path in reversed(frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(frame_path, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        # 4. Hold first frame
        first_frame = frames[0]
        self.report({'INFO'}, f"🔄 Adding hold on first frame ({hold_frames} frames)")
        for i in range(hold_frames):
            new_name = f"frame_{total_frames+1:04d}{ext}"
            shutil.copy2(first_frame, os.path.join(temp_dir, new_name))
            total_frames += 1
        
        self.report({'INFO'}, f"✅ Prepared total of {total_frames} frames for FFmpeg")
        return total_frames
    
    def create_video_with_ffmpeg(self, frames_dir, output_file, blend_filename, fps=30, 
                               loop=False, hold_frames=15, quality="high", crf=23):
        """Use FFmpeg to create video from frames with proper color management"""
        # Check if FFmpeg is available
        if not self.check_ffmpeg():
            self.report({'ERROR'}, "❌ FFmpeg is required but not found. Please install FFmpeg.")
            return False
        
        # Use the stored ffmpeg path
        ffmpeg_command = getattr(self, 'ffmpeg_path', 'ffmpeg')
        
        # Find original frames to check format
        self.report({'INFO'}, f"🔍 Checking frames in {frames_dir}")
        original_frames = self.find_frames(frames_dir, blend_filename)
        
        if not original_frames:
            self.report({'WARNING'}, f"⚠️ No frames found in {frames_dir}")
            return False
        
        # Check if we have EXR files that need conversion
        _, ext = os.path.splitext(original_frames[0])
        is_exr = ext.lower() == '.exr'
        
        # Use frames variable to store whatever frames we'll process (either original or converted)
        frames = original_frames
        
        # For EXR files, convert to PNG first for better color management
        if is_exr:
            self.report({'INFO'}, f"🎨 Detected EXR frames, converting to PNG for proper color handling")
            png_frames = self.convert_exr_to_png(frames_dir, blend_filename)
            if png_frames and len(png_frames) > 0:
                self.report({'INFO'}, f"🎨 Using converted PNG frames instead of EXR")
                frames = png_frames
            else:
                self.report({'WARNING'}, f"⚠️ PNG conversion failed, falling back to original EXR frames")
        
        # Create temporary directory for frame processing
        with tempfile.TemporaryDirectory() as temp_dir:
            self.report({'INFO'}, f"📁 Created temporary directory: {temp_dir}")
            
            # Prepare frames (copy/rename for FFmpeg and handle looping)
            total_frames = self.prepare_frames_for_ffmpeg(
                frames, 
                temp_dir, 
                loop=loop, 
                hold_frames=hold_frames
            )
            
            if total_frames == 0:
                self.report({'ERROR'}, "❌ No frames were prepared for FFmpeg")
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
            output_dir = os.path.dirname(abs_output_file)
            if not os.path.exists(output_dir):
                self.report({'INFO'}, f"📁 Creating output directory: {output_dir}")
                os.makedirs(output_dir, exist_ok=True)
            
            # Get file extension for the frame sequence in temp_dir
            first_frame = glob.glob(os.path.join(temp_dir, "frame_*.*"))[0]
            frame_ext = os.path.splitext(first_frame)[1]
            
            # Build FFmpeg command with extensive options
            cmd = [
                ffmpeg_command, '-y',  # Use the found ffmpeg path
                '-framerate', str(fps),
                '-i', os.path.join(temp_dir, f'frame_%04d{frame_ext}'),
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
            self.report({'INFO'}, f"🎞️ Running FFmpeg command:")
            self.report({'INFO'}, f"🎞️ {' '.join(cmd)}")
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                if result.returncode == 0:
                    self.report({'INFO'}, f"✅ FFmpeg successfully created video: {output_file}")
                    # Check if the file was actually created
                    if os.path.exists(abs_output_file):
                        file_size = os.path.getsize(abs_output_file)
                        self.report({'INFO'}, f"✅ Output file exists: {abs_output_file}")
                        self.report({'INFO'}, f"✅ File size: {file_size / 1024 / 1024:.2f} MB")
                    else:
                        self.report({'WARNING'}, f"⚠️ FFmpeg reported success but output file not found: {abs_output_file}")
                    return True
                else:
                    self.report({'ERROR'}, f"❌ FFmpeg error (code {result.returncode}):")
                    for line in result.stderr.splitlines():
                        self.report({'ERROR'}, f"❌ {line}")
                    return False
            except Exception as e:
                self.report({'ERROR'}, f"❌ Error running FFmpeg: {str(e)}")
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