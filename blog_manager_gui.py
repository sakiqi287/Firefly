#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firefly 博客管理工具
功能：新建 / 编辑 / 删除文章、插入图片、设置封面、自动 Git 推送
"""

import os
import re
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

# ================= 配置 =================
POSTS_DIR = "src/content/posts"          # 文章目录
ROOT_DIR = Path(__file__).parent         # 项目根目录

# ================ 主程序 ================
class BlogManager:
    def __init__(self, root):
        self.root = root
        self.root.title("绘鱼博客管理工具")
        self.root.geometry("1280x820")
        self.root.minsize(1000, 600)

        # 当前文章
        self.current_slug = None
        self.current_post_dir = None
        self.current_md_file = None
        self.current_images_dir = None

        # 初始化界面和加载文章
        self._build_ui()
        self.refresh_post_list()
        self.set_status("就绪")

    # ---------------- UI 构建 ----------------
    def _build_ui(self):
        # 顶部工具栏
        top_bar = ttk.Frame(self.root, padding=(10, 8))
        top_bar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top_bar, text="➕ 新建文章", width=12, command=self.new_post).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="💾 保存", width=10, command=self.save_post).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="🗑️ 删除", width=10, command=self.delete_post).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="🔄 刷新列表", width=10, command=self.refresh_post_list).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_bar, text="🚀 推送 GitHub", width=16, command=self.git_push).pack(side=tk.LEFT, padx=8)

        ttk.Label(top_bar, text="", width=40).pack(side=tk.LEFT, padx=3)

        # 主体（双栏）
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ===== 左侧：文章列表 =====
        left = ttk.Frame(main, width=260)
        main.add(left, weight=0)

        ttk.Label(left, text="📚 文章列表", font=("", 11, "bold")).pack(pady=(5, 3))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5)

        self.posts_listbox = tk.Listbox(list_frame, font=("", 10))
        self.posts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.posts_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.posts_listbox.config(yscrollcommand=sb.set)
        self.posts_listbox.bind("<<ListboxSelect>>", self.on_select_post)

        # ===== 右侧：编辑区 =====
        right = ttk.Frame(main)
        main.add(right, weight=1)

        # 文章信息
        info = ttk.LabelFrame(right, text="文章信息", padding=10)
        info.pack(fill=tk.X, padx=5, pady=5)

        self.title_var = tk.StringVar()
        self.slug_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.category_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.cover_var = tk.StringVar()

        fields = [
            ("标题", 0, self.title_var, 50),
            ("Slug (英文/拼音)", 1, self.slug_var, 50),
            ("日期", 2, self.date_var, 20),
            ("分类", 3, self.category_var, 50),
            ("标签（逗号分隔）", 4, self.tags_var, 50),
        ]
        for label_text, row, var, width in fields:
            ttk.Label(info, text=label_text + ":").grid(row=row, column=0, sticky="e", pady=3, padx=(0, 8))
            ent = ttk.Entry(info, textvariable=var, width=width)
            ent.grid(row=row, column=1, sticky="we", pady=3)
        info.grid_columnconfigure(1, weight=1)

        # 封面
        ttk.Label(info, text="封面:").grid(row=5, column=0, sticky="e", pady=3, padx=(0, 8))
        cover_row = ttk.Frame(info)
        cover_row.grid(row=5, column=1, sticky="we", pady=3)
        ttk.Entry(cover_row, textvariable=self.cover_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(cover_row, text="选择图片", command=self.select_cover, width=10).pack(side=tk.LEFT, padx=5)

        # 内容编辑区
        content_frame = ttk.LabelFrame(right, text="文章内容 (Markdown)", padding=8)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 工具栏
        tool_bar = ttk.Frame(content_frame)
        tool_bar.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(tool_bar, text="🖼️ 插入图片", command=self.insert_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_bar, text="📎 插入链接", command=self.insert_link).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_bar, text="🔗 插入资源链接", command=self.insert_download_link).pack(side=tk.LEFT, padx=2)

        self.content_text = scrolledtext.ScrolledText(
            content_frame, wrap=tk.WORD, font=("Microsoft YaHei", 10),
            undo=True
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)

        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Frame(self.root)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status_var, anchor="w", padding=(10, 5)).pack(fill=tk.X)

    # ---------------- 工具函数 ----------------
    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def safe_filename(self, name):
        """把文件名处理成安全格式"""
        name = re.sub(r"[\s\(\)\[\]\{\}\【\】（）,，]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        return name

    def slugify(self, text):
        """从标题生成 slug"""
        text = text.strip()
        # 中文直接用原文，英文/数字保留
        text = re.sub(r"[\s\/\\:\*\?\"<>\|]+", "-", text)
        return text.strip("-") or "untitled"

    # ---------------- 列表加载 ----------------
    def refresh_post_list(self):
        """扫描文章目录，把已有文章列出来"""
        self.posts_listbox.delete(0, tk.END)
        posts_root = ROOT_DIR / POSTS_DIR
        if not posts_root.exists():
            posts_root.mkdir(parents=True, exist_ok=True)
            return

        entries = []
        for item in posts_root.iterdir():
            if item.is_dir() and (item / "index.md").exists():
                entries.append(item.name)
        entries.sort()
        for name in entries:
            self.posts_listbox.insert(tk.END, name)

    # ---------------- 选中文章 ----------------
    def on_select_post(self, event=None):
        sel = self.posts_listbox.curselection()
        if not sel:
            return
        slug = self.posts_listbox.get(sel[0])
        self._load_post(slug)

    def _load_post(self, slug):
        posts_root = ROOT_DIR / POSTS_DIR
        post_dir = posts_root / slug
        md_file = post_dir / "index.md"

        if not md_file.exists():
            messagebox.showerror("错误", f"找不到文章文件：{md_file}")
            return

        self.current_slug = slug
        self.current_post_dir = post_dir
        self.current_md_file = md_file
        self.current_images_dir = post_dir / "images"

        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        self._parse_frontmatter(content)
        self.slug_var.set(slug)
        self.set_status(f"已加载：{slug}")

    def _parse_frontmatter(self, raw):
        """解析文章开头的 --- ... --- 区域"""
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
        if not m:
            # 没有 frontmatter，全当正文
            self.title_var.set("")
            self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.category_var.set("")
            self.tags_var.set("")
            self.cover_var.set("")
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", raw)
            return

        frontmatter = m.group(1)
        body = m.group(2)

        self.title_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.category_var.set("")
        self.tags_var.set("")
        self.cover_var.set("")

        for line in frontmatter.split("\n"):
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip("\"'")

            if key == "title":
                self.title_var.set(value)
            elif key in ("published", "date"):
                self.date_var.set(value)
            elif key == "category":
                self.category_var.set(value)
            elif key == "tags":
                tags = re.findall(r'"([^"]+)"', value)
                self.tags_var.set(", ".join(tags))
            elif key in ("image", "cover"):
                # value 形如 ./images/xxx.jpg，只保留文件名
                name = os.path.basename(value)
                self.cover_var.set(name)

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", body)

    # ---------------- 新建 ----------------
    def new_post(self):
        self.current_slug = None
        self.current_post_dir = None
        self.current_md_file = None
        self.current_images_dir = None

        self.title_var.set("")
        self.slug_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.category_var.set("")
        self.tags_var.set("")
        self.cover_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.posts_listbox.selection_clear(0, tk.END)
        self.set_status("新建文章模式")

    # ---------------- 保存 ----------------
    def save_post(self):
        title = self.title_var.get().strip()
        slug = self.slug_var.get().strip()
        date = self.date_var.get().strip()
        category = self.category_var.get().strip()
        tags = self.tags_var.get().strip()
        cover = self.cover_var.get().strip()
        body = self.content_text.get("1.0", tk.END).strip()

        if not title:
            messagebox.showerror("错误", "请输入标题")
            return
        if not slug:
            slug = self.slugify(title)
            self.slug_var.set(slug)
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            self.date_var.set(date)

        # 构建 frontmatter
        tag_items = [t.strip() for t in tags.split(",") if t.strip()]
        tags_line = ", ".join(f'"{t}"' for t in tag_items)

        fm = f'title: "{title}"\n'
        fm += f"published: {date}\n"
        fm += f"tags: [{tags_line}]\n"
        if category:
            fm += f"category: {category}\n"
        if cover:
            fm += f"image: ./images/{cover}\n"
        full = f"---\n{fm}---\n\n{body}\n"

        # 写入文件
        posts_root = ROOT_DIR / POSTS_DIR
        posts_root.mkdir(parents=True, exist_ok=True)
        post_dir = posts_root / slug
        post_dir.mkdir(exist_ok=True)
        md_file = post_dir / "index.md"

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(full)

        self.current_slug = slug
        self.current_post_dir = post_dir
        self.current_md_file = md_file
        self.current_images_dir = post_dir / "images"

        # 刷新列表
        self.refresh_post_list()
        # 在列表里定位到这篇文章
        for i in range(self.posts_listbox.size()):
            if self.posts_listbox.get(i) == slug:
                self.posts_listbox.selection_clear(0, tk.END)
                self.posts_listbox.selection_set(i)
                self.posts_listbox.see(i)
                break

        self.set_status(f"已保存：{md_file}")

        # 问是否马上推送到 GitHub
        if messagebox.askyesno("推送", "文章已保存，是否立即推送到 GitHub？"):
            self.git_push()

    # ---------------- 删除 ----------------
    def delete_post(self):
        sel = self.posts_listbox.curselection()
        if not sel and not self.current_slug:
            messagebox.showwarning("提示", "请先选择一篇文章")
            return

        slug = self.current_slug
        if not slug and sel:
            slug = self.posts_listbox.get(sel[0])

        if not slug:
            return

        if not messagebox.askyesno(
            "确认删除",
            f"确定删除文章「{slug}」吗？\n同时会删除该文章目录下的所有图片。\n\n此操作无法恢复。"
        ):
            return

        post_dir = ROOT_DIR / POSTS_DIR / slug
        if post_dir.exists():
            shutil.rmtree(post_dir)

        self.new_post()
        self.refresh_post_list()
        self.set_status(f"已删除：{slug}")

        if messagebox.askyesno("推送", "删除完成，是否立即推送到 GitHub？"):
            self.git_push()

    # ---------------- 图片 ----------------
    def _ensure_current_images_dir(self):
        slug = self.slug_var.get().strip() or self.slugify(self.title_var.get().strip())
        if not slug:
            messagebox.showerror("错误", "请先填写标题或 Slug")
            return None
        d = ROOT_DIR / POSTS_DIR / slug / "images"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def select_cover(self):
        fn = filedialog.askopenfilename(
            title="选择封面图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.gif"), ("所有文件", "*.*")]
        )
        if not fn:
            return
        target_dir = self._ensure_current_images_dir()
        if not target_dir:
            return

        base = os.path.basename(fn)
        safe = self.safe_filename(base)
        shutil.copy2(fn, target_dir / safe)
        self.cover_var.set(safe)
        self.set_status(f"封面已设置：{safe}")

    def insert_image(self):
        fn = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.gif"), ("所有文件", "*.*")]
        )
        if not fn:
            return
        target_dir = self._ensure_current_images_dir()
        if not target_dir:
            return

        base = os.path.basename(fn)
        safe = self.safe_filename(base)
        shutil.copy2(fn, target_dir / safe)
        self.content_text.insert(tk.INSERT, f"\n![{safe}](./images/{safe})\n")
        self.set_status(f"已插入图片：{safe}")

    def insert_link(self):
        self.content_text.insert(tk.INSERT, "[链接文本](https://)")

    def insert_download_link(self):
        """插入网盘资源下载链接（你常用的格式）"""
        self.content_text.insert(
            tk.INSERT,
            "\n链接：https://pan.xunlei.com/s/xxxxxx#\n提取码：xxxx\n"
        )

    # ---------------- Git 推送 ----------------
    def git_push(self):
        try:
            self.set_status("正在推送到 GitHub...")
            self.root.update()

            # git status 检查有改动吗
            r = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(ROOT_DIR), capture_output=True, text=True
            )
            if not r.stdout.strip() and r.returncode == 0:
                self.set_status("没有改动，无需推送")
                messagebox.showinfo("提示", "本地代码没有改动，无需推送。")
                return

            commands = [
                ["git", "add", "-A"],
                ["git", "commit", "-m", f"更新文章：{datetime.now().strftime('%Y-%m-%d %H:%M')}"],
                ["git", "push"],
            ]

            for cmd in commands:
                self.set_status(f"执行：{' '.join(cmd)}")
                self.root.update()
                result = subprocess.run(
                    cmd, cwd=str(ROOT_DIR), capture_output=True, text=True
                )
                # commit 如果没有改动会返回非 0，但不是致命错误
                if cmd[1] == "commit" and result.returncode != 0:
                    if "nothing to commit" in (result.stdout + result.stderr):
                        self.set_status("没有新改动，跳过 commit")
                        continue
                if result.returncode != 0:
                    err = result.stderr.strip() or result.stdout.strip()
                    raise Exception(err)

            self.set_status("✅ 推送成功，Cloudflare 正在自动部署（约 2-5 分钟）")
            messagebox.showinfo(
                "推送成功",
                "已推送到 GitHub！\n\nCloudflare Pages 会自动检测并重新部署，\n大约 2-5 分钟后你的博客就会更新。"
            )
        except Exception as e:
            err_msg = str(e)
            self.set_status("❌ 推送失败")
            messagebox.showerror(
                "推送失败",
                f"Git 推送失败：\n\n{err_msg}\n\n"
                f"请检查：\n"
                f"1. 是否已安装 Git\n"
                f"2. 是否配置了 Git 账号\n"
                f"3. 是否能正常访问 GitHub"
            )


if __name__ == "__main__":
    root = tk.Tk()
    # Windows 下让 ttk 主题好看点
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = BlogManager(root)
    root.mainloop()
