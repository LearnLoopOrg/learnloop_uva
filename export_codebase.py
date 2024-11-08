import os


def export_directory_content(
    dir_path, output_file="exported_codebase.txt", ignore_list=[]
):
    # Reset file-inhoud van exported_codebase.txt
    open(output_file, "w").close()

    # Schrijf de folderstructuur en file-inhoud naar exported_codebase.txt
    with open(output_file, "w", encoding="utf-8") as out:
        # Folderstructuur toevoegen
        out.write("Folder Structure:\n")
        for root, dirs, files in os.walk(dir_path):
            # Filter directories die genegeerd moeten worden
            dirs[:] = [d for d in dirs if d not in ignore_list]
            level = root.replace(dir_path, "").count(os.sep)
            indent = " " * 4 * level
            if os.path.basename(root) not in ignore_list:
                out.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = " " * 4 * (level + 1)
            for file in files:
                if file not in ignore_list:
                    out.write(f"{subindent}{file}\n")
        out.write("\n" + "=" * 50 + "\n\n")

        # Bestanden en inhoud toevoegen
        for root, dirs, files in os.walk(dir_path):
            # Filter directories die genegeerd moeten worden
            dirs[:] = [d for d in dirs if d not in ignore_list]
            for file in files:
                if file not in ignore_list:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, dir_path)
                    out.write(f"File: {relative_path}\n")
                    out.write("-" * 50 + "\n")
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        out.write(f.read())
                    out.write("\n" + "-" * 50 + "\n\n")

    print(f"Directory content exported to {output_file}")


if __name__ == "__main__":
    # Stel het pad in naar de react_app directory relatief aan het huidige script
    react_app_path = os.path.join(os.getcwd(), "react_app")

    # Stel dat je bestanden en mappen wilt negeren zoals '.git', 'node_modules', en '__pycache__'
    ignore_list = [
        ".git",
        ".env",
        "package-lock.json",
        "node_modules",
        "__pycache__",
        "exported_codebase.txt",
        "requirements.txt",
    ]
    export_directory_content(react_app_path, ignore_list=ignore_list)
