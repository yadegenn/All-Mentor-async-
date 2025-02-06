import os
import json
import shutil
from jinja2 import Environment, FileSystemLoader

# Paths
data_file = "data.json"
default_template_file = "templates/template.py.j2"
output_folder = "output"
middleware_folder = "middlewares"

# Load data
with open(data_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Configure Jinja2 environment
template_dir = 'templates'  # Base template directory
file_loader = FileSystemLoader(template_dir)
env = Environment(loader=file_loader)

# Create output directory if not exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Process each bot configuration
for bot in data['bots']:
    folder_name = bot['Folder_Name']
    bot_output_folder = os.path.join(output_folder, folder_name)

    # Create bot-specific output directory
    if not os.path.exists(bot_output_folder):
        os.makedirs(bot_output_folder)

    # Choose template based on template_type
    if bot.get('template_type') == 'Apps':
        # Get the specific template for this Apps bot
        template_path = bot.get('template_path')
        if not template_path:
            print(f"Warning: No template path specified for Apps bot {folder_name}")
            continue

        # Get just the filename from the template path
        template_filename = os.path.basename(template_path)
        template = env.get_template(template_filename)
    else:
        # Use default template for non-Apps bots
        template = env.get_template(os.path.basename(default_template_file))

    # Render the template
    try:
        rendered_content = template.render(**bot)
    except Exception as e:
        print(f"Error rendering template for {folder_name}: {str(e)}")
        continue

    # Write the rendered content to main.py
    try:
        with open(os.path.join(bot_output_folder, "main.py"), 'w', encoding='utf-8') as main_file:
            main_file.write(rendered_content)
    except Exception as e:
        print(f"Error writing file for {folder_name}: {str(e)}")
        continue

    # Copy middleware folder to the bot's output folder
    if os.path.exists(middleware_folder):
        try:
            shutil.copytree(middleware_folder, os.path.join(bot_output_folder, middleware_folder), dirs_exist_ok=True)
        except Exception as e:
            print(f"Error copying middleware for {folder_name}: {str(e)}")

print("Files generated successfully.")