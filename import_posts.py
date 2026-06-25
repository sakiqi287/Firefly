import os
import csv
import json
import shutil
import argparse
from datetime import datetime
from pathlib import Path

POSTS_DIR = "src/content/posts"
ASSETS_DIR = "src/assets/images"

def generate_slug(title):
    import re
    slug = re.sub(r'[^\w\s-]', '', title).strip().lower()
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug

def create_post(title, content, published=None, description="", image=None, tags=[], category="", draft=False):
    os.makedirs(POSTS_DIR, exist_ok=True)
    
    if published is None:
        published = datetime.now().strftime("%Y-%m-%d")
    
    slug = generate_slug(title)
    date_str = published
    
    tags_str = ", ".join([f'"{tag.strip()}"' for tag in tags if tag.strip()])
    
    image_md = ""
    image_frontmatter = ""
    if image:
        if os.path.exists(image):
            os.makedirs(ASSETS_DIR, exist_ok=True)
            dest = os.path.join(ASSETS_DIR, os.path.basename(image))
            shutil.copy2(image, dest)
            image_frontmatter = f"image: /cover/{os.path.basename(image)}"
            image_md = f"\n![cover](/assets/images/{os.path.basename(image)})\n"
        else:
            print(f"警告：图片 {image} 不存在")
    
    frontmatter = f"""---
title: "{title}"
published: {date_str}
description: "{description}"
{image_frontmatter}
tags: [{tags_str}]
category: "{category}"
draft: {str(draft).lower()}
---

"""
    
    md_content = frontmatter + content + image_md
    
    post_dir = os.path.join(POSTS_DIR, slug)
    os.makedirs(post_dir, exist_ok=True)
    
    file_path = os.path.join(post_dir, "index.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"[+] 文章 '{title}' 已创建: {file_path}")
    return file_path

def import_from_csv(csv_path):
    if not os.path.exists(csv_path):
        print(f"错误：文件 {csv_path} 不存在")
        return
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('title', '').strip()
            if not title:
                continue
            
            content = row.get('content', '')
            published = row.get('published', datetime.now().strftime("%Y-%m-%d"))
            description = row.get('description', '')
            image = row.get('image', '')
            tags = row.get('tags', '').split(',') if row.get('tags') else []
            category = row.get('category', '')
            draft = row.get('draft', 'false').lower() == 'true'
            
            create_post(title, content, published, description, image, tags, category, draft)

def import_from_json(json_path):
    if not os.path.exists(json_path):
        print(f"错误：文件 {json_path} 不存在")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        for post in data:
            create_post(
                title=post.get('title', ''),
                content=post.get('content', ''),
                published=post.get('published'),
                description=post.get('description', ''),
                image=post.get('image', ''),
                tags=post.get('tags', []),
                category=post.get('category', ''),
                draft=post.get('draft', False)
            )
    elif isinstance(data, dict):
        create_post(
            title=data.get('title', ''),
            content=data.get('content', ''),
            published=data.get('published'),
            description=data.get('description', ''),
            image=data.get('image', ''),
            tags=data.get('tags', []),
            category=data.get('category', ''),
            draft=data.get('draft', False)
        )

def import_from_md_files(source_dir):
    if not os.path.exists(source_dir):
        print(f"错误：目录 {source_dir} 不存在")
        return
    
    for filename in os.listdir(source_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(source_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            frontmatter = {}
            in_frontmatter = False
            content_start = 0
            
            for i, line in enumerate(lines):
                if line.strip() == '---':
                    if in_frontmatter:
                        content_start = i + 1
                        break
                    in_frontmatter = True
                elif in_frontmatter:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip().strip('"').strip("'")
            
            title = frontmatter.get('title', os.path.splitext(filename)[0])
            content = '\n'.join(lines[content_start:])
            
            create_post(
                title=title,
                content=content,
                published=frontmatter.get('published'),
                description=frontmatter.get('description', ''),
                image=frontmatter.get('image', ''),
                tags=frontmatter.get('tags', '').strip('[]').split(',') if frontmatter.get('tags') else [],
                category=frontmatter.get('category', ''),
                draft=frontmatter.get('draft', 'false').lower() == 'true'
            )

def generate_sample_csv(output_path="sample_posts.csv"):
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['title', 'content', 'published', 'description', 'image', 'tags', 'category', 'draft'])
        writer.writerow(['我的第一篇文章', '这是文章的内容。\n\n支持多行内容。', '2025-01-01', '文章描述', '', '技术,开发', '前端开发', 'false'])
        writer.writerow(['Python 学习笔记', 'Python 是一门很棒的语言。', '2025-01-02', 'Python 教程', '', 'Python,编程', '技术', 'false'])
    
    print(f"[+] 示例 CSV 文件已生成: {output_path}")

def generate_sample_json(output_path="sample_posts.json"):
    posts = [
        {
            "title": "我的第一篇文章",
            "content": "这是文章的内容。\n\n支持多行内容。",
            "published": "2025-01-01",
            "description": "文章描述",
            "image": "",
            "tags": ["技术", "开发"],
            "category": "前端开发",
            "draft": False
        },
        {
            "title": "Python 学习笔记",
            "content": "Python 是一门很棒的语言。",
            "published": "2025-01-02",
            "description": "Python 教程",
            "image": "",
            "tags": ["Python", "编程"],
            "category": "技术",
            "draft": False
        }
    ]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
    
    print(f"[+] 示例 JSON 文件已生成: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Fuwari 博客文章导入工具')
    parser.add_argument('--csv', help='从 CSV 文件导入文章')
    parser.add_argument('--json', help='从 JSON 文件导入文章')
    parser.add_argument('--md', help='从 Markdown 目录导入文章')
    parser.add_argument('--gen-csv', action='store_true', help='生成示例 CSV 文件')
    parser.add_argument('--gen-json', action='store_true', help='生成示例 JSON 文件')
    
    args = parser.parse_args()
    
    if args.gen_csv:
        generate_sample_csv()
    elif args.gen_json:
        generate_sample_json()
    elif args.csv:
        import_from_csv(args.csv)
    elif args.json:
        import_from_json(args.json)
    elif args.md:
        import_from_md_files(args.md)
    else:
        print("用法:")
        print("  python import_posts.py --csv <csv文件>        # 从 CSV 文件导入")
        print("  python import_posts.py --json <json文件>      # 从 JSON 文件导入")
        print("  python import_posts.py --md <目录>            # 从 Markdown 目录导入")
        print("  python import_posts.py --gen-csv              # 生成示例 CSV")
        print("  python import_posts.py --gen-json             # 生成示例 JSON")

if __name__ == "__main__":
    main()
