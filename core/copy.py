import shutil
import os

def copy_folder_contents(source_path, destination_path, task_name="Unnamed Task"):
    """
    Copies the contents of a source folder to a destination folder.
    If the destination folder doesn't exist, it will be created.
    If the destination folder exists, its contents will be overwritten/merged.
    """
    if not os.path.exists(source_path):
        print(f"  Error for '{task_name}': Source path '{source_path}' does not exist. Skipping this copy task.")
        return False
    if not os.path.isdir(source_path):
        print(f"  Error for '{task_name}': Source path '{source_path}' is not a directory. Skipping this copy task.")
        return False

    try:
        # Ensure the destination directory exists
        os.makedirs(destination_path, exist_ok=True)
        print(f"    Ensured destination directory exists: '{destination_path}'")

        # Iterate over all items in the source directory
        for item_name in os.listdir(source_path):
            source_item_path = os.path.join(source_path, item_name)
            destination_item_path = os.path.join(destination_path, item_name)

            if os.path.isdir(source_item_path):
                # If it's a directory, recursively copy it
                print(f"      Copying directory: '{source_item_path}' to '{destination_item_path}'")
                shutil.copytree(source_item_path, destination_item_path, dirs_exist_ok=True)
            else:
                # If it's a file, copy it
                print(f"      Copying file: '{source_item_path}' to '{destination_item_path}'")
                shutil.copy2(source_item_path, destination_item_path)

        print(f"  Successfully copied contents for '{task_name}' from '{source_path}' to '{destination_path}'")
        return True
    except Exception as e:
        print(f"  An error occurred during copy for '{task_name}' from '{source_path}' to '{destination_path}': {e}")
        return False