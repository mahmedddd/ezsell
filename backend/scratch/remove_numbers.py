import re

with open('build_master_doc.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find h3(doc, '8.x.x Some Title') and replace with h3(doc, 'Some Title')
# e.g., h3(doc, '8.1.1 M1 — Profile Management Tests') -> h3(doc, 'M1 — Profile Management Tests')
# We match h3(doc, 'NUMBER.NUMBER.NUMBER(optional more) Title')
new_content = re.sub(r"h3\(doc,\s*'\d+\.\d+\.\d+(?:\.\d+)?\s+(.*?)'\)", r"h3(doc, '\1')", content)

with open('build_master_doc.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
