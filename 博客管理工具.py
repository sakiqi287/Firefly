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

# 配置
POSTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'posts')
GIT_REMOTE = "https://github.com/sakiqi287/Firefly.git"

class BlogManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firefly 博客管理工具")
        self.root.geometry("780x520")
        self.root.minsize(700, 450)

        self.posts = []
        self.load_posts()

        self.create_ui()

    def load_posts(self):
        """加载所有文章"""
        self.posts = []
        if os.path.exists(POSTS_DIR):
            for name in os.listdir(POSTS_DIR):
                post_path = os.path.join(POSTS_DIR, name)
                if os.path.isdir(post_path):
                    index_file = os.path.join(post_path, 'index.md')
                    if os.path.exists(index_file):
                        self.posts.append(name)

    def create_ui(self):
        """创建界面 - 简洁版"""
        # 顶部工具栏
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(top_frame, text="刷新列表", command=self.refresh_posts).pack(side=tk.RIGHT)

        # 文章列表
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=2)

        columns = ('name',)
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=18)
        self.tree.heading('#0', text='序号')
        self.tree.heading('name', text='文章名称')
        self.tree.column('#0', width=60, anchor=tk.CENTER, stretch=False)
        self.tree.column('name', anchor=tk.W, stretch=True)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.populate_tree()

        # 底部按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="添加文章", command=self.add_post).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑文章", command=self.edit_post).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除文章", command=self.delete_post).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="打开文章目录", command=self.open_posts_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Git 推送", command=self.git_push).pack(side=tk.RIGHT, padx=5)

        # 状态栏
        self.status_var = tk.StringVar(value=f"共 {len(self.posts)} 篇文章")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X, padx=10, pady=5)

    def populate_tree(self):
        """填充文章列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, name in enumerate(sorted(self.posts), 1):
            self.tree.insert('', tk.END, text=str(i), values=(name,))

    def refresh_posts(self):
        """刷新文章列表"""
        self.load_posts()
        self.populate_tree()
        self.status_var.set(f"共 {len(self.posts)} 篇文章")

    def parse_frontmatter(self, content):
        """解析 Markdown 文件的 frontmatter"""
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
        """添加新文章或编辑现有文章 - 左右分栏布局"""
        is_edit = post_name is not None

        dialog = tk.Toplevel(self.root)
        dialog.title("编辑文章" if is_edit else "添加新文章")
        dialog.geometry("1000x620")
        dialog.minsize(900, 550)
        dialog.transient(self.root)
        dialog.grab_set()

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

        # ===== 主容器：左右分栏 =====
        main_pane = ttk.PanedWindow(dialog, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ===== 左侧：基本信息 =====
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=1)

        info_frame = ttk.LabelFrame(left_frame, text="基本信息")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 内容可滚动
        info_canvas = tk.Canvas(info_frame, highlightthickness=0)
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_canvas.yview)
        info_inner = ttk.Frame(info_canvas)
        info_inner.bind(
            "<Configure>",
            lambda e: info_canvas.configure(scrollregion=info_canvas.bbox("all"))
        )
        info_canvas.create_window((0, 0), window=info_inner, anchor="nw")
        info_canvas.configure(yscrollcommand=info_scrollbar.set)
        info_canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        info_scrollbar.pack(side="right", fill="y")

        row = 0
        ttk.Label(info_inner, text="标题 *:").grid(row=row, column=0, sticky=tk.E, padx=3, pady=3)
        title_entry = ttk.Entry(info_inner, width=32)
        title_entry.insert(0, defaults['title'])
        title_entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)

        row += 1
        ttk.Label(info_inner, text="Slug *:").grid(row=row, column=0, sticky=tk.E, padx=3, pady=3)
        slug_entry = ttk.Entry(info_inner, width=22)
        slug_entry.insert(0, defaults['slug'])
        slug_entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)
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

        ttk.Button(info_inner, text="← 根据标题生成", command=gen_slug_from_title).grid(row=row+1, column=1, sticky=tk.W, padx=3, pady=0)
        row += 1

        path_label = ttk.Label(info_inner, text="路径: (先填标题或Slug)", foreground="blue")
        path_label.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=3, pady=2)

        def update_path_label(*args):
            slug = slug_entry.get().strip() or title_entry.get().strip()
            if slug:
                path_label.config(text=f"路径: .../posts/{slug}/index.md")
            else:
                path_label.config(text="路径: (先填标题或Slug)")

        title_entry.bind("<KeyRelease>", update_path_label)
        slug_entry.bind("<KeyRelease>", update_path_label)
        update_path_label()

        row += 1
        ttk.Label(info_inner, text="日期:").grid(row=row, column=0, sticky=tk.E, padx=3, pady=3)
        date_entry = ttk.Entry(info_inner, width=32)
        date_entry.insert(0, defaults['date'])
        date_entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)

        row += 1
        ttk.Label(info_inner, text="分类:").grid(row=row, column=0, sticky=tk.E, padx=3, pady=3)
        category_entry = ttk.Entry(info_inner, width=32)
        category_entry.insert(0, defaults['category'])
        category_entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)

        row += 1
        ttk.Label(info_inner, text="标签:").grid(row=row, column=0, sticky=tk.E, padx=3, pady=3)
        tags_entry = ttk.Entry(info_inner, width=32)
        tags_entry.insert(0, defaults['tags'])
        tags_entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)
        ttk.Label(info_inner, text="(逗号分隔)", foreground="gray").grid(row=row+1, column=1, sticky=tk.W, padx=3, pady=0)
        row += 1

        row += 1
        ttk.Label(info_inner, text="描述:").grid(row=row, column=0, sticky=tk.NE, padx=3, pady=3)
        description_text = tk.Text(info_inner, width=28, height=3, wrap=tk.WORD)
        description_text.insert(tk.END, defaults['description'])
        description_text.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)

        row += 1
        ttk.Label(info_inner, text="封面:").grid(row=row, column=0, sticky=tk.E, padx=3, pady=3)
        cover_entry = ttk.Entry(info_inner, width=22)
        cover_entry.insert(0, defaults['cover'])
        cover_entry.grid(row=row, column=1, sticky=tk.W, padx=3, pady=3)

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

        ttk.Button(info_inner, text="选择图片", command=select_cover).grid(row=row+1, column=1, sticky=tk.W, padx=3, pady=0)
        row += 1

        row += 2
        opt_frame = ttk.Frame(info_inner)
        opt_frame.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=3, pady=8)

        draft_var = tk.BooleanVar(value=defaults['draft'])
        pinned_var = tk.BooleanVar(value=defaults['pinned'])

        ttk.Checkbutton(opt_frame, text="草稿", variable=draft_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(opt_frame, text="置顶", variable=pinned_var).pack(side=tk.LEFT, padx=5)

        # ===== 右侧：文章内容 =====
        right_frame = ttk.Frame(main_pane)
        main_pane.add(right_frame, weight=3)

        content_frame = ttk.LabelFrame(right_frame, text="文章内容 (Markdown)")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 工具栏
        toolbar = ttk.Frame(content_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=4)

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
            if 'pan.xunlei.com' in url:
                text = "迅雷下载"
            elif 'pan.quark.cn' in url:
                text = "夸克下载"
            if pwd:
                content_text.insert(tk.INSERT, f"{text}：{url}\n提取码：{pwd}\n\n")
            else:
                content_text.insert(tk.INSERT, f"{text}：{url}\n\n")

        ttk.Button(toolbar, text="🖼️ 插入图片", command=insert_image).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🔗 插入链接", command=insert_link).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="☁️ 插入网盘链接", command=insert_cloud_link).pack(side=tk.LEFT, padx=3)
        ttk.Label(toolbar, text="图片自动复制到文章images目录", foreground="gray").pack(side=tk.LEFT, padx=8)

        # 内容编辑区（带滚动条）
        content_text_frame = ttk.Frame(content_frame)
        content_text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        content_text = tk.Text(content_text_frame, wrap=tk.WORD)
        content_text.insert(tk.END, defaults['content'])
        content_sb = ttk.Scrollbar(content_text_frame, orient=tk.VERTICAL, command=content_text.yview)
        content_text.configure(yscrollcommand=content_sb.set)
        content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ===== 底部按钮 =====
        bottom_frame = ttk.Frame(dialog)
        bottom_frame.pack(fill=tk.X, padx=10, pady=8)

        def do_save():
            title = title_entry.get().strip()
            slug = slug_entry.get().strip()
            date_str = date_entry.get().strip()
            category = category_entry.get().strip()
            tags_raw = tags_entry.get().strip()
            description = description_text.get("1.0", tk.END).strip()
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

        ttk.Button(bottom_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="✓ 保存文章", command=do_save).pack(side=tk.RIGHT, padx=5)

        title_entry.focus_set()

    def edit_post(self):
        """编辑文章"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的文章")
            return

        item = selection[0]
        post_name = self.tree.item(item, 'values')[0]
        self.add_post(post_name)

    def delete_post(self):
        """删除文章"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要编辑的文章")
            return

        item = selection[0]
        post_name = self.tree.item(item, 'values')[0]

        if messagebox.askyesno("确认删除", f"确定要删除文章 '{post_name}' 吗？\n此操作不可恢复！"):
            post_dir = os.path.join(POSTS_DIR, post_name)
            try:
                shutil.rmtree(post_dir)
                self.refresh_posts()
                messagebox.showinfo("成功", f"文章 '{post_name}' 已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")

    def open_posts_dir(self):
        """打开文章目录"""
        try:
            os.startfile(POSTS_DIR) if sys.platform == 'win32' else subprocess.run(['open', POSTS_DIR])
        except:
            messagebox.showerror("错误", "无法打开目录")

    def git_push(self):
        """Git推送 - 自动提交（commit message固定为update）"""
        project_dir = os.path.dirname(os.path.dirname(POSTS_DIR))
        commit_msg = "update"

        log_dialog = tk.Toplevel(self.root)
        log_dialog.title("Git 推送")
        log_dialog.geometry("700x500")
        log_dialog.transient(self.root)

        log_text = tk.Text(log_dialog, wrap=tk.WORD, font=("Consolas", 10))
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(log_dialog, orient=tk.VERTICAL, command=log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        log_text.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(log_dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        close_btn = ttk.Button(btn_frame, text="关闭", command=log_dialog.destroy)
        close_btn.pack(side=tk.RIGHT)

        def run_git():
            import threading
            def worker():
                commands = [
                    ("git add -A", ["git", "-C", project_dir, "add", "-A"]),
                    ("git status", ["git", "-C", project_dir, "status", "--short"]),
                    (f'git commit -m "{commit_msg}"', ["git", "-C", project_dir, "commit", "-m", commit_msg]),
                    ("git push", ["git", "-C", project_dir, "push"]),
                ]
                log_dialog.after(0, lambda: log_text.insert(tk.END, "开始执行...\n\n"))

                for name, cmd in commands:
                    log_dialog.after(0, lambda n=name: log_text.insert(tk.END, f">>> {n}\n"))
                    log_dialog.after(0, log_text.see, tk.END)
                    try:
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, encoding='utf-8', cwd=project_dir
                        )
                        output = (result.stdout or '').strip()
                        err_output = (result.stderr or '').strip()
                        if output:
                            for line in output.split('\n'):
                                log_dialog.after(0, lambda l=line: log_text.insert(tk.END, l + "\n"))
                        if err_output:
                            for line in err_output.split('\n'):
                                log_dialog.after(0, lambda l=line: log_text.insert(tk.END, l + "\n"))
                        if result.returncode == 0:
                            log_dialog.after(0, lambda: log_text.insert(tk.END, "✓ 成功\n\n"))
                        else:
                            if 'nothing to commit' in output or 'nothing to commit' in err_output:
                                log_dialog.after(0, lambda: log_text.insert(tk.END, "ℹ 没有改动，跳过提交\n\n"))
                            else:
                                log_dialog.after(0, lambda: log_text.insert(tk.END, "✗ 失败\n\n"))
                    except Exception as e:
                        log_dialog.after(0, lambda err=e: log_text.insert(tk.END, f"错误: {err}\n\n"))
                    log_dialog.after(0, log_text.see, tk.END)

                log_dialog.after(0, lambda: log_text.insert(tk.END, "=" * 50 + "\n完成！请查看上面的日志。\n"))
                log_dialog.after(0, log_text.see, tk.END)

            threading.Thread(target=worker, daemon=True).start()

        log_dialog.after(100, run_git)

if __name__ == '__main__':
    root = tk.Tk()
    app = BlogManagerApp(root)
    root.mainloop()
