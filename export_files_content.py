import os

output_file_path = "exported_src_code_list.txt"


# Function to write files to the output file
def write_files_to_output(paths, output_file):
    for path in paths:
        path = path.strip()
        if os.path.isfile(path):
            # Write the file title
            output_file.write(f"--- {os.path.basename(path)} ---\n")
            # Write the file content
            with open(path, "r", encoding="utf-8") as f:
                output_file.write(f.read())
            # Write a separator line
            output_file.write("\n" + "-" * 40 + "\n")
        elif os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Write the file title
                    output_file.write(f"--- {os.path.basename(file_path)} ---\n")
                    # Write the file content
                    with open(file_path, "r", encoding="utf-8") as f:
                        output_file.write(f.read())
                    # Write a separator line
                    output_file.write("\n" + "-" * 40 + "\n")


file_paths_raw = r"""
C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\src\components
C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\src\App.css
C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\src\App.js
C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\src\index.css
C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\src\index.js
"""
file_paths = file_paths_raw.strip().split("\n")

with open(output_file_path, "w", encoding="utf-8") as output_file:
    write_files_to_output(file_paths, output_file)

print(f"File list has been written to {output_file_path}")
