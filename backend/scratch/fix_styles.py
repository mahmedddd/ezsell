content = open(r'backend\scratch\build_doc_p1.py', encoding='utf-8').read()
content = content.replace("'List Bullet'", "'List Paragraph'")
open(r'backend\scratch\build_doc_p1.py', 'w', encoding='utf-8').write(content)
print('Done')
