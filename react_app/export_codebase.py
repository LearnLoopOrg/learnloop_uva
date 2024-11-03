import os

# Pas de directory aan als je het script vanuit een andere locatie uitvoert
root_dir = "."
output_file = "codebase.txt"
extensions = [
    ".py",
    ".js",
    ".html",
    ".css",
    ".java",
]  # Voeg andere extensies toe die je wilt opnemen

# Bestanden en mappen om over te slaan
excluded_files = {
    "package-lock.json",
    "package.json",
    ".gitignore",
    "reportWebVitals.js",
    "setupTests.js",
}
excluded_dirs = {"node_modules"}

with open(output_file, "w", encoding="utf-8") as out_file:
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Verwijder uitgesloten directories uit de doorzoeking
        dirnames[:] = [d for d in dirnames if d not in excluded_dirs]

        for filename in filenames:
            # Sla uitgesloten bestanden over
            if filename in excluded_files:
                continue

            file_path = os.path.join(dirpath, filename)
            if any(filename.endswith(ext) for ext in extensions):
                with open(file_path, "r", encoding="utf-8") as code_file:
                    # Schrijf een Markdown header en pad voor elk bestand
                    out_file.write(f"\n# {file_path}\n\n")
                    # Lees de code-inhoud en schrijf die in het output-bestand
                    out_file.write(code_file.read())
                    # Voeg een scheiding toe na elk bestand
                    out_file.write("\n\n---\n\n")

print(f"Codebase succesvol opgeslagen in {output_file}")
