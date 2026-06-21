# -*- coding: utf-8 -*-
"""
Firefly 博客管理工具
用于添加和删除博客文章
"""

import os
import sys
import re
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import shutil
import subprocess

# 配置
POSTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'posts')
GIT_REMOTE = "https://github.com/sakiqi287/Firefly.git"

class BlogManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Firefly 博客管理工具")
        self.root.geometry("800x600")

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
        """创建界面"""
        # 顶部标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(title_frame, text="Firefly 博客管理", font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        ttk.Button(title_frame, text="刷新列表", command=self.refresh_posts).pack(side=tk.RIGHT)

        # 文章列表
        list_frame = ttk.Frame(self.root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        ttk.Label(list_frame, text="文章列表:").pack(anchor=tk.W)

        # 创建Treeview显示文章列表
        columns = ('name',)
        self.tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', height=15)
        self.tree.heading('#0', text='序号')
        self.tree.heading('name', text='文章名称')

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.populate_tree()

        # 底部按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="添加文章", command=self.add_post).pack(side=tk.LEFT, padx=5)
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

    def add_post(self):
        """添加新文章 - 详细表单"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新文章")
        dialog.geometry("800x750")
        dialog.transient(self.root)
        dialog.grab_set()

        # 创建主滚动容器
        main_canvas = tk.Canvas(dialog)
        main_scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=main_canvas.yview)
        main_frame = ttk.Frame(main_canvas)

        main_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(
                scrollregion=main_canvas.bbox("all")
            )
        )

        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")

        # ===== 文章信息分组 =====
        info_frame = ttk.LabelFrame(main_frame, text="文章信息")
        info_frame.pack(fill=tk.X, padx=10, pady=10)

        # 标题
        row = 0
        ttk.Label(info_frame, text="标题 *:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
        title_entry = ttk.Entry(info_frame, width=70)
        title_entry.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # Slug
        row += 1
        ttk.Label(info_frame, text="Slug *:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
        slug_entry = ttk.Entry(info_frame, width=55)
        slug_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        def gen_slug_from_title():
            title = title_entry.get().strip()
            if title:
                # 转成小写英文 slug（中文保持原样）
                s = title.strip().replace(' ', '-')
                s = re.sub(r'[\\/:*?"<>|]', '', s)
                slug_entry.delete(0, tk.END)
                slug_entry.insert(0, s)
                update_path_label()
            else:
                messagebox.showwarning("提示", "请先填写标题")

        ttk.Button(info_frame, text="根据标题生成", command=gen_slug_from_title).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)

        # 保存路径提示
        row += 1
        path_label = ttk.Label(info_frame, text="保存路径: (请先填写标题或 Slug)", foreground="blue")
        path_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)

        def update_path_label(*args):
            slug = slug_entry.get().strip() or title_entry.get().strip()
            if slug:
                path_label.config(text=f"保存路径: src/content/posts/{slug}/index.md")
            else:
                path_label.config(text="保存路径: (请先填写标题或 Slug)")

        title_entry.bind("<KeyRelease>", update_path_label)
        slug_entry.bind("<KeyRelease>", update_path_label)

        # 日期
        row += 1
        ttk.Label(info_frame, text="日期:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
        date_entry = ttk.Entry(info_frame, width=70)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        date_entry.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # 分类
        row += 1
        ttk.Label(info_frame, text="分类:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
        category_entry = ttk.Entry(info_frame, width=70)
        category_entry.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # 标签
        row += 1
        ttk.Label(info_frame, text="标签:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
        tags_entry = ttk.Entry(info_frame, width=70)
        tags_entry.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        ttk.Label(info_frame, text="(多个标签用逗号分隔，如: 前端, 开发)", foreground="gray").grid(row=row+1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=0)
        row += 1

        # 描述
        row += 1
        ttk.Label(info_frame, text="描述:").grid(row=row, column=0, sticky=tk.NE, padx=5, pady=5)
        description_text = tk.Text(info_frame, width=70, height=2)
        description_text.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        # 封面
        row += 1
        ttk.Label(info_frame, text="封面:").grid(row=row, column=0, sticky=tk.E, padx=5, pady=5)
        cover_entry = ttk.Entry(info_frame, width=55)
        cover_entry.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)

        cover_info = {"path": ""}  # 存储封面原始路径

        def select_cover():
            filepath = filedialog.askopenfilename(
                title="选择封面图片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png *.gif *.webp *.bmp"), ("所有文件", "*.*")]
            )
            if filepath:
                cover_info["path"] = filepath
                filename = os.path.basename(filepath)
                cover_entry.delete(0, tk.END)
                cover_entry.insert(0, f"./images/{filename}")

        ttk.Button(info_frame, text="选择图片", command=select_cover).grid(row=row, column=2, sticky=tk.W, padx=5, pady=5)

        # 选项（复选框）
        row += 1
        opt_frame = ttk.Frame(info_frame)
        opt_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=10)

        draft_var = tk.BooleanVar(value=False)
        pinned_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(opt_frame, text="草稿（不显示给读者）", variable=draft_var).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(opt_frame, text="置顶", variable=pinned_var).pack(side=tk.LEFT, padx=10)

        # ===== 文章内容分组 =====
        content_frame = ttk.LabelFrame(dialog, text="文章内容 (Markdown)")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 工具栏
        toolbar = ttk.Frame(content_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        # 存储当前文章目录和图片目录（用于图片插入功能）
        post_state = {"dir": None, "images_dir": None, "slug": None}

        def ensure_post_dir():
            """确保文章目录存在，用于图片插入"""
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
                    dest = os.path.join(images_dir, filename)
                    shutil.copy2(fp, dest)
                    content_text.insert(tk.INSERT, f"![{filename}](./images/{filename})\n\n")

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

        ttk.Button(toolbar, text="🖼️ 插入图片", command=insert_image).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🔗 插入链接", command=insert_link).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="☁️ 插入网盘链接", command=insert_cloud_link).pack(side=tk.LEFT, padx=3)
        ttk.Label(toolbar, text="💡 图片自动复制到文章自己的 images 目录", foreground="gray").pack(side=tk.LEFT, padx=10)

        # 内容编辑区
        content_text = tk.Text(content_frame, wrap=tk.WORD)
        content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ===== 底部按钮 =====
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        def do_add():
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
                # 自动生成 slug
                s = title.strip().replace(' ', '-')
                s = re.sub(r'[\\/:*?"<>|]', '', s)
                slug = s

            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")

            # 文章目录（先确保存在）
            folder_name = slug
            post_dir = os.path.join(POSTS_DIR, folder_name)

            if os.path.exists(post_dir) and os.path.isfile(os.path.join(post_dir, 'index.md')):
                if not messagebox.askyesno("确认", f"文章 '{folder_name}' 已存在，是否覆盖？"):
                    return
            os.makedirs(post_dir, exist_ok=True)
            images_dir = os.path.join(post_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)

            # 复制封面图片
            cover_value = cover
            if cover_info["path"] and cover:
                try:
                    cover_filename = os.path.basename(cover_info["path"])
                    dest = os.path.join(images_dir, cover_filename)
                    shutil.copy2(cover_info["path"], dest)
                    cover_value = f"./images/{cover_filename}"
                except Exception as e:
                    messagebox.showwarning("提示", f"封面复制失败: {e}")

            # 生成 frontmatter
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

            # 写入 index.md
            index_path = os.path.join(post_dir, 'index.md')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            dialog.destroy()
            self.refresh_posts()
            messagebox.showinfo("成功", f"文章 '{title}' 创建成功！\n\n路径: src/content/posts/{folder_name}/")

        ttk.Button(btn_frame, text="✓ 创建文章", command=do_add).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

        title_entry.focus_set()

    def delete_post(self):
        """删除文章"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的文章")
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
        """Git推送 - 打开独立命令行窗口"""
        project_dir = os.path.dirname(POSTS_DIR)
        commit_msg = simpledialog.askstring("提交信息", "请输入提交信息:")
        if not commit_msg:
            return

        # 创建批处理脚本
        bat_content = f"""@echo off
chcp 65001 >nul
cd /d "{project_dir}"
echo ============================================
echo   Firefly 博客 Git 推送
echo ============================================
echo.
echo [1/4] git add -A
git add -A
echo.
echo [2/4] git status
git status
echo.
echo [3/4] git commit -m "{commit_msg}"
git commit -m "{commit_msg}"
echo.
echo [4/4] git push
git push
echo.
echo ============================================
echo   完成! 按任意键退出...
echo ============================================
pause >nul
"""
        bat_path = os.path.join(project_dir, "_git_push_temp.bat")
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)

        try:
            subprocess.Popen(['cmd', '/c', 'start', 'cmd', '/k', bat_path], shell=False)
            messagebox.showinfo("提示", "已打开命令行窗口执行推送操作")
        except Exception as e:
            messagebox.showerror("错误", f"执行失败: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = BlogManagerApp(root)
    root.mainloop()
