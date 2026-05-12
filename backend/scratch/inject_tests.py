import re

with open('new_tests.py', 'r', encoding='utf-8') as f:
    new_content = f.read()

with open('build_master_doc.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
for i, line in enumerate(lines):
    if line.strip() == '# ══════════════════════════════════════════════════════════════════════════════':
        if i + 1 < len(lines) and 'CHAPTER 6 – TESTING AND EVALUATION' in lines[i+1]:
            start_idx = i
            break

# We will keep the conclusion section which is currently:
# # ══════════════════════════════════════════════════════════════════════════════
# # CHAPTER 7 & 8 – CONCLUSION & REFERENCES
# # ══════════════════════════════════════════════════════════════════════════════
end_idx = -1
for i in range(start_idx + 1 if start_idx != -1 else 0, len(lines)):
    if 'CHAPTER 7 & 8' in lines[i]:
        end_idx = i - 1
        break

if start_idx != -1 and end_idx != -1:
    new_file_lines = lines[:start_idx] + [new_content + '\n'] + lines[end_idx:]
    with open('build_master_doc.py', 'w', encoding='utf-8') as f:
        f.writelines(new_file_lines)
    print("Replaced testing section successfully.")
else:
    print("Could not find start/end indices.", start_idx, end_idx)
