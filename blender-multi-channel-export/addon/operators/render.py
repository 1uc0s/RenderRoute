import bpy
from bpy.props import StringProperty
from bpy.types import Operator

class RenderAllOperator(Operator):
    """Render all scenes and composites in sequence"""
    bl_idname = "export.render_all"
    bl_label = "Render All Scenes"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        scenes_to_render = [
            "MobileScene",
            "MobileScene_Comp",
            "DesktopScene",
            "DesktopScene_Comp"
        ]
        
        # Store original scene
        original_scene = context.window.scene.name
        
        # Ensure we're rendering one scene at a time
        for scene_name in scenes_to_render:
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
        
        # Return to original scene (likely the control scene)
        context.window.scene = bpy.data.scenes[original_scene]
        self.report({'INFO'}, "All rendering complete!")
        return {'FINISHED'}


class RenderMobileOnlyOperator(Operator):
    """Render only the mobile scenes"""
    bl_idname = "export.render_mobile"
    bl_label = "Render Mobile Only"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        scenes_to_render = [
            "MobileScene",
            "MobileScene_Comp"
        ]
        
        # Store original scene
        original_scene = context.window.scene.name
        
        # Ensure we're rendering one scene at a time
        for scene_name in scenes_to_render:
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
        
        # Return to original scene (likely the control scene)
        context.window.scene = bpy.data.scenes[original_scene]
        self.report({'INFO'}, "Mobile rendering complete!")
        return {'FINISHED'}


class RenderDesktopOnlyOperator(Operator):
    """Render only the desktop scenes"""
    bl_idname = "export.render_desktop"
    bl_label = "Render Desktop Only"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        scenes_to_render = [
            "DesktopScene",
            "DesktopScene_Comp"
        ]
        
        # Store original scene
        original_scene = context.window.scene.name
        
        # Ensure we're rendering one scene at a time
        for scene_name in scenes_to_render:
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
        
        # Return to original scene (likely the control scene)
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