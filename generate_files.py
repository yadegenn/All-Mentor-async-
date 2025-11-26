import os
import json
import shutil
from jinja2 import Environment, FileSystemLoader

# Paths
data_file = "data.json"
base_template_file = "templates/template.py.j2"
output_folder = "output"
middleware_folder = "middlewares"
utils_folder = "utils"
# Load data
with open(data_file, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Configure Jinja2 environment
template_dir = 'templates'
file_loader = FileSystemLoader(template_dir)
env = Environment(loader=file_loader)

# Create output directory if not exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)


def find_function_boundaries(content, func_name):
    """Find the start and end of a function in the content."""
    # Find the function definition
    func_start = content.find(f"async def {func_name}")
    if func_start == -1:
        return None, None

    # Find the start of the next function or if __name__ block
    next_def = content.find("\nasync def", func_start + 1)
    if_name_start = content.find("\nif __name__", func_start + 1)

    # Get the earliest next block after our function
    possible_ends = [pos for pos in [next_def, if_name_start] if pos != -1]
    func_end = min(possible_ends) if possible_ends else len(content)

    return func_start, func_end


# Process each bot configuration
for bot in data['bots']:
    folder_name = bot['Folder_Name']
    bot_output_folder = os.path.join(output_folder, folder_name)

    # Create bot-specific output directory
    if not os.path.exists(bot_output_folder):
        os.makedirs(bot_output_folder)

    if bot.get('template_type') == 'Apps':
        # Step 1: Get the base template and render it with bot data
        base_template = env.get_template(os.path.basename(base_template_file))
        base_rendered = base_template.render(**bot)

        # Step 2: Get the specific Apps template
        template_path = bot.get('template_path')
        if not template_path:
            print(f"Warning: No template path specified for Apps bot {folder_name}")
            continue

        apps_template = env.get_template(os.path.basename(template_path))
        apps_rendered = apps_template.render(**bot)

        # Find main function boundaries
        main_start, main_end = find_function_boundaries(base_rendered, "main")
        if main_start is None:
            print(f"Error: Could not find main function in base template for {folder_name}")
            continue

        # Combine the templates:
        # 1. Everything before main from base template
        # 2. The apps template content
        # 3. Everything after main from base template
        final_content = (
                base_rendered[:main_start] +  # Before main (includes all previous functions)
                apps_rendered +  # Apps template content
                base_rendered[main_end:]  # After main (includes if __name__ block)
        )

    else:
        # For non-Apps bots, just use the base template
        template = env.get_template(os.path.basename(base_template_file))
        final_content = template.render(**bot)

    # Write the rendered content to main.py
    try:
        with open(os.path.join(bot_output_folder, "main.py"), 'w', encoding='utf-8') as main_file:
            main_file.write(final_content)
    except Exception as e:
        print(f"Error writing file for {folder_name}: {str(e)}")
        continue

    # Copy middleware folder to the bot's output folder
    if os.path.exists(middleware_folder):
        try:
            shutil.copytree(middleware_folder, os.path.join(bot_output_folder, middleware_folder), dirs_exist_ok=True)

        except Exception as e:
            print(f"Error copying middleware for {folder_name}: {str(e)}")
    if os.path.exists(utils_folder):
        try:
            shutil.copytree(utils_folder, os.path.join(bot_output_folder, utils_folder), dirs_exist_ok=True)

        except Exception as e:
            print(f"Error copying utils for {folder_name}: {str(e)}")

print("Files generated successfully.")