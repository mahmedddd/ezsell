import os
import re

# We are in the frontend directory
src_dir = "src"

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith((".tsx", ".ts")):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Remove .ts extension from relative imports
            new_content = re.sub(r"(['\"]\.*[/\\]lib[/\\]api)\.ts(['\"])", r"\1\2", content)
            new_content = re.sub(r"(['\"]\.*[/\\]lib[/\\]utils)\.ts(['\"])", r"\1\2", new_content)
            new_content = re.sub(r"(['\"]\.*[/\\]lib[/\\]nlp)\.ts(['\"])", r"\1\2", new_content)

            if content != new_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Cleaned up extensions in {path}")
