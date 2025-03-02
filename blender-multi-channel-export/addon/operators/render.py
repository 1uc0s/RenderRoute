import bpy
import os
import sys  # Add sys module for platform detection
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
       