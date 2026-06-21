# -*- coding: utf-8 -*-
"""
Firefly 博客管理工具
用于添加和删除博客文章
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
        """添加新文章"""
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新文章")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # 文章标题
        ttk.Label(dialog, text="文章标题:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        title_entry = ttk.Entry(dialog, width=40)
        title_entry.grid(row=0, column=1, padx=10, pady=5)

        # 文章标签
        ttk.Label(dialog, text="标签 (逗号分隔):").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        tags_entry = ttk.Entry(dialog, width=40)
        tags_entry.grid(row=1, column=1, padx=10, pady=5)

        # 文章内容
        ttk.Label(dialog, text="文章内容:").grid(row=2, column=0, sticky=tk.NW, padx=10, pady=5)
        content_text = tk.Text(dialog, width=50, height=15)
        content_text.grid(row=2, column=1, padx=10, pady=5)

        def do_add():
            title = title_entry.get().strip()
            tags = tags_entry.get().strip()
            content = content_text.get("1.0", tk.END).strip()

            if not title:
                messagebox.showerror("错误", "请输入文章标题")
                return

            # 创建文件夹名（使用标题）
            folder_name = title
            post_dir = os.path.join(POSTS_DIR, folder_name)

            if os.path.exists(post_dir):
                messagebox.showerror("错误", f"文章 '{title}' 已存在！")
                return

            # 创建文章目录
            os.makedirs(post_dir)

            # 生成frontmatter
            date_str = datetime.now().strftime("%Y-%m-%d")
            tags_str = ""
            if tags:
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                if tag_list:
                    tags_str = '\ntags: [' + ', '.join(f'"{t}"' for t in tag_list) + ']'

            # 生成markdown内容
            md_content = f"""---
title: "{title}"
published: {date_str}{tags_str}
---

{content}
"""

            # 写入index.md
            index_path = os.path.join(post_dir, 'index.md')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            # 创建图片目录
            images_dir = os.path.join(post_dir, 'images')
            os.makedirs(images_dir, exist_ok=True)

            dialog.destroy()
            self.refresh_posts()
            messagebox.showinfo("成功", f"文章 '{title}' 创建成功！")

        ttk.Button(dialog, text="创建文章", command=do_add).grid(row=3, column=1, sticky=tk.E, padx=10, pady=10)
        ttk.Button(dialog, text="取消", command=dialog.destroy).grid(row=3, column=0, sticky=tk.E, padx=10, pady=10)

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
