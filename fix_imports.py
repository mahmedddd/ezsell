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
            
            # Calculate distance from 'src'
            # e.g. src/pages is 1 level from src
            # e.g. src/components/ui is 2 levels from src
            rel_to_src = os.path.relpath(root, src_dir)
            if rel_to_src == ".":
                depth = 0
            else:
                depth = rel_to_src.count(os.sep) + 1
            
            prefix = "../" * depth if depth > 0 else "./"
            
            # Replace any variant of lib/api.ts imports
            new_content = re.sub(r"['\"]\.*[/\\]lib[/\\]api\.ts['\"]", f"'{prefix}lib/api.ts'", content)
            new_content = re.sub(r"['\"]\.*[/\\]lib[/\\]utils\.ts['\"]", f"'{prefix}lib/utils.ts'", new_content)
            new_content = re.sub(r"['\"]\.*[/\\]lib[/\\]nlp\.ts['\"]", f"'{prefix}lib/nlp.ts'", new_content)

            if content != new_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path} (depth {depth})")
