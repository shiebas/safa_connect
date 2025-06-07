# Create a script to help find where CustomUserForm is used
import os

def find_file_with_text(directory, search_text):
    found_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if search_text in content:
                            found_files.append(file_path)
                except Exception as e:
                    # Optionally print or log the error
                    pass
    return found_files

search_text = "CustomUserForm"
found_files = find_file_with_text('/home/shaun/safa_global', search_text)

for file in found_files:
    print(file)