import os
import re

root_dir = r"c:\Users\ahmed\ezsell\ezsell\ezsell\frontend\src"

for root, dirs, files in os.walk(root_dir):
    for file in files:
        if file.endswith((".tsx", ".ts")):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Determine relative path back to lib
            rel_depth = os.path.relpath(root_dir, root).count(os.sep)
            prefix = "./" if rel_depth == 0 else "../" * rel_depth
            
            new_content = re.sub(r"['\"]@/lib/api['\"]", f"'{prefix}lib/api.ts'", content)
            new_content = re.sub(r"['\"]@/lib/api\.ts['\"]", f"'{prefix}lib/api.ts'", new_content)
            new_content = re.sub(r"['\"]@/lib/utils['\"]", f"'{prefix}lib/utils.ts'", new_content)
            new_content = re.sub(r"['\"]@/lib/nlp['\"]", f"'{prefix}lib/nlp.ts'", new_content)

            if content != new_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path}")
