import os
import json
import shutil
from jinja2 import Environment, FileSystemLoader

# Paths
data_file = "data.json"
template_file = "templates/template.py.j2"
output_folder = "output"
middleware_folder = "middlewares"

# Load data
with open(data_file, 'r') as file:
    data = json.load(file)

# Configure Jinja2 environment
file_loader = FileSystemLoader(os.path.dirname(template_file))
env = Environment(loader=file_loader)
template = env.get_template(os.path.basename(template_file))

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

    # Render the template
    rendered_content = template.render(**bot)

    # Write the rendered content to main.py
    with open(os.path.join(bot_output_folder, "main.py"), 'w') as main_file:
        main_file.write(rendered_content)

    # Copy middleware folder to the bot's output folder
    if os.path.exists(middleware_folder):
        shutil.copytree(middleware_folder, os.path.join(bot_output_folder, middleware_folder), dirs_exist_ok=True)

print("Files generated successfully.")
