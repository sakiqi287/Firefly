#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firefly 博客管理工具
功能：管理文章、编辑文章、插入图片、设置封面等
"""

import os
import re
import json
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

# ================= 配置项 =================
POSTS_DIR = "src/content/posts"      # 文章存放目录
IMAGES_DIR = "src/content/posts/images"  # 文章图片存放目录

class BlogManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Firefly 博客管理工具")
        self.root.geometry("1200x800")
        
        # 确保目录存在
        os.makedirs(POSTS_DIR, exist_ok=True)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        
        self.current_file = None
        self.dirty = False
        
        self.create_widgets()
        self.load_posts_list()
        
    def create_widgets(self):
        # 顶部框架
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(top_frame, text="新建文章", command=self.new_post).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="保存", command=self.save_post).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="删除", command=self.delete_post).pack(side=tk.LEFT, padx=2)
        ttk.Button(top_frame, text="刷新", command=self.load_posts_list).pack(side=tk.LEFT, padx=2)
        
        # 主区域
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧：文章列表
        left_frame = ttk.Frame(main_frame, width=250)
        main_frame.add(left_frame, weight=0)
        
        ttk.Label(left_frame, text="文章列表", font=('', 12, 'bold')).pack(pady=5)
        self.posts_listbox = tk.Listbox(left_frame, width=30)
        self.posts_listbox.pack(fill=tk.BOTH, expand=True)
        self.posts_listbox.bind('<<ListboxSelect>>', self.on_post_select)
        
        # 右侧：编辑区
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=1)
        
        # 文章信息区
        info_frame = ttk.LabelFrame(right_frame, text="文章信息", padding=10)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text="标题:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.title_entry = ttk.Entry(info_frame, width=50)
        self.title_entry.grid(row=0, column=1, pady=2, padx=5)
        
        ttk.Label(info_frame, text="Slug:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.slug_entry = ttk.Entry(info_frame, width=50)
        self.slug_entry.grid(row=1, column=1, pady=2, padx=5)
        
        ttk.Label(info_frame, text="日期:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.date_entry = ttk.Entry(info_frame, width=50)
        self.date_entry.grid(row=2, column=1, pady=2, padx=5)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(info_frame, text="分类:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.category_entry = ttk.Entry(info_frame, width=50)
        self.category_entry.grid(row=3, column=1, pady=2, padx=5)
        
        ttk.Label(info_frame, text="标签:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.tags_entry = ttk.Entry(info_frame, width=50)
        self.tags_entry.grid(row=4, column=1, pady=2, padx=5)
        
        # 封面图片
        ttk.Label(info_frame, text="封面:").grid(row=5, column=0, sticky=tk.W, pady=2)
        cover_frame = ttk.Frame(info_frame)
        cover_frame.grid(row=5, column=1, sticky=tk.W, pady=2, padx=5)
        self.cover_entry = ttk.Entry(cover_frame, width=35)
        self.cover_entry.pack(side=tk.LEFT)
        ttk.Button(cover_frame, text="选择", command=self.select_cover).pack(side=tk.LEFT, padx=2)
        
        # 内容区
        content_frame = ttk.LabelFrame(right_frame, text="文章内容 (Markdown)", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD, width=80, height=25)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # 插入图片按钮
        img_frame = ttk.Frame(right_frame)
        img_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(img_frame, text="插入图片", command=self.insert_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(img_frame, text="插入标题", command=self.insert_heading).pack(side=tk.LEFT, padx=2)
        ttk.Button(img_frame, text="插入链接", command=self.insert_link).pack(side=tk.LEFT, padx=2)
        
    def safe_filename(self, filename):
        """将文件名转换为安全格式"""
        # 替换空格、括号等特殊字符
        filename = re.sub(r'[\s\(\)\[\]]', '_', filename)
        filename = re.sub(r'_+', '_', filename)  # 多个下划线合并
        return filename
        
    def load_posts_list(self):
        """加载文章列表"""
        self.posts_listbox.delete(0, tk.END)
        posts_dir = Path(POSTS_DIR)
        
        for item in posts_dir.iterdir():
            if item.is_dir() and (item / 'index.md').exists():
                self.posts_listbox.insert(tk.END, item.name)
            elif item.suffix == '.md':
                name = item.stem
                self.posts_listbox.insert(tk.END, name)
                
    def on_post_select(self, event):
        """选择文章"""
        selection = self.posts_listbox.curselection()
        if not selection:
            return
            
        post_name = self.posts_listbox.get(selection[0])
        self.load_post(post_name)
        
    def load_post(self, post_name):
        """加载文章内容"""
        posts_dir = Path(POSTS_DIR)
        md_file = posts_dir / post_name / 'index.md'
        
        if not md_file.exists():
            md_file = posts_dir / f"{post_name}.md"
            
        if not md_file.exists():
            messagebox.showerror("错误", f"找不到文章文件: {post_name}")
            return
            
        self.current_file = md_file
        
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 解析 frontmatter
        self.parse_frontmatter(content)
        
    def parse_frontmatter(self, content):
        """解析 frontmatter"""
        match = re.match(r'^---\n(.*?)\n---(.*)$', content, re.DOTALL)
        if not match:
            self.title_entry.delete(0, tk.END)
            self.slug_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.category_entry.delete(0, tk.END)
            self.tags_entry.delete(0, tk.END)
            self.cover_entry.delete(0, tk.END)
            self.content_text.delete(1.0, tk.END)
            self.content_text.insert(1.0, content)
            return
            
        frontmatter = match.group(1)
        body = match.group(2).strip()
        
        # 解析各字段
        self.title_entry.delete(0, tk.END)
        self.slug_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        self.tags_entry.delete(0, tk.END)
        self.cover_entry.delete(0, tk.END)
        
        for line in frontmatter.split('\n'):
            if line.startswith('title:'):
                self.title_entry.insert(0, line.split(':', 1)[1].strip().strip('"').strip("'"))
            elif line.startswith('published:'):
                self.date_entry.insert(0, line.split(':', 1)[1].strip())
            elif line.startswith('date:'):
                self.date_entry.insert(0, line.split(':', 1)[1].strip())
            elif line.startswith('tags:'):
                tags_str = line.split(':', 1)[1].strip()
                tags = re.findall(r'"([^"]+)"', tags_str)
                self.tags_entry.insert(0, ', '.join(tags))
            elif line.startswith('category:'):
                self.category_entry.insert(0, line.split(':', 1)[1].strip().strip('"').strip("'"))
            elif line.startswith('image:'):
                img_path = line.split(':', 1)[1].strip().strip('"').strip("'")
                img_name = os.path.basename(img_path)
                self.cover_entry.insert(0, img_name)
            elif line.startswith('cover:'):
                img_path = line.split(':', 1)[1].strip().strip('"').strip("'")
                img_name = os.path.basename(img_path)
                self.cover_entry.insert(0, img_name)
                
        # 从路径获取 slug
        if self.current_file:
            self.slug_entry.delete(0, tk.END)
            self.slug_entry.insert(0, self.current_file.parent.name if self.current_file.suffix == '.md' else self.current_file.stem)
                
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, body)
        
    def new_post(self):
        """新建文章"""
        self.current_file = None
        self.title_entry.delete(0, tk.END)
        self.slug_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.category_entry.delete(0, tk.END)
        self.tags_entry.delete(0, tk.END)
        self.cover_entry.delete(0, tk.END)
        self.content_text.delete(1.0, tk.END)
        
    def save_post(self):
        """保存文章"""
        title = self.title_entry.get().strip()
        slug = self.slug_entry.get().strip()
        date = self.date_entry.get().strip()
        category = self.category_entry.get().strip()
        tags = self.tags_entry.get().strip()
        cover = self.cover_entry.get().strip()
        content = self.content_text.get(1.0, tk.END).strip()
        
        if not title:
            messagebox.showerror("错误", "请输入标题")
            return
        if not slug:
            slug = title  # 如果没有 slug，用标题代替
            
        # 构建 frontmatter
        tags_str = ', '.join([f'"{t.strip()}"' for t in tags.split(',') if t.strip()])
        
        frontmatter = f"""---
