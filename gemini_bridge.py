import bpy
import textwrap
import urllib.request
import urllib.error
import json

bl_info = {
    "name": "Gemini AI Native Bridge",
    "description": "Connects Blender directly to Google's Gemini AI with scene context awareness, without requiring external pip modules.",
    "author": "aminebncd", 
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar (N) > Gemini AI",
    "category": "3D View",
}

# --- SETUP YOUR API KEY HERE ---
# Get yours at: https://aistudio.google.com/
API_KEY = "YOUR_API_KEY_HERE"
# -------------------------------

def ask_gemini_direct(full_prompt, model_name):
    """Handles the native HTTP POST request to the Gemini API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "temperature": 0.7, 
            "maxOutputTokens": 2048
        }
    }
    
    req = urllib.request.Request(url, method="POST")
    req.add_header('Content-Type', 'application/json')
    
    try:
        json_data = json.dumps(payload).encode('utf-8')
        response = urllib.request.urlopen(req, data=json_data)
        res_dict = json.loads(response.read().decode('utf-8'))
        
        if 'candidates' in res_dict and len(res_dict['candidates']) > 0:
            return res_dict['candidates'][0]['content']['parts'][0]['text']
        else:
            return "Error: Empty response from API."
            
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        try:
            err_data = json.loads(error_msg)
            reason = err_data.get('error', {}).get('message', error_msg)
            return f"API Denied: {reason}"
        except:
            return f"HTTP Error {e.code}: {error_msg}"
    except Exception as e:
        return f"Internal Python Error: {str(e)}"

def _label_multiline(context, text, parent):
    """Custom wrapper to handle multiline text in Blender's UI panels."""
    if not text or text == "":
        return
        
    width = context.region.width
    chars = int(width / 7) if width > 0 else 40
    chars = max(35, chars) # Minimum character width
    
    wrapper = textwrap.TextWrapper(width=chars)
    for line in text.split("\n"):
        if line.strip() == "":
            parent.separator()
        else:
            for wrap_line in wrapper.wrap(text=line):
                parent.label(text=wrap_line)

class GeminiChatPanel(bpy.types.Panel):
    """Creates a Panel in the 3D Viewport sidebar"""
    bl_label = "Gemini AI Bridge"
    bl_idname = "VIEW3D_PT_gemini_chat"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Gemini AI'

    def draw(self, context):
        layout = self.layout
        
        layout.prop(context.scene, "gemini_selected_model", text="Model")
        layout.separator()
        
        layout.label(text="Ask your question:")
        layout.prop(context.scene, "gemini_message", text="")
        layout.operator("object.send_to_gemini", text="Send with Context", icon='PLAY')
        layout.separator()
        
        layout.label(text="Response:")
        box = layout.box()
        _label_multiline(context, context.scene.gemini_response, box)
        
        # UX Tools: Copy & Export
        if context.scene.gemini_response and context.scene.gemini_response not in ["", "Waiting..."]:
            layout.separator()
            row = layout.row()
            row.operator("object.copy_gemini_response", text="Copy", icon='COPYDOWN')
            row.operator("object.gemini_to_text_editor", text="To Text Editor", icon='TEXT')

class CopyGeminiResponseOperator(bpy.types.Operator):
    bl_idname = "object.copy_gemini_response"
    bl_label = "Copy Response to Clipboard"

    def execute(self, context):
        context.window_manager.clipboard = context.scene.gemini_response
        self.report({'INFO'}, "Response copied to clipboard!")
        return {'FINISHED'}

class SendToTextEditorOperator(bpy.types.Operator):
    bl_idname = "object.gemini_to_text_editor"
    bl_label = "Open in Text Editor"

    def execute(self, context):
        text_name = "Gemini_Response.txt"
        if text_name not in bpy.data.texts:
            bpy.data.texts.new(text_name)
        text_block = bpy.data.texts[text_name]
        text_block.clear()
        text_block.write(context.scene.gemini_response)
        self.report({'INFO'}, f"Exported to Text Editor: '{text_name}'")
        return {'FINISHED'}

class SendToGeminiOperator(bpy.types.Operator):
    bl_idname = "object.send_to_gemini"
    bl_label = "Send Message to Gemini"

    def execute(self, context):
        user_input = context.scene.gemini_message
        selected_model = context.scene.gemini_selected_model
        
        # --- INVISIBLE SCENE CONTEXT FOR THE AI ---
        active_obj = context.active_object
        context_str = "You are a Blender 3D expert assistant. Here is the current scene data:\n[CONTEXT]\n"
        
        if active_obj:
            context_str += f"- Active object selected: {active_obj.name} (Type: {active_obj.type})\n"
            if active_obj.type == 'MESH':
                context_str += f"  - Vertices: {len(active_obj.data.vertices)}, Faces: {len(active_obj.data.polygons)}\n"
            elif active_obj.type == 'ARMATURE':
                context_str += f"  - Bones: {len(active_obj.data.bones)}\n"
                context_str += f"  - Current Mode: {context.active_object.mode}\n"
        else:
            context_str += "- No object selected.\n"
            
        context_str += "[END OF CONTEXT]\n\n"
        context_str += f"USER QUESTION: {user_input}\n"
        context_str += "STRICT INSTRUCTION: Reply in PLAIN TEXT ONLY. NEVER use asterisks (**) or markdown formatting. Keep sentences concise."
        # ------------------------------------------
        
        context.scene.gemini_response = "Waiting..."
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1) # Force UI refresh
        
        response = ask_gemini_direct(context_str, selected_model)
        context.scene.gemini_response = response

        return {'FINISHED'}

def register():
    bpy.utils.register_class(GeminiChatPanel)
    bpy.utils.register_class(SendToGeminiOperator)
    bpy.utils.register_class(CopyGeminiResponseOperator)
    bpy.utils.register_class(SendToTextEditorOperator)
    
    bpy.types.Scene.gemini_message = bpy.props.StringProperty(name="Message", default="")
    bpy.types.Scene.gemini_response = bpy.props.StringProperty(name="Response", default="")
    
    # Model Dropdown
    bpy.types.Scene.gemini_selected_model = bpy.props.EnumProperty(
        name="AI Model",
        description="Choose the Gemini reasoning engine",
        items=[
            ('gemini-2.5-flash', "2.5 Flash (Fast & Nimble)", "Highly responsive, great for quick questions"),
            ('gemini-2.5-pro', "2.5 Pro (Expert)", "Deep reasoning for complex scripts or rigging issues"),
            ('gemini-3.1-pro-preview', "3.1 Pro (Experimental)", "Test the latest bleeding-edge model"),
        ],
        default='gemini-2.5-flash'
    )

def unregister():
    bpy.utils.unregister_class(GeminiChatPanel)
    bpy.utils.unregister_class(SendToGeminiOperator)
    bpy.utils.unregister_class(CopyGeminiResponseOperator)
    bpy.utils.unregister_class(SendToTextEditorOperator)
    del bpy.types.Scene.gemini_message
    del bpy.types.Scene.gemini_response
    del bpy.types.Scene.gemini_selected_model

if __name__ == "__main__":
    register()
