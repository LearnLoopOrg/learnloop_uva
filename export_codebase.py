import os

# Define the directory paths
charts_directory_path = (
    r"C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\charts"
)
react_app_directory_path = (
    r"C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app"
)
src_directory_path = r"C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\src"
backend_directory_path = r"C:\Users\LucMa\OneDrive\Desktop\LearnLoop\repositories\learnloop_uva\react_app\backend"
output_file_path = os.path.join(charts_directory_path, "file_list.txt")


# Function to write files to the output file
def write_files_to_output(directory_path, output_file, specific_files=None):
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            if (
                specific_files is None
                or file_path in specific_files
                or any(
                    file_path.startswith(os.path.join(directory_path, sf))
                    for sf in specific_files
                )
            ):
                # Write the file title
                output_file.write(f"--- {file} ---\n")
                # Write the file content
                with open(file_path, "r", encoding="utf-8") as f:
                    output_file.write(f.read())
                # Write a separator line
                output_file.write("\n" + "-" * 40 + "\n")


# List of specific files to include
specific_files = [
    os.path.join(src_directory_path, "app.js"),
    os.path.join(src_directory_path, "index.js"),
    os.path.join(backend_directory_path, "index.js"),
]

# Open the output file in write mode
with open(output_file_path, "w", encoding="utf-8") as output_file:
    # Write files from the charts directory
    write_files_to_output(charts_directory_path, output_file)
    # Write Dockerfiles from the react_app directory
    write_files_to_output(
        react_app_directory_path,
        output_file,
        specific_files=[os.path.join(react_app_directory_path, "Dockerfile")],
    )
    # Write specific files from the src and backend directories
    write_files_to_output(
        src_directory_path,
        output_file,
        specific_files=specific_files
        + [os.path.join(src_directory_path, "components")],
    )
    write_files_to_output(
        backend_directory_path, output_file, specific_files=specific_files
    )

print(f"File list has been written to {output_file_path}")
