# Gemini AI Native Bridge for Blender

A lightweight, powerful, and **pip-free** Blender add-on that connects directly to Google's Gemini AI API. It reads your active scene context (selected objects, meshes, armatures) and sends it to Gemini to provide highly accurate, contextual assistance.

## Features
- **Zero Dependencies:** Uses Python's native `urllib`. No need to mess around with installing `google-generativeai` via `pip` inside Blender!
- **Context-Aware:** Automatically sends details about your active object (vertices, faces, bones, modes) to the AI.
- **Model Selector:** Choose between `Gemini 2.5 Flash` (speed), `2.5 Pro` (complex reasoning), or bleeding-edge previews.
- **Smart UX:** Features automatic text wrapping, a "Copy to Clipboard" button, and an "Open in Text Editor" button for long scripts or answers.

## Installation
1. Download `gemini_bridge.py`.
2. Open the script in a text editor and replace `YOUR_API_KEY_HERE` (line 19) with your actual API key from [Google AI Studio](https://aistudio.google.com/).
3. In Blender, go to `Edit > Preferences > Add-ons > Install...` and select the script.
4. Check the box to enable it.
5. Press `N` in the 3D Viewport to open the sidebar and navigate to the **Gemini AI** tab.

## Security Note
**Never commit or share your API key publicly.** Keep it local.
