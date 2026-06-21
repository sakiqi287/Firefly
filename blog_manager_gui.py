#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
绘鱼博客管理工具 v2.0
功能：
  ✨ 新建文章 / 📝 编辑文章 / 🗑️ 删除文章
  🖼️  封面设置 / 图片插入
  🚀 一键推送到 GitHub
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
POSTS_DIR = "src/content/posts"
ROOT_DIR = Path(__file__).resolve().parent

# ================ 主程序 ================
class BlogManager:
    def __init__(self, root):
        self.root = root
        self.root.title("绘鱼博客管理工具")
        self.root.geometry("1300x860")
        self.root.minsize(1100, 650)

        # 状态："new" = 新建文章模式，"edit" = 编辑已有文章模式
        self.mode = "new"
        self.editing_slug = None  # 记录最开始加载的 slug（防止保存时重命名）

        self._build_ui()
        self.refresh_post_list()
        self.set_mode("new")

    # ---------------- UI 构建 ----------------
    def _build_ui(self):
        # ===== 顶部：标题 + 模式显示 =====
        header = ttk.Frame(self.root, padding=(12, 8))
        header.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(header, text="📖 绘鱼博客管理工具", font=("", 14, "bold")).pack(side=tk.LEFT)

        self.mode_label = ttk.Label(header, text="", font=("", 11))
        self.mode_label.pack(side=tk.LEFT, padx=20)

        # ===== 工具栏 =====
        toolbar = ttk.Frame(self.root, padding=(10, 4))
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_style = {"width": 14}
        ttk.Button(toolbar, text="✨ 新建文章", command=self.action_new_post, **btn_style).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="💾 保存文章", command=self.action_save, **btn_style).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🗑️ 删除当前文章", command=self.action_delete, **btn_style).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🔄 刷新", command=self.refresh_post_list, **btn_style).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🚀 推送到 GitHub", command=self.action_git_push, **btn_style).pack(side=tk.LEFT, padx=10)

        # ===== 主体：双栏布局 =====
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- 左侧：文章列表 ---
        left = ttk.Frame(main, width=280)
        main.add(left, weight=0)

        ttk.Label(left, text="📚 已有文章", font=("", 11, "bold")).pack(pady=(5, 3))

        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.posts_listbox = tk.Listbox(list_frame, font=("", 10), activestyle="dotbox")
        self.posts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.posts_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.posts_listbox.config(yscrollcommand=sb.set)
        self.posts_listbox.bind("<<ListboxSelect>>", self.on_select_post)

        ttk.Label(left, text="💡 点击左侧文章进行编辑", foreground="#888", font=("", 9)).pack(pady=5)

        # --- 右侧：编辑区 ---
        right = ttk.Frame(main)
        main.add(right, weight=1)

        # 文章信息
        info = ttk.LabelFrame(right, text="  文章信息  ", padding=12)
        info.pack(fill=tk.X, padx=5, pady=5)

        self.title_var = tk.StringVar()
        self.slug_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.cover_var = tk.StringVar()

        # 标题
        ttk.Label(info, text="标题 *:").grid(row=0, column=0, sticky="e", pady=4, padx=(0, 10))
        ttk.Entry(info, textvariable=self.title_var, font=("", 10)).grid(row=0, column=1, sticky="we", pady=4)

        # Slug
        ttk.Label(info, text="Slug *:").grid(row=1, column=0, sticky="e", pady=4, padx=(0, 10))
        slug_frame = ttk.Frame(info)
        slug_frame.grid(row=1, column=1, sticky="we", pady=4)
        ttk.Entry(slug_frame, textvariable=self.slug_var, font=("", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(slug_frame, text="根据标题生成", command=self.auto_slug_from_title, width=15).pack(side=tk.LEFT, padx=8)

        # 保存路径显示
        self.path_label = ttk.Label(info, text="", foreground="#0066cc", font=("", 9))
        self.path_label.grid(row=2, column=1, sticky="w", pady=(0, 5))
        self.slug_var.trace_add("write", lambda *a: self.update_path_label())

        # 日期 / 分类 / 标签
        ttk.Label(info, text="日期:").grid(row=3, column=0, sticky="e", pady=4, padx=(0, 10))
        ttk.Entry(info, textvariable=self.date_var, width=15, font=("", 10)).grid(row=3, column=1, sticky="w", pady=4)

        ttk.Label(info, text="分类:").grid(row=4, column=0, sticky="e", pady=4, padx=(0, 10))
        ttk.Entry(info, textvariable=self.category_var, font=("", 10)).grid(row=4, column=1, sticky="we", pady=4)

        ttk.Label(info, text="标签:").grid(row=5, column=0, sticky="e", pady=4, padx=(0, 10))
        ttk.Entry(info, textvariable=self.tags_var, font=("", 10)).grid(row=5, column=1, sticky="we", pady=4)

        # 封面
        ttk.Label(info, text="封面:").grid(row=6, column=0, sticky="e", pady=4, padx=(0, 10))
        cover_row = ttk.Frame(info)
        cover_row.grid(row=6, column=1, sticky="we", pady=4)
        ttk.Entry(cover_row, textvariable=self.cover_var, font=("", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(cover_row, text="选择图片", command=self.action_select_cover, width=10).pack(side=tk.LEFT, padx=8)

        info.grid_columnconfigure(1, weight=1)

        # 内容编辑区
        content_frame = ttk.LabelFrame(right, text="  文章内容 (Markdown)  ", padding=8)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 工具按钮
        tool_bar = ttk.Frame(content_frame)
        tool_bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(tool_bar, text="🖼️ 插入图片", command=self.action_insert_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_bar, text="📎 插入链接", command=self.action_insert_link).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_bar, text="🔗 插入网盘链接", command=self.action_insert_download_link).pack(side=tk.LEFT, padx=2)
        ttk.Label(tool_bar, text="  💡 图片会自动复制到文章自己的 images 目录").pack(side=tk.LEFT, padx=5)

        self.content_text = scrolledtext.ScrolledText(
            content_frame, wrap=tk.WORD, font=("Microsoft YaHei", 11), undo=True, height=15
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)

        # ===== 底部状态栏 =====
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status_var, anchor="w", padding=(10, 4)).pack(fill=tk.X)

    # ---------------- 模式/状态 ----------------
    def set_mode(self, mode, slug=None):
        """设置当前模式（新建/编辑）"""
        self.mode = mode
        self.editing_slug = slug
        if mode == "new":
            self.mode_label.configure(text="✨ 模式：新建文章", foreground="#009933")
        else:
            self.mode_label.configure(text=f"📝 模式：编辑「{slug}」", foreground="#cc6600")

    def set_status(self, text):
        self.status_var.set(text)
        self.root.update_idletasks()

    def update_path_label(self):
        """更新显示当前文章将保存到哪里"""
        slug = self.slug_var.get().strip()
        if slug:
            path = f"  保存路径: src/content/posts/{slug}/index.md"
        else:
            path = "  保存路径: （请先填写 Slug 或标题）"
        self.path_label.configure(text=path)

    # ---------------- 工具函数 ----------------
    def safe_filename(self, name):
        name = re.sub(r"[\s\(\)\[\]\{\}\【\】（）,，]+", "_", name)
        name = re.sub(r"_+", "_", name).strip("_")
        return name or "file"

    def auto_slug_from_title(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showinfo("提示", "请先填写标题")
            return
        slug = re.sub(r"[\s\/\\:\*\?\"<>\|]+", "-", title).strip("-") or "untitled"
        self.slug_var.set(slug)

    # ---------------- 列表加载 ----------------
    def refresh_post_list(self):
        """重新扫描文章目录"""
        self.posts_listbox.delete(0, tk.END)
        posts_root = ROOT_DIR / POSTS_DIR
        if not posts_root.exists():
            posts_root.mkdir(parents=True, exist_ok=True)
            self.set_status("已创建文章目录")
            return

        entries = []
        for item in posts_root.iterdir():
            if item.is_dir() and not item.name == "images":
                if (item / "index.md").exists():
                    entries.append(item.name)
        entries.sort()

        for name in entries:
            self.posts_listbox.insert(tk.END, name)

        self.set_status(f"共发现 {len(entries)} 篇文章")

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

        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 解析 frontmatter
        self._parse_frontmatter(content)

        # 设置 slug（只读当前加载的这篇）
        self.slug_var.set(slug)
        self.set_mode("edit", slug)

        self.set_status(f"已加载文章：{slug}")

    def _parse_frontmatter(self, raw):
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.DOTALL)
        if not m:
            self.title_var.set("")
            self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
            self.category_var.set("")
            self.tags_var.set("")
            self.cover_var.set("")
            self.content_text.delete("1.0", tk.END)
            self.content_text.insert("1.0", raw)
            return

        frontmatter = m.group(1)
        body = m.group(2).strip()

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
                name = os.path.basename(value)
                self.cover_var.set(name)

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", body)

    # ---------------- 新建 ----------------
    def action_new_post(self):
        """点新建文章：清空所有输入，切换到新建模式"""
        self.title_var.set("")
        self.slug_var.set("")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.category_var.set("")
        self.tags_var.set("")
        self.cover_var.set("")
        self.content_text.delete("1.0", tk.END)
        self.posts_listbox.selection_clear(0, tk.END)

        self.set_mode("new")
        self.set_status("✨ 现在可以写一篇新文章了")

    # ---------------- 保存 ----------------
    def action_save(self):
        """保存文章（新建或编辑）"""
        title = self.title_var.get().strip()
        slug = self.slug_var.get().strip()
        date = self.date_var.get().strip()
        category = self.category_var.get().strip()
        tags = self.tags_var.get().strip()
        cover = self.cover_var.get().strip()
        body = self.content_text.get("1.0", tk.END).strip()

        # 校验
        if not title:
            messagebox.showerror("保存失败", "❌ 请先填写「标题」")
            return
        if not slug:
            # 自动从标题生成 slug
            slug = re.sub(r"[\s\/\\:\*\?\"<>\|]+", "-", title).strip("-") or "untitled"
            self.slug_var.set(slug)
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            self.date_var.set(date)

        # 检查：如果在编辑模式，但用户改了 Slug → 这会创建新目录
        if self.mode == "edit" and self.editing_slug and slug != self.editing_slug:
            if not messagebox.askyesno(
                "注意",
                f"你修改了 Slug（文章目录名）。\n\n"
                f"原目录: {self.editing_slug}\n"
                f"新目录: {slug}\n\n"
                f"是否要创建为一篇新文章？\n\n"
                f"（选『是』会在新目录创建文章，原目录保留不变）"
            ):
                return

        # 构建 frontmatter
        tag_items = [t.strip() for t in tags.split(",") if t.strip()]
        tags_line = ", ".join(f'"{t}"' for t in tag_items)

        fm = f'title: "{title}"\n'
        fm += f"published: {date}\n"
        fm += f'tags: [{tags_line}]\n'
        if category:
            fm += f"category: {category}\n"
        if cover:
            fm += f"image: ./images/{cover}\n"

        full_content = f"---\n{fm}---\n\n{body}\n"

        # 写入文件
        posts_root = ROOT_DIR / POSTS_DIR
        post_dir = posts_root / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        md_file = post_dir / "index.md"

        with open(md_file, "w", encoding="utf-8") as f:
            f.write(full_content)

        # 刷新列表并定位到这篇文章
        self.refresh_post_list()
        for i in range(self.posts_listbox.size()):
            if self.posts_listbox.get(i) == slug:
                self.posts_listbox.selection_clear(0, tk.END)
                self.posts_listbox.selection_set(i)
                self.posts_listbox.see(i)
                break

        # 切换到编辑模式
        self.set_mode("edit", slug)

        self.set_status(f"✅ 保存成功：{md_file}")

        # 询问推送
        if messagebox.askyesno(
            "保存成功",
            f"✅ 文章已保存到：\n{md_file}\n\n是否立即推送到 GitHub？\n\n"
            f"（推送后 Cloudflare 会自动更新博客）"
        ):
            self.action_git_push()

    # ---------------- 删除 ----------------
    def action_delete(self):
        sel = self.posts_listbox.curselection()
        if not sel:
            if self.mode == "edit" and self.editing_slug:
                slug = self.editing_slug
            else:
                messagebox.showwarning("提示", "请先从左侧列表选择一篇文章")
                return
        else:
            slug = self.posts_listbox.get(sel[0])

        if not messagebox.askyesno(
            "确认删除",
            f"⚠️ 确定要删除文章「{slug}」吗？\n\n"
            f"同时会删除该文章目录下的所有图片文件。\n\n"
            f"此操作不可恢复！"
        ):
            return

        post_dir = ROOT_DIR / POSTS_DIR / slug
        if post_dir.exists():
            shutil.rmtree(post_dir)

        self.action_new_post()
        self.refresh_post_list()
        self.set_status(f"🗑️ 已删除：{slug}")

        if messagebox.askyesno("删除完成", f"文章「{slug}」已删除。\n是否同步推送到 GitHub？"):
            self.action_git_push()

    # ---------------- 图片操作 ----------------
    def _ensure_images_dir(self):
        """确保当前文章的图片目录存在（用于保存前先放图片）"""
        slug = self.slug_var.get().strip()
        if not slug:
            # 尝试从标题生成
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("提示", "请先填写标题或 Slug，\n这样才能为图片创建正确的目录。")
                return None
            slug = re.sub(r"[\s\/\\:\*\?\"<>\|]+", "-", title).strip("-") or "untitled"
            self.slug_var.set(slug)

        img_dir = ROOT_DIR / POSTS_DIR / slug / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        return img_dir

    def action_select_cover(self):
        fn = filedialog.askopenfilename(
            title="选择封面图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.gif"), ("所有文件", "*.*")]
        )
        if not fn:
            return
        target_dir = self._ensure_images_dir()
        if not target_dir:
            return

        base = os.path.basename(fn)
        safe = self.safe_filename(base)
        target = target_dir / safe

        # 如果目标已存在且是同一文件，跳过
        if not (target.exists() and target.stat().st_size == os.path.getsize(fn)):
            shutil.copy2(fn, target)

        self.cover_var.set(safe)
        self.set_status(f"🖼️  封面已设置：{safe}（{target}）")

    def action_insert_image(self):
        fn = filedialog.askopenfilename(
            title="选择要插入的图片",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.gif"), ("所有文件", "*.*")]
        )
        if not fn:
            return
        target_dir = self._ensure_images_dir()
        if not target_dir:
            return

        base = os.path.basename(fn)
        safe = self.safe_filename(base)
        target = target_dir / safe

        if not (target.exists() and target.stat().st_size == os.path.getsize(fn)):
            shutil.copy2(fn, target)

        self.content_text.insert(tk.INSERT, f"\n![{safe}](./images/{safe})\n")
        self.set_status(f"🖼️  已插入图片：{safe}")

    def action_insert_link(self):
        self.content_text.insert(tk.INSERT, "[链接文本](https://)")

    def action_insert_download_link(self):
        self.content_text.insert(
            tk.INSERT,
            "\n链接：https://pan.xunlei.com/s/xxxxxx#\n提取码：xxxx\n"
        )

    # ---------------- Git 推送 ----------------
    def action_git_push(self):
        try:
            self.set_status("🔍 检查 Git 状态...")
            self.root.update()

            r = subprocess.run(
                ["git", "status", "--short"],
                cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=30
            )
            if r.returncode != 0:
                raise Exception(f"git status 失败: {r.stderr.strip() or r.stdout.strip()}")

            if not r.stdout.strip():
                messagebox.showinfo(
                    "没有改动",
                    "📭 本地文件没有新的变化，\n无需推送到 GitHub。\n\n"
                    "如果你刚保存了文章，请确认：\n1. 文件内容确实有变化\n2. Git 仓库配置正确"
                )
                self.set_status("没有需要推送的改动")
                return

            # 显示有哪些改动
            changes = r.stdout.strip()
            if not messagebox.askyesno(
                "确认推送",
                f"以下内容将推送到 GitHub：\n\n{changes}\n\n是否继续？"
            ):
                self.set_status("已取消推送")
                return

            # 执行推送
            self.set_status("📤 git add ...")
            self.root.update()
            r = subprocess.run(["git", "add", "-A"], cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=30)
            if r.returncode != 0:
                raise Exception(r.stderr.strip() or "git add 失败")

            self.set_status("📝 git commit ...")
            self.root.update()
            msg = f"更新文章：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
            r = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=30)
            if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
                raise Exception(r.stderr.strip() or "git commit 失败")

            self.set_status("🚀 git push ...")
            self.root.update()
            r = subprocess.run(["git", "push"], cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=60)
            if r.returncode != 0:
                raise Exception(r.stderr.strip() or "git push 失败")

            self.set_status("✅ 推送成功！Cloudflare 约 2-5 分钟后自动更新")
            messagebox.showinfo(
                "✅ 推送成功",
                "已成功推送到 GitHub！\n\n"
                "Cloudflare Pages 会自动检测并重新部署，\n"
                "大约 2-5 分钟后你的博客就会更新。\n\n"
                "你可以在 Cloudflare 控制台查看部署进度。"
            )

        except subprocess.TimeoutExpired:
            self.set_status("❌ 推送超时")
            messagebox.showerror("推送超时", "Git 操作超时。请检查网络连接。")
        except Exception as e:
            err = str(e)
            self.set_status("❌ 推送失败")
            messagebox.showerror(
                "推送失败",
                f"❌ Git 推送失败：\n\n{err}\n\n"
                f"请检查：\n"
                f"1. 是否已安装 Git：在命令行输入 git --version\n"
                f"2. 是否配置了 Git 账号：git config user.name / user.email\n"
                f"3. 仓库是否正确关联到 GitHub\n"
                f"4. 网络是否能访问 GitHub"
            )


if __name__ == "__main__":
    root = tk.Tk()
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = BlogManager(root)
    root.mainloop()
