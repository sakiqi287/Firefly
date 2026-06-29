# -*- coding: utf-8 -*-
"""
Firefly 博客管理工具
用于添加、编辑和删除博客文章
"""

import os
import sys
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import shutil
import subprocess

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def compress_and_copy_image(src, dest, max_dimension=1920, quality=80):
    if HAS_PIL:
        try:
            img = Image.open(src)
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            width, height = img.size
            if max(img.size) > max_dimension:
                ratio = max_dimension / max(width, height)
                new_size = (int(width * ratio), int(height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            img.save(dest, 'JPEG', quality=quality, optimize=True)
            return True
        except Exception:
            pass
    shutil.copy2(src, dest)
    return False


POSTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'posts')
GIT_REMOTE = "https://github.com/sakiqi287/Firefly.git"


COLORS = {
    'bg': '#f8fafc',
    'card': '#ffffff',
    'primary': '#6366f1',
    'primary_hover': '#4f46e5',
    'secondary': '#f1f5f9',
    'text': '#1e293b',
    'text_secondary': '#64748b',
    'border': '#e2e8f0',
    'success': '#10b981',
    'danger': '#ef4444',
    'warning': '#f59e0b',
}


def apply_modern_style(root):
    style = ttk.Style(root)
    
    try:
        style.theme_use('clam')
    except Exception:
        pass
    
    style.configure('.', 
        background=COLORS['bg'],
        foreground=COLORS['text'],
        fieldbackground=COLORS['card'],
        bordercolor=COLORS['border'],
        lightcolor=COLORS['border'],
        darkcolor=COLORS['border'],
    )
    
    style.configure('TFrame', background=COLORS['bg'])
    style.configure('Card.TFrame', 
        background=COLORS['card'],
        relief='flat',
    )
    
    style.configure('TLabel', 
        background=COLORS['bg'],
        foreground=COLORS['text'],
        font=('Microsoft YaHei UI', 10)
    )
    style.configure('Title.TLabel',
        background=COLORS['bg'],
        foreground=COLORS['text'],
        font=('Microsoft YaHei UI', 18, 'bold')
    )
    style.configure('Subtitle.TLabel',
        background=COLORS['bg'],
        foreground=COLORS['text_secondary'],
        font=('Microsoft YaHei UI', 10)
    )
    style.configure('CardTitle.TLabel',
        background=COLORS['card'],
        foreground=COLORS['text'],
        font=('Microsoft YaHei UI', 11, 'bold')
    )
    style.configure('Hint.TLabel',
        background=COLORS['bg'],
        foreground=COLORS['text_secondary'],
        font=('Microsoft YaHei UI', 9)
    )
    style.configure('Path.TLabel',
        background=COLORS['card'],
        foreground=COLORS['primary'],
        font=('Microsoft YaHei UI', 9)
    )
    style.configure('Status.TLabel',
        background=COLORS['secondary'],
        foreground=COLORS['text_secondary'],
        font=('Microsoft YaHei UI', 9)
    )
    
    style.configure('TEntry',
        fieldbackground=COLORS['card'],
        foreground=COLORS['text'],
        bordercolor=COLORS['border'],
        lightcolor=COLORS['border'],
        darkcolor=COLORS['border'],
        padding=8,
        font=('Microsoft YaHei UI', 10)
    )
    style.map('TEntry',
        bordercolor=[('focus', COLORS['primary'])],
        lightcolor=[('focus', COLORS['primary'])],
        darkcolor=[('focus', COLORS['primary'])],
    )
    
    style.configure('TButton',
        background=COLORS['secondary'],
        foreground=COLORS['text'],
        bordercolor=COLORS['border'],
        lightcolor=COLORS['secondary'],
        darkcolor=COLORS['secondary'],
        padding=(16, 8),
        font=('Microsoft YaHei UI', 10)
    )
    style.map('TButton',
        background=[('active', '#e2e8f0'), ('pressed', '#cbd5e1')],
    )
    
    style.configure('Primary.TButton',
        background=COLORS['primary'],
        foreground='#ffffff',
        bordercolor=COLORS['primary'],
        lightcolor=COLORS['primary'],
        darkcolor=COLORS['primary'],
        padding=(18, 9),
        font=('Microsoft YaHei UI', 10, 'bold')
    )
    style.map('Primary.TButton',
        background=[('active', COLORS['primary_hover']), ('pressed', '#4338ca')],
        bordercolor=[('active', COLORS['primary_hover']), ('pressed', '#4338ca')],
        lightcolor=[('active', COLORS['primary_hover']), ('pressed', '#4338ca')],
        darkcolor=[('active', COLORS['primary_hover']), ('pressed', '#4338ca')],
    )
    
    style.configure('Danger.TButton',
        background=COLORS['danger'],
        foreground='#ffffff',
        bordercolor=COLORS['danger'],
        lightcolor=COLORS['danger'],
        darkcolor=COLORS['danger'],
        padding=(16, 8),
        font=('Microsoft YaHei UI', 10)
    )
    style.map('Danger.TButton',
        background=[('active', '#dc2626'), ('pressed', '#b91c1c')],
    )
    
    style.configure('Success.TButton',
        background=COLORS['success'],
        foreground='#ffffff',
        bordercolor=COLORS['success'],
        lightcolor=COLORS['success'],
        darkcolor=COLORS['success'],
        padding=(16, 8),
        font=('Microsoft YaHei UI', 10)
    )
    style.map('Success.TButton',
        background=[('active', '#059669'), ('pressed', '#047857')],
    )
    
    style.configure('TLabelframe',
        background=COLORS['bg'],
        foreground=COLORS['text'],
        bordercolor=COLORS['border'],
        relief='solid',
        borderwidth=1
    )
    style.configure('TLabelframe.Label',
        background=COLORS['bg'],
        foreground=COLORS['text_secondary'],
        font=('Microsoft YaHei UI', 10, 'bold')
    )
    
    style.configure('Treeview',
        background=COLORS['card'],
        foreground=COLORS['text'],
        fieldbackground=COLORS['card'],
        bordercolor=COLORS['border'],
        rowheight=36,
        font=('Microsoft YaHei UI', 10)
    )
    style.configure('Treeview.Heading',
        background=COLORS['secondary'],
        foreground=COLORS['text_secondary'],
        font=('Microsoft YaHei UI', 10, 'bold'),
        padding=8
    )
    style.map('Treeview',
        background=[('selected', COLORS['primary'])],
        foreground=[('selected', '#ffffff')],
    )
    
    style.configure('TScrollbar',
        background=COLORS['bg'],
        troughcolor=COLORS['bg'],
        bordercolor=COLORS['bg'],
        arrowcolor=COLORS['text_secondary'],
    )
    
    style.configure('TCheckbutton',
        background=COLORS['bg'],
        foreground=COLORS['text'],
        font=('Microsoft YaHei UI', 10)
    )
    
    style.configure('Card.TLabelframe',
        background=COLORS['card'],
        foreground=COLORS['text'],
        bordercolor=COLORS['border'],
        relief='solid',
        borderwidth=1
    )
    style.configure('Card.TLabelframe.Label',
        background=COLORS['card'],
        foreground=COLORS['primary'],
        font=('Microsoft YaHei UI', 11, 'bold')
    )


class BlogManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firefly 博客管理工具")
        self.root.geometry("820x700")
        self.root.resizable(True, True)
        self.root.minsize(600, 500)
        self.root.configure(bg=COLORS['bg'])
        
        apply_modern_style(root)
        
        self.posts = []
        self.load_posts()
        self.create_ui()
    
    def load_posts(self):
        self.posts = []
        if os.path.exists(POSTS_DIR):
            for name in os.listdir(POSTS_DIR):
                post_path = os.path.join(POSTS_DIR, name)
                if os.path.isdir(post_path):
                    index_file = os.path.join(post_path, 'index.md')
                    if os.path.exists(index_file):
                        self.posts.append(name)
    
    def create_ui(self):
        header = ttk.Frame(self.root, style='Card.TFrame', padding=(16, 8))
        header.pack(fill=tk.X)
        
        ttk.Button(header, text="🔄 刷新", command=self.refresh_posts).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(header, text="📤 Git 推送", command=self.git_push, style='Primary.TButton').pack(side=tk.RIGHT)
        
        body = ttk.Frame(self.root, padding=(20, 16))
        body.pack(fill=tk.BOTH, expand=True)
        
        list_card = ttk.Frame(body, style='Card.TFrame')
        list_card.pack(fill=tk.BOTH, expand=True)
        
        list_header = ttk.Frame(list_card, style='Card.TFrame', padding=(16, 14))
        list_header.pack(fill=tk.X)
        ttk.Label(list_header, text="📚 文章列表", style='CardTitle.TLabel').pack(side=tk.LEFT)
        ttk.Label(list_header, text=f"共 {len(self.posts)} 篇", style='Hint.TLabel').pack(side=tk.RIGHT)
        
        tree_frame = ttk.Frame(list_card, style='Card.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        
        columns = ('name', 'date')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        self.tree.heading('name', text='文章名称')
        self.tree.heading('date', text='日期')
        self.tree.column('name', width=400)
        self.tree.column('date', width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.populate_tree()
        self.tree.bind('<Double-1>', lambda e: self.edit_post())
        
        btn_frame = ttk.Frame(body, padding=(0, 16, 0, 0))
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="➕ 新建文章", command=self.add_post, style='Primary.TButton').pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="✏️ 编辑", command=self.edit_post).pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="🗑️ 删除", command=self.delete_post, style='Danger.TButton').pack(side=tk.LEFT, padx=4)
        ttk.Button(btn_frame, text="📂 打开目录", command=self.open_posts_dir).pack(side=tk.LEFT, padx=4)
        
        status_bar = ttk.Frame(self.root, style='Card.TFrame', padding=(16, 10))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="准备就绪")
        ttk.Label(status_bar, textvariable=self.status_var, style='Hint.TLabel').pack(side=tk.LEFT)
        ttk.Label(status_bar, text="双击文章可快速编辑", style='Hint.TLabel').pack(side=tk.RIGHT)
    
    def populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        post_dates = {}
        for name in sorted(self.posts):
            date_str = self._get_post_date(name)
            post_dates[name] = date_str
        
        for i, name in enumerate(sorted(self.posts, key=lambda x: post_dates.get(x, ''), reverse=True)):
            self.tree.insert('', tk.END, values=(name, post_dates.get(name, '-')))
    
    def _get_post_date(self, slug):
        index_file = os.path.join(POSTS_DIR, slug, 'index.md')
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                data = self.parse_frontmatter(content)
                return data.get('published', data.get('date', '-'))
            except Exception:
                pass
        return '-'
    
    def refresh_posts(self):
        self.load_posts()
        self.populate_tree()
        self.status_var.set(f"已刷新，共 {len(self.posts)} 篇文章")
    
    def parse_frontmatter(self, content):
        data = {}
        if content.startswith('---'):
            end_idx = content.find('\n---\n', 4)
            if end_idx != -1:
                frontmatter = content[4:end_idx]
                lines = frontmatter.split('\n')
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        if value.startswith('[') and not value.endswith(']'):
                            array_content = value
                            j = i + 1
                            while j < len(lines) and not array_content.endswith(']'):
                                array_content += '\n' + lines[j].strip()
                                j += 1
                            i = j
                            value = array_content
                        elif value.startswith('"') and not value.endswith('"'):
                            str_content = value
                            j = i + 1
                            while j < len(lines) and not str_content.endswith('"'):
                                str_content += '\n' + lines[j].strip()
                                j += 1
                            i = j
                        data[key] = value
                    i += 1
        return data
    
    def add_post(self, post_name=None):
        is_edit = post_name is not None
        
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑文章" if is_edit else "新建文章")
        dialog.geometry("950x700")
        dialog.minsize(800, 550)
        dialog.configure(bg=COLORS['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_canvas = tk.Canvas(dialog, bg=COLORS['bg'], highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas, style='TFrame')
        
        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
        main_scrollbar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        
        defaults = {
            'title': '',
            'slug': '',
            'date': datetime.now().strftime("%Y-%m-%d"),
            'category': '',
            'tags': '',
            'description': '',
            'cover': '',
            'content': '',
            'draft': False,
            'pinned': False,
        }
        
        if is_edit:
            post_dir = os.path.join(POSTS_DIR, post_name)
            index_file = os.path.join(post_dir, 'index.md')
            if os.path.exists(index_file):
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                data = self.parse_frontmatter(content)
                
                defaults['title'] = data.get('title', '').strip('"')
                defaults['slug'] = post_name
                defaults['date'] = data.get('published', datetime.now().strftime("%Y-%m-%d"))
                defaults['category'] = data.get('category', '').strip('"')
                
                tags_str = data.get('tags', '')
                if tags_str.startswith('[') and tags_str.endswith(']'):
                    tags_str = tags_str[1:-1].strip()
                    tags = [t.strip().strip('"') for t in tags_str.split(',')]
                    defaults['tags'] = ', '.join(tags)
                else:
                    defaults['tags'] = tags_str.strip('"')
                
                defaults['description'] = data.get('description', '').strip('"')
                defaults['cover'] = data.get('image', '').strip('"')
                defaults['draft'] = data.get('draft', 'false').lower() == 'true'
                defaults['pinned'] = data.get('pinned', 'false').lower() == 'true'
                
                if content.startswith('---'):
                    end_idx = content.find('\n---\n', 4)
                    if end_idx != -1:
                        defaults['content'] = content[end_idx + 5:].strip()
                else:
                    defaults['content'] = content.strip()
        
        split_frame = ttk.Frame(main_frame, style='TFrame')
        split_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = ttk.Frame(split_frame, style='TFrame', width=360)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        left_panel.pack_propagate(False)
        
        info_frame = ttk.LabelFrame(left_panel, text="  基本信息  ", style='Card.TLabelframe', padding=14)
        info_frame.pack(fill=tk.X, pady=(0, 12))
        
        row = 0
        ttk.Label(info_frame, text="标题", style='CardTitle.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        title_entry = ttk.Entry(info_frame)
        title_entry.insert(0, defaults['title'])
        title_entry.grid(row=row, column=1, sticky=tk.EW, pady=(0, 10))
        
        row += 1
        ttk.Label(info_frame, text="Slug", style='CardTitle.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        slug_wrap = ttk.Frame(info_frame, style='Card.TFrame')
        slug_wrap.grid(row=row, column=1, sticky=tk.EW, pady=(0, 10))
        slug_entry = ttk.Entry(slug_wrap)
        slug_entry.insert(0, defaults['slug'])
        slug_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if is_edit:
            slug_entry.config(state='readonly')
        
        def gen_slug_from_title():
            if is_edit:
                messagebox.showwarning("提示", "编辑模式下不能修改 Slug")
                return
            title = title_entry.get().strip()
            if title:
                s = title.strip().replace(' ', '-')
                s = re.sub(r'[\\/:*?"<>|]', '', s)
                slug_entry.delete(0, tk.END)
                slug_entry.insert(0, s)
                update_path_label()
            else:
                messagebox.showwarning("提示", "请先填写标题")
        
        ttk.Button(slug_wrap, text="生成", command=gen_slug_from_title, width=6).pack(side=tk.LEFT, padx=(6, 0))
        
        row += 1
        path_label = ttk.Label(info_frame, text="保存路径: （请先填写标题或 Slug）", style='Path.TLabel')
        path_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))
        
        def update_path_label(*args):
            slug = slug_entry.get().strip() or title_entry.get().strip()
            if slug:
                path_label.config(text=f"📁 src/content/posts/{slug}/index.md")
            else:
                path_label.config(text="📁 保存路径: （请先填写标题或 Slug）")
        
        title_entry.bind("<KeyRelease>", update_path_label)
        slug_entry.bind("<KeyRelease>", update_path_label)
        update_path_label()
        
        row += 1
        ttk.Label(info_frame, text="日期", style='CardTitle.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        date_entry = ttk.Entry(info_frame)
        date_entry.insert(0, defaults['date'])
        date_entry.grid(row=row, column=1, sticky=tk.EW, pady=(0, 10))
        
        row += 1
        ttk.Label(info_frame, text="分类", style='CardTitle.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        category_entry = ttk.Entry(info_frame)
        category_entry.insert(0, defaults['category'])
        category_entry.grid(row=row, column=1, sticky=tk.EW, pady=(0, 10))
        
        row += 1
        ttk.Label(info_frame, text="标签", style='CardTitle.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        tags_entry = ttk.Entry(info_frame)
        tags_entry.insert(0, defaults['tags'])
        tags_entry.grid(row=row, column=1, sticky=tk.EW, pady=(0, 6))
        ttk.Label(info_frame, text="逗号分隔", style='Hint.TLabel').grid(row=row+1, column=1, sticky=tk.W)
        
        row += 2
        ttk.Label(info_frame, text="封面", style='CardTitle.TLabel').grid(row=row, column=0, sticky=tk.W, pady=(0, 4))
        cover_wrap = ttk.Frame(info_frame, style='Card.TFrame')
        cover_wrap.grid(row=row, column=1, sticky=tk.EW, pady=(0, 10))
        cover_entry = ttk.Entry(cover_wrap)
        cover_entry.insert(0, defaults['cover'])
        cover_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        cover_info = {"path": ""}
        
        def select_cover():
            filepath = filedialog.askopenfilename(
                title="选择封面图片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"), ("所有文件", "*.*")]
            )
            if filepath:
                cover_info["path"] = filepath
                filename = os.path.basename(filepath)
                safe_name = re.sub(r'[\s()\[\]{}]+', '_', filename)
                safe_name = re.sub(r'_+', '_', safe_name)
                cover_entry.delete(0, tk.END)
                cover_entry.insert(0, f"./images/{safe_name}")
        
        ttk.Button(cover_wrap, text="选择", command=select_cover, width=6).pack(side=tk.LEFT, padx=(6, 0))
        
        row += 1
        opt_frame = ttk.Frame(info_frame, style='Card.TFrame')
        opt_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(8, 0))
        
        draft_var = tk.BooleanVar(value=defaults['draft'])
        pinned_var = tk.BooleanVar(value=defaults['pinned'])
        
        ttk.Checkbutton(opt_frame, text="草稿", variable=draft_var).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Checkbutton(opt_frame, text="置顶", variable=pinned_var).pack(side=tk.LEFT)
        
        info_frame.columnconfigure(1, weight=1)
        
        btn_frame = ttk.Frame(left_panel, style='TFrame')
        btn_frame.pack(fill=tk.X)
        
        def do_save():
            title = title_entry.get().strip()
            slug = slug_entry.get().strip()
            date_str = date_entry.get().strip()
            category = category_entry.get().strip()
            tags_raw = tags_entry.get().strip()
            description = ''
            cover = cover_entry.get().strip()
            content = content_text.get("1.0", tk.END).strip()
            draft = draft_var.get()
            pinned = pinned_var.get()
            
            if not title:
                messagebox.showerror("错误", "请填写标题")
                return
            if not slug:
                s = title.strip().replace(' ', '-')
                s = re.sub(r'[\\/:*?"<>|]', '', s)
                slug = s
            
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            folder_name = slug
            post_dir = os.path.join(POSTS_DIR, folder_name)
            os.makedirs(post_dir, exist_ok=True)
            images_dir = os.path.join(post_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            cover_value = cover
            if cover_info["path"] and cover:
                try:
                    cover_filename = os.path.basename(cover_info["path"])
                    safe_cover_name = re.sub(r'[\s()\[\]{}]+', '_', cover_filename)
                    safe_cover_name = re.sub(r'_+', '_', safe_cover_name)
                    dest = os.path.join(images_dir, safe_cover_name)
                    compress_and_copy_image(cover_info["path"], dest)
                    cover_value = f"./images/{safe_cover_name}"
                except Exception as e:
                    messagebox.showwarning("提示", f"封面复制失败: {e}")
            
            lines = []
            lines.append('---')
            lines.append(f'title: "{title}"')
            lines.append(f'published: {date_str}')
            if description:
                lines.append(f'description: "{description}"')
            if cover_value:
                lines.append(f'image: {cover_value}')
            if tags_raw:
                tag_list = [t.strip() for t in tags_raw.split(',') if t.strip()]
                if tag_list:
                    lines.append('tags: [' + ', '.join(f'"{t}"' for t in tag_list) + ']')
            if category:
                lines.append(f'category: {category}')
            if draft:
                lines.append('draft: true')
            if pinned:
                lines.append('pinned: true')
            lines.append('---')
            lines.append('')
            lines.append(content)
            lines.append('')
            
            md_content = '\n'.join(lines)
            
            index_path = os.path.join(post_dir, 'index.md')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            dialog.destroy()
            self.refresh_posts()
            messagebox.showinfo("成功", f"文章 '{title}' {'更新' if is_edit else '创建'}成功！\n\n路径: src/content/posts/{folder_name}/")
        
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=(8, 0))
        ttk.Button(btn_frame, text="💾 保存", command=do_save, style='Primary.TButton').pack(side=tk.RIGHT)
        
        right_panel = ttk.Frame(split_frame, style='TFrame')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        content_frame = ttk.LabelFrame(right_panel, text="  文章内容  ", style='Card.TLabelframe', padding=12)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        toolbar = ttk.Frame(content_frame, style='Card.TFrame')
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        post_state = {"dir": None, "images_dir": None, "slug": None}
        
        def ensure_post_dir():
            slug = slug_entry.get().strip() or title_entry.get().strip()
            if not slug:
                messagebox.showwarning("提示", "请先填写标题或 Slug")
                return None
            slug_clean = re.sub(r'[\\/:*?"<>|]', '', slug.replace(' ', '-'))
            post_dir = os.path.join(POSTS_DIR, slug_clean)
            images_dir = os.path.join(post_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)
            post_state["dir"] = post_dir
            post_state["images_dir"] = images_dir
            post_state["slug"] = slug_clean
            return images_dir
        
        def insert_image():
            images_dir = ensure_post_dir()
            if not images_dir:
                return
            filepaths = filedialog.askopenfilenames(
                title="选择图片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"), ("所有文件", "*.*")]
            )
            if filepaths:
                for fp in filepaths:
                    filename = os.path.basename(fp)
                    safe_name = re.sub(r'[\s()\[\]{}]+', '_', filename)
                    safe_name = re.sub(r'_+', '_', safe_name)
                    dest = os.path.join(images_dir, safe_name)
                    compress_and_copy_image(fp, dest)
                    content_text.insert(tk.INSERT, f"![{safe_name}](./images/{safe_name})\n\n")
        
        def insert_link():
            url = simpledialog.askstring("插入链接", "请输入链接地址:")
            if not url:
                return
            text = simpledialog.askstring("插入链接", "请输入链接文字:") or url
            content_text.insert(tk.INSERT, f"[{text}]({url})")
        
        def insert_cloud_link():
            url = simpledialog.askstring("插入网盘链接", "请输入网盘链接:")
            if not url:
                return
            pwd = simpledialog.askstring("插入网盘链接", "请输入提取码（可留空）:") or ""
            text = "网盘下载"
            if pwd:
                content_text.insert(tk.INSERT, f"[{text}]({url})  提取码：{pwd}\n\n")
            else:
                content_text.insert(tk.INSERT, f"[{text}]({url})\n\n")
        
        ttk.Button(toolbar, text="🖼️ 插入图片", command=insert_image).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="🔗 插入链接", command=insert_link).pack(side=tk.LEFT, padx=6)
        ttk.Button(toolbar, text="☁️ 插入网盘链接", command=insert_cloud_link).pack(side=tk.LEFT, padx=6)
        ttk.Label(toolbar, text="💡 图片会自动复制到文章的 images 目录", style='Hint.TLabel').pack(side=tk.LEFT, padx=16)
        
        content_text = tk.Text(
            content_frame, 
            wrap=tk.WORD, 
            font=('Microsoft YaHei UI', 11),
            bg=COLORS['card'],
            fg=COLORS['text'],
            insertbackground=COLORS['primary'],
            relief='flat',
            padx=12,
            pady=12,
            undo=True
        )
        content_text.insert(tk.END, defaults['content'])
        content_text.pack(fill=tk.BOTH, expand=True)
        
        title_entry.focus_set()
    
    def edit_post(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要编辑的文章")
            return
        
        item = selection[0]
        post_name = self.tree.item(item, 'values')[0]
        self.add_post(post_name)
    
    def delete_post(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要删除的文章")
            return
        
        item = selection[0]
        post_name = self.tree.item(item, 'values')[0]
        
        if messagebox.askyesno("确认删除", f"确定要删除文章 '{post_name}' 吗？\n\n同时会删除该文章目录下的所有图片。\n此操作不可恢复！"):
            post_dir = os.path.join(POSTS_DIR, post_name)
            try:
                shutil.rmtree(post_dir)
                self.refresh_posts()
                messagebox.showinfo("成功", f"文章 '{post_name}' 已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")
    
    def open_posts_dir(self):
        try:
            os.startfile(POSTS_DIR) if sys.platform == 'win32' else subprocess.run(['open', POSTS_DIR])
        except:
            messagebox.showerror("错误", "无法打开目录")
    
    def git_push(self):
        project_dir = os.path.dirname(POSTS_DIR)
        commit_msg = simpledialog.askstring("提交信息", "请输入提交信息:")
        if not commit_msg:
            return
        
        log_dialog = tk.Toplevel(self.root)
        log_dialog.title("Git 推送")
        log_dialog.geometry("720x520")
        log_dialog.configure(bg=COLORS['bg'])
        log_dialog.transient(self.root)
        
        header = ttk.Frame(log_dialog, style='TFrame', padding=(20, 16))
        header.pack(fill=tk.X)
        ttk.Label(header, text="📤 Git 推送中...", style='Title.TLabel').pack(side=tk.LEFT)
        
        log_frame = ttk.Frame(log_dialog, style='TFrame', padding=(20, 0))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        log_text = tk.Text(
            log_frame, 
            wrap=tk.WORD, 
            font=("Consolas", 10),
            bg='#1e293b',
            fg='#e2e8f0',
            insertbackground='#6366f1',
            relief='flat',
            padx=16,
            pady=12
        )
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.configure(yscrollcommand=scrollbar.set)
        
        btn_frame = ttk.Frame(log_dialog, style='TFrame', padding=(20, 16))
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="关闭", command=log_dialog.destroy, style='Primary.TButton').pack(side=tk.RIGHT)
        
        def run_git():
            import threading
            def worker():
                commands = [
                    ("git add -A", ["git", "-C", project_dir, "add", "-A"]),
                    ("git status", ["git", "-C", project_dir, "status"]),
                    (f'git commit -m "{commit_msg}"', ["git", "-C", project_dir, "commit", "-m", commit_msg]),
                    ("git push", ["git", "-C", project_dir, "push"]),
                ]
                log_dialog.after(0, lambda: log_text.insert(tk.END, "🚀 开始执行...\n\n"))
                
                for name, cmd in commands:
                    log_dialog.after(0, lambda n=name: log_text.insert(tk.END, f"$ {n}\n", 'command'))
                    log_dialog.after(0, log_text.see, tk.END)
                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, encoding='utf-8', cwd=project_dir
                        )
                        output = (result.stdout or '').strip()
                        err_output = (result.stderr or '').strip()
                        if output:
                            for line in output.split('\n'):
                                log_dialog.after(0, lambda l=line: log_text.insert(tk.END, l + "\n", 'output'))
                        if err_output:
                            for line in err_output.split('\n'):
                                log_dialog.after(0, lambda l=line: log_text.insert(tk.END, l + "\n", 'error'))
                        if result.returncode == 0:
                            log_dialog.after(0, lambda: log_text.insert(tk.END, "\n✓ 成功\n\n", 'success'))
                        else:
                            if 'nothing to commit' in output or 'nothing to commit' in err_output:
                                log_dialog.after(0, lambda: log_text.insert(tk.END, "\nℹ 没有改动，跳过提交\n\n", 'info'))
                            else:
                                log_dialog.after(0, lambda: log_text.insert(tk.END, "\n✗ 失败\n\n", 'error'))
                    except Exception as e:
                        log_dialog.after(0, lambda err=e: log_text.insert(tk.END, f"错误: {err}\n\n", 'error'))
                    log_dialog.after(0, log_text.see, tk.END)
                
                log_dialog.after(0, lambda: log_text.insert(tk.END, "=" * 50 + "\n完成！请查看上面的日志。\n", 'info'))
                log_dialog.after(0, log_text.see, tk.END)
            
            threading.Thread(target=worker, daemon=True).start()
        
        log_text.tag_config('command', foreground='#94a3b8')
        log_text.tag_config('output', foreground='#e2e8f0')
        log_text.tag_config('error', foreground='#f87171')
        log_text.tag_config('success', foreground='#34d399')
        log_text.tag_config('info', foreground='#fbbf24')
        
        log_dialog.after(100, run_git)


if __name__ == '__main__':
    root = tk.Tk()
    app = BlogManagerApp(root)
    root.mainloop()
