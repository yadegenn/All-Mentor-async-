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
handlers_folder = "handlers"
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
    bot_output_folder = os.path.join(output_folder, folder_name) if not bot.get('IsParasite') else os.path.join(output_folder, f"{bot['host_folder']}/parasite")

    # Create bot-specific output directory


    if not os.path.exists(bot_output_folder):
        os.makedirs(bot_output_folder)
        # For non-Apps bots, just use the base template
    template = env.get_template(os.path.basename(base_template_file))
    if bot.get("IsParasite"):
        bot['Folder_Name'] = bot['host_folder']

    final_content = template.render(**bot)
    try:
        with open(os.path.join(bot_output_folder, "loader.py"), 'w', encoding='utf-8') as main_file:
            main_file.write(final_content)
    except Exception as e:
        print(f"Error writing file for {folder_name}: {str(e)}")
        continue
    shutil.copyfile("test_bot/main.py", os.path.join(bot_output_folder, "main.py"))
    shutil.copyfile("test_bot/currency_rate.json", os.path.join(bot_output_folder, "currency_rate.json"))
    shutil.copyfile("test_bot/main.png", os.path.join(bot_output_folder, "main.png"))
    if os.path.exists(f"test_bot/{middleware_folder}"):
        try:
            shutil.copytree(f"test_bot/{middleware_folder}", os.path.join(bot_output_folder, middleware_folder),
                            dirs_exist_ok=True)

        except Exception as e:
            print(f"Error copying middleware for {folder_name}: {str(e)}")
    if os.path.exists(f"test_bot/{utils_folder}"):
        try:
            shutil.copytree(f"test_bot/{utils_folder}", os.path.join(bot_output_folder, utils_folder), dirs_exist_ok=True)

        except Exception as e:
            print(f"Error copying utils for {folder_name}: {str(e)}")
    if os.path.exists(f"test_bot/{handlers_folder}"):
        try:
            shutil.copytree(f"test_bot/{handlers_folder}", os.path.join(bot_output_folder, handlers_folder), dirs_exist_ok=True)

        except Exception as e:
            print(f"Error copying utils for {folder_name}: {str(e)}")
    # Write the rendered content to main.py


    # Copy middleware folder to the bot's output folder

print("Files generated successfully.")