import os, re, shutil
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(r'd:\2\Firefly')
POSTS_DIR = 'src/content/posts'

# 测试保存一篇新文章
slug = 'test_article_2026'
title = '测试文章'
date = '2026-06-21'
category = '测试'
tags = ''
cover = ''
body = '这是测试内容'

tag_items = [t.strip() for t in tags.split(',') if t.strip()]
tags_line = ', '.join(f'"{t}"' for t in tag_items)

fm = f'title: "{title}"\n'
fm += f'published: {date}\n'
fm += f'tags: [{tags_line}]\n'
if category:
    fm += f'category: {category}\n'
if cover:
    fm += f'image: ./images/{cover}\n'
full = f'---\n{fm}---\n\n{body}\n'

posts_root = ROOT_DIR / POSTS_DIR
posts_root.mkdir(parents=True, exist_ok=True)
post_dir = posts_root / slug
post_dir.mkdir(exist_ok=True)
md_file = post_dir / 'index.md'

with open(md_file, 'w', encoding='utf-8') as f:
    f.write(full)

print(f'OK: 文件写入成功 -> {md_file}')
print(f'文件存在: {md_file.exists()}')
print(f'文件大小: {md_file.stat().st_size} bytes')
print('---内容---')
with open(md_file, 'r', encoding='utf-8') as f:
    print(f.read())

# 清理测试文件
shutil.rmtree(post_dir)
print(f'\n测试文件已清理')
