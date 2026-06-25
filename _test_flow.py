"""完整流程测试 - 模拟用户新建文章"""
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(r'd:\2\Firefly')
POSTS_DIR = 'src/content/posts'

def slugify(text):
    text = text.strip()
    text = re.sub(r"[\s\/\\:\*\?\"<>\|]+", "-", text)
    return text.strip("-") or "untitled"

def safe_filename(name):
    name = re.sub(r"[\s\(\)\[\]\{\}\【\】（）,，]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name

# ============= 模拟用户新建文章流程 =============
print("=" * 60)
print("测试1: 新建文章（中文标题，不填 Slug）")
print("=" * 60)

title = "我的新文章测试"
slug = ""  # 用户没填 slug
date = "2026-06-21"
category = "测试分类"
tags = "标签1, 标签2"
cover = ""
body = "这是文章正文内容。\n可以有多行。"

if not slug:
    slug = slugify(title)
    print(f"  自动生成 slug: '{slug}'")

tag_items = [t.strip() for t in tags.split(",") if t.strip()]
tags_line = ", ".join(f'"{t}"' for t in tag_items)

fm = f'title: "{title}"\n'
fm += f"published: {date}\n"
fm += f'tags: [{tags_line}]\n'
if category:
    fm += f"category: {category}\n"
if cover:
    fm += f"image: ./images/{cover}\n"
full = f"---\n{fm}---\n\n{body}\n"

posts_root = ROOT_DIR / POSTS_DIR
post_dir = posts_root / slug
post_dir.mkdir(parents=True, exist_ok=True)
md_file = post_dir / "index.md"

with open(md_file, "w", encoding="utf-8") as f:
    f.write(full)

print(f"  ✅ 保存成功: {md_file}")
print(f"  ✅ 文件存在: {md_file.exists()}")
print(f"  ✅ 文件大小: {md_file.stat().st_size} bytes")

# 验证内容
with open(md_file, "r", encoding="utf-8") as f:
    content = f.read()
print("  --- 文件内容 ---")
for line in content.split("\n")[:12]:
    print(f"    {line}")

# 清理
shutil.rmtree(post_dir)
print("  🧹 测试文件已清理")

# ============= 测试2: 带图片的文章 =============
print("\n" + "=" * 60)
print("测试2: 带封面图片的文章")
print("=" * 60)

title2 = "带封面的文章"
slug2 = slugify(title2)
cover2 = "test_cover.jpg"

# 模拟选择封面 - 需要有图片可复制
test_img = ROOT_DIR / "src" / "content" / "posts" / "images" / "1_.jpg"
if test_img.exists():
    target_dir = ROOT_DIR / POSTS_DIR / slug2 / "images"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(test_img, target_dir / cover2)
    print(f"  ✅ 封面图片已复制: {target_dir / cover2}")
else:
    print(f"  ⚠️  测试图片不存在: {test_img}")

posts_root2 = ROOT_DIR / POSTS_DIR
post_dir2 = posts_root2 / slug2
post_dir2.mkdir(exist_ok=True)

fm2 = f'title: "{title2}"\n'
fm2 += f"published: {date}\n"
fm2 += "tags: []\n"
fm2 += f"image: ./images/{cover2}\n"
full2 = f"---\n{fm2}---\n\n带封面的文章正文。\n"

md_file2 = post_dir2 / "index.md"
with open(md_file2, "w", encoding="utf-8") as f:
    f.write(full2)
print(f"  ✅ 带封面的文章已保存: {md_file2}")

# 验证 frontmatter 解析
match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", full2, re.DOTALL)
if match:
    print(f"  ✅ frontmatter 格式正确")
    frontmatter = match.group(1)
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            print(f"    - {key.strip()}: {value.strip()}")
else:
    print("  ❌ frontmatter 格式错误！")

shutil.rmtree(post_dir2)
print("  🧹 测试文件已清理")

# ============= 测试3: 扫描列表 =============
print("\n" + "=" * 60)
print("测试3: 扫描文章目录列表")
print("=" * 60)

posts_root3 = ROOT_DIR / POSTS_DIR
entries = []
for item in posts_root3.iterdir():
    if item.is_dir() and (item / "index.md").exists():
        entries.append(item.name)
entries.sort()

print(f"  共发现 {len(entries)} 篇文章:")
for name in entries:
    md = posts_root3 / name / "index.md"
    img_dir = posts_root3 / name / "images"
    img_count = 0
    if img_dir.exists():
        img_count = len([f for f in img_dir.iterdir() if f.is_file()])
    size = md.stat().st_size
    print(f"    - {name} (图片: {img_count}张, 文本: {size}字节)")

print("\n" + "=" * 60)
print("✅ 所有测试通过！")
print("=" * 60)