title: "{title}"
published: {date}
tags: [{tags_str}]
"""
        if category:
            frontmatter += f"category: {category}\n"
        if cover:
            frontmatter += f"image: ./images/{cover}\n"
            
        frontmatter += "---\n\n"
        
        full_content = frontmatter + content
        
        # 保存文件
        posts_dir = Path(POSTS_DIR)
        post_dir = posts_dir / slug
        
        if post_dir.exists() or (posts_dir / f"{slug}.md").exists():
            # 更新现有文章
            if post_dir.exists():
                md_file = post_dir / 'index.md'
            else:
                md_file = posts_dir / f"{slug}.md"
        else:
            # 新建文章
            post_dir.mkdir(exist_ok=True)
            md_file = post_dir / 'index.md'
            
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
            
        self.current_file = md_file
        messagebox.showinfo("成功", f"文章已保存: {md_file}")
        self.load_posts_list()
        
    def delete_post(self):
        """删除文章"""
        if not self.current_file:
            selection = self.posts_listbox.curselection()
            if not selection:
                messagebox.showwarning("警告", "请先选择要删除的文章")
                return
            post_name = self.posts_listbox.get(selection[0])
            posts_dir = Path(POSTS_DIR)
            post_dir = posts_dir / post_name
            md_file = post_dir / 'index.md'
            if not md_file.exists():
                md_file = posts_dir / f"{post_name}.md"
        else:
            post_dir = self.current_file.parent
            md_file = self.current_file
            
        if not md_file.exists():
            messagebox.showerror("错误", "找不到文章文件")
            return
            
        if messagebox.askyesno("确认", f"确定要删除文章吗？\n{md_file}"):
            try:
                # 如果是目录，删除整个目录
                if post_dir.is_dir():
                    shutil.rmtree(post_dir)
                else:
                    post_dir.unlink()
                messagebox.showinfo("成功", "文章已删除")
                self.new_post()
                self.load_posts_list()
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")
                
    def get_post_images_dir(self):
        """获取当前文章的 images 目录路径"""
        slug = self.slug_entry.get().strip() or self.title_entry.get().strip()
        if not slug:
            return None
        return Path(POSTS_DIR) / slug / 'images'
        
    def select_cover(self):
        """选择封面图片"""
        filename = filedialog.askopenfilename(
            title="选择封面图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.webp"), ("所有文件", "*.*")]
        )
        if filename:
            # 复制图片到文章自己的 images 目录
            basename = os.path.basename(filename)
            safe_basename = self.safe_filename(basename)
            post_images_dir = self.get_post_images_dir()
            if not post_images_dir:
                messagebox.showerror("错误", "请先输入文章标题")
                return
            os.makedirs(post_images_dir, exist_ok=True)
            dest = post_images_dir / safe_basename
            shutil.copy2(filename, dest)
            self.cover_entry.delete(0, tk.END)
            self.cover_entry.insert(0, safe_basename)
            
    def insert_image(self):
        """插入图片"""
        filename = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.webp"), ("所有文件", "*.*")]
        )
        if filename:
            # 复制图片到文章自己的 images 目录
            basename = os.path.basename(filename)
            safe_basename = self.safe_filename(basename)
            post_images_dir = self.get_post_images_dir()
            if not post_images_dir:
                messagebox.showerror("错误", "请先输入文章标题")
                return
            os.makedirs(post_images_dir, exist_ok=True)
            dest = post_images_dir / safe_basename
            shutil.copy2(filename, dest)
            
            # 在光标位置插入 Markdown 图片语法
            img_markdown = f"\n![{safe_basename}](./images/{safe_basename})\n"
            self.content_text.insert(tk.INSERT, img_markdown)
            
    def insert_heading(self):
        """插入标题"""
        heading_markdown = "\n## 标题\n"
        self.content_text.insert(tk.INSERT, heading_markdown)
        
    def insert_link(self):
        """插入链接"""
        link_markdown = "\n[链接文本](https://)\n"
        self.content_text.insert(tk.INSERT, link_markdown)


if __name__ == "__main__":
    root = tk.Tk()
    app = BlogManager(root)
    root.mainloop()
