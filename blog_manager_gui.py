#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绘鱼博客管理工具 v2.1
支持：新建文章 / 编辑文章 / 删除文章 / 封面设置 / 图片插入 / 一键 Git 推送
所有耗时操作（扫描目录、删除、Git）均在后台线程执行，不会卡死窗口。
"""

import os
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path

# ========= 配置 =========
POSTS_DIR = "src/content/posts"

# 打包后自动定位博客根目录（包含 src/content/posts 的目录）
import sys

def _find_blog_root():
    # 1. 开发模式：脚本所在目录
    script_dir = Path(__file__).resolve().parent

    # 2. 打包模式：exe 所在目录
    if getattr(sys, "frozen", False):
        script_dir = Path(sys.executable).resolve().parent

    # 3. 逐级往上找 src/content/posts
    search_dirs = [script_dir]
    for parent in script_dir.parents:
        search_dirs.append(parent)

    for d in search_dirs:
        if (d / POSTS_DIR).exists():
            return d

    # 4. 找不到就弹框让用户选
    root = tk.Tk()
    root.withdraw()
    result = filedialog.askdirectory(title="请选择博客根目录（包含 src/content/posts 的文件夹）")
    root.destroy()
    if not result:
        messagebox.showerror("错误", "未选择博客目录，程序退出。")
        sys.exit(1)
    return Path(result)

ROOT_DIR = _find_blog_root()


# ========= 主程序 =========
class BlogManager:
    def __init__(self, root):
        self.root = root
        self.root.title("绘鱼博客管理工具")
        self.root.geometry("1300x860")
        self.root.minsize(1100, 650)

        # 当前模式
        self.mode = "new"          # "new" 或 "edit"
        self.editing_slug = None   # 当前编辑中文章的原始 slug
        self._post_cache = []      # 文章列表缓存（避免重复扫描）

        self._build_ui()
        self.root.after(200, self.refresh_post_list)
        self.root.after(300, lambda: self.set_mode("new"))

    # ---------- UI 构建 ----------
    def _build_ui(self):
        # 顶部标题 + 模式显示
        header = ttk.Frame(self.root, padding=(12, 8))
        header.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(header, text="📖 绘鱼博客管理工具", font=("", 14, "bold")).pack(side=tk.LEFT)
        self.mode_label = ttk.Label(header, text="", font=("", 11))
        self.mode_label.pack(side=tk.LEFT, padx=20)

        # 工具栏
        toolbar = ttk.Frame(self.root, padding=(10, 4))
        toolbar.pack(side=tk.TOP, fill=tk.X)
        bs = {"width": 14}
        ttk.Button(toolbar, text="✨ 新建文章", command=self.action_new_post, **bs).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="💾 保存文章", command=self.action_save, **bs).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🗑️ 删除当前", command=self.action_delete, **bs).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🔄 刷新列表", command=self.refresh_post_list, **bs).pack(side=tk.LEFT, padx=3)
        ttk.Button(toolbar, text="🚀 推送到 GitHub", command=self.action_git_push, **bs).pack(side=tk.LEFT, padx=10)

        # 主体（双栏布局）
        main = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 左侧：文章列表
        left = ttk.Frame(main, width=280)
        main.add(left, weight=0)
        ttk.Label(left, text="📚 已有文章", font=("", 11, "bold")).pack(pady=(5, 3))
        list_frame = ttk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.posts_listbox = tk.Listbox(list_frame, font=("", 10))
        self.posts_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.posts_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.posts_listbox.config(yscrollcommand=sb.set)
        self.posts_listbox.bind("<<ListboxSelect>>", self.on_select_post)
        ttk.Label(left, text="💡 点击文章进行编辑", foreground="#888", font=("", 9)).pack(pady=5)

        # 右侧：编辑区
        right = ttk.Frame(main)
        main.add(right, weight=1)

        # 文章信息面板
        info = ttk.LabelFrame(right, text="  文章信息  ", padding=12)
        info.pack(fill=tk.X, padx=5, pady=5)

        self.title_var = tk.StringVar()
        self.slug_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.tags_var = tk.StringVar()
        self.cover_var = tk.StringVar()

        def add_row(label_text, var, row, with_gen_button=False):
            ttk.Label(info, text=label_text).grid(row=row, column=0, sticky="e", pady=4, padx=(0, 10))
            box = ttk.Frame(info)
            box.grid(row=row, column=1, sticky="we", pady=4)
            ent = ttk.Entry(box, textvariable=var, font=("", 10))
            ent.pack(side=tk.LEFT, fill=tk.X, expand=True)
            if with_gen_button:
                ttk.Button(box, text="根据标题生成", command=self.auto_slug_from_title, width=15).pack(side=tk.LEFT, padx=8)

        add_row("标题 *:", self.title_var, 0)
        add_row("Slug *:", self.slug_var, 1, with_gen_button=True)

        # 保存路径提示（在 Slug 下面新增一行）
        self.path_label = ttk.Label(info, text="  保存路径: （请先填写标题或 Slug）", foreground="#0066cc", font=("", 9))
        self.path_label.grid(row=2, column=1, sticky="w", pady=(0, 5))

        add_row("日期:", self.date_var, 3)
        add_row("分类:", self.category_var, 4)
        add_row("标签:", self.tags_var, 5)
        add_row("封面:", self.cover_var, 6)

        # 在封面行右边加一个“选择图片”按钮
        cover_children = info.grid_slaves(row=6, column=1)
        if cover_children:
            # 找到刚才放进去的 Entry 所在的 Frame
            cover_box = cover_children[0]
            for child in cover_box.winfo_children():
                if isinstance(child, ttk.Entry):
                    # 在 entry 后面加个“选择图片”按钮
                    ttk.Button(cover_box, text="选择图片", command=self.action_select_cover, width=10).pack(side=tk.LEFT, padx=8)
                    break

        info.grid_columnconfigure(1, weight=1)

        # 内容编辑区
        content_frame = ttk.LabelFrame(right, text="  文章内容 (Markdown)  ", padding=8)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tool_bar = ttk.Frame(content_frame)
        tool_bar.pack(fill=tk.X, pady=(0, 6))
        ttk.Button(tool_bar, text="🖼️ 插入图片", command=self.action_insert_image).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_bar, text="📎 插入链接", command=self.action_insert_link).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_bar, text="🔗 插入网盘链接", command=self.action_insert_download_link).pack(side=tk.LEFT, padx=2)
        ttk.Label(tool_bar, text="  💡 图片自动复制到文章自己的 images 目录", foreground="#666").pack(side=tk.LEFT, padx=5)

        self.content_text = scrolledtext.ScrolledText(
            content_frame, wrap=tk.WORD, font=("Microsoft YaHei", 11), undo=True, height=15
        )
        self.content_text.pack(fill=tk.BOTH, expand=True)

        # 底部状态栏
        self.status_var = tk.StringVar(value="准备就绪")
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        ttk.Label(status_bar, textvariable=self.status_var, anchor="w", padding=(10, 4)).pack(fill=tk.X)

        # 绑定 Slug 变化（实时提示保存路径）
        self.slug_var.trace_add("write", self._on_slug_changed)

    # ---------- 状态/模式 ----------
    def set_status(self, text):
        self.status_var.set(text)

    def set_mode(self, mode, slug=None):
        self.mode = mode
        self.editing_slug = slug
        if mode == "new":
            self.mode_label.configure(text="✨ 模式：新建文章", foreground="#009933")
        else:
            self.mode_label.configure(text=f"📝 模式：编辑「{slug}」", foreground="#cc6600")

    def _on_slug_changed(self, *args):
        slug = self.slug_var.get().strip()
        if slug:
            self.path_label.configure(text=f"  保存路径: src/content/posts/{slug}/index.md")
        else:
            self.path_label.configure(text="  保存路径: （请先填写标题或 Slug）")

    # ---------- 工具函数 ----------
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

    # ---------- 列表加载 ----------
    def refresh_post_list(self):
        """后台扫描文章目录，不卡主线程"""
        self.set_status("🔍 正在扫描文章...")

        def worker():
            entries = []
            posts_root = ROOT_DIR / POSTS_DIR
            if posts_root.exists():
                try:
                    for item in posts_root.iterdir():
                        if item.is_dir() and item.name != "images":
                            if (item / "index.md").exists():
                                entries.append(item.name)
                except Exception:
                    pass
                entries.sort()
            self.root.after(0, lambda: self._update_list_ui(entries))

        threading.Thread(target=worker, daemon=True).start()

    def _update_list_ui(self, entries):
        self.posts_listbox.delete(0, tk.END)
        for name in entries:
            self.posts_listbox.insert(tk.END, name)
        self._post_cache = list(entries)
        self.set_status(f"共发现 {len(entries)} 篇文章")

    # ---------- 选中文章 ----------
    def on_select_post(self, event=None):
        sel = self.posts_listbox.curselection()
        if not sel:
            return
        slug = self.posts_listbox.get(sel[0])
        self._load_post(slug)

    def _load_post(self, slug):
        md_file = ROOT_DIR / POSTS_DIR / slug / "index.md"
        if not md_file.exists():
            messagebox.showerror("错误", f"找不到文章文件：{md_file}")
            return
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("读取失败", str(e))
            return

        self._parse_frontmatter(content)
        self.slug_var.set(slug)
        self.set_mode("edit", slug)
        self.set_status(f"已加载：{slug}")

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
                self.cover_var.set(os.path.basename(value))

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", body)

    # ---------- 新建 ----------
    def action_new_post(self):
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

    # ---------- 保存 ----------
    def action_save(self):
        title = self.title_var.get().strip()
        slug = self.slug_var.get().strip()
        date = self.date_var.get().strip()
        category = self.category_var.get().strip()
        tags = self.tags_var.get().strip()
        cover = self.cover_var.get().strip()
        body = self.content_text.get("1.0", tk.END).strip()

        if not title:
            messagebox.showerror("保存失败", "❌ 请先填写「标题」")
            return
        if not slug:
            slug = re.sub(r"[\s\/\\:\*\?\"<>\|]+", "-", title).strip("-") or "untitled"
            self.slug_var.set(slug)
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            self.date_var.set(date)

        # 编辑模式下修改了 Slug → 警告
        if self.mode == "edit" and self.editing_slug and slug != self.editing_slug:
            if not messagebox.askyesno(
                "注意",
                f"你修改了 Slug（文章目录名）。\n\n"
                f"原目录: {self.editing_slug}\n新目录: {slug}\n\n"
                f"是否创建为新文章？（原目录保留不变）"
            ):
                return

        # 构建 frontmatter
        tag_items = [t.strip() for t in tags.split(",") if t.strip()]
        tags_line = ", ".join(f'"{t}"' for t in tag_items)

        fm = f'title: "{title}"\npublished: {date}\ntags: [{tags_line}]\n'
        if category:
            fm += f"category: {category}\n"
        if cover:
            fm += f"image: ./images/{cover}\n"
        full_content = f"---\n{fm}---\n\n{body}\n"

        # 写文件
        posts_root = ROOT_DIR / POSTS_DIR
        post_dir = posts_root / slug
        post_dir.mkdir(parents=True, exist_ok=True)
        md_file = post_dir / "index.md"

        try:
            with open(md_file, "w", encoding="utf-8") as f:
                f.write(full_content)
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return

        # 切换到编辑模式
        self.set_mode("edit", slug)
        self.set_status(f"✅ 保存成功：{md_file}")

        # 增量更新列表
        if slug not in self._post_cache:
            self._post_cache.append(slug)
            self._post_cache.sort()
            self.posts_listbox.delete(0, tk.END)
            for name in self._post_cache:
                self.posts_listbox.insert(tk.END, name)

        # 选中刚保存的那篇
        for i in range(self.posts_listbox.size()):
            if self.posts_listbox.get(i) == slug:
                self.posts_listbox.selection_clear(0, tk.END)
                self.posts_listbox.selection_set(i)
                self.posts_listbox.see(i)
                break

        if messagebox.askyesno("保存成功", f"✅ 文章已保存到：\n{md_file}\n\n是否立即推送到 GitHub？"):
            self.action_git_push()

    # ---------- 删除 ----------
    def action_delete(self):
        sel = self.posts_listbox.curselection()
        slug = None
        if sel:
            slug = self.posts_listbox.get(sel[0])
        elif self.mode == "edit" and self.editing_slug:
            slug = self.editing_slug

        if not slug:
            messagebox.showwarning("提示", "请先从左侧列表选择一篇文章")
            return

        if not messagebox.askyesno(
            "确认删除",
            f"⚠️ 确定要删除文章「{slug}」吗？\n\n同时会删除该文章目录下的所有图片。\n\n此操作不可恢复！"
        ):
            return

        post_dir = ROOT_DIR / POSTS_DIR / slug
        if not post_dir.exists():
            messagebox.showinfo("提示", "目录不存在，无需删除")
            return

        # 后台线程删除（避免大目录删除卡死窗口）
        self.set_status(f"🗑️ 正在删除：{slug}")

        def delete_worker():
            try:
                shutil.rmtree(post_dir)
                self.root.after(0, lambda: self._after_delete(slug))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("删除失败", str(e)))
                self.root.after(0, lambda: self.set_status("❌ 删除失败"))

        threading.Thread(target=delete_worker, daemon=True).start()

    def _after_delete(self, slug):
        if slug in self._post_cache:
            self._post_cache.remove(slug)
        for i in range(self.posts_listbox.size()):
            if self.posts_listbox.get(i) == slug:
                self.posts_listbox.delete(i)
                break

        self.action_new_post()
        self.set_status(f"🗑️ 已删除：{slug}")

        if messagebox.askyesno("删除完成", f"文章「{slug}」已删除。\n是否推送到 GitHub？"):
            self.action_git_push()

    # ---------- 图片 ----------
    def _ensure_images_dir(self):
        slug = self.slug_var.get().strip()
        if not slug:
            title = self.title_var.get().strip()
            if not title:
                messagebox.showerror("提示", "请先填写标题或 Slug")
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

        safe = self.safe_filename(os.path.basename(fn))
        target = target_dir / safe
        try:
            if not (target.exists() and target.stat().st_size == os.path.getsize(fn)):
                shutil.copy2(fn, target)
        except Exception as e:
            messagebox.showerror("复制失败", str(e))
            return

        self.cover_var.set(safe)
        self.set_status(f"🖼️  封面已设置：{safe}")

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

        safe = self.safe_filename(os.path.basename(fn))
        target = target_dir / safe
        try:
            if not (target.exists() and target.stat().st_size == os.path.getsize(fn)):
                shutil.copy2(fn, target)
        except Exception as e:
            messagebox.showerror("复制失败", str(e))
            return

        self.content_text.insert(tk.INSERT, f"\n![{safe}](./images/{safe})\n")
        self.set_status(f"🖼️  已插入图片：{safe}")

    def action_insert_link(self):
        self.content_text.insert(tk.INSERT, "[链接文本](https://)")

    def action_insert_download_link(self):
        self.content_text.insert(tk.INSERT, "\n链接：https://pan.xunlei.com/s/xxxxxx#\n提取码：xxxx\n")

    # ---------- Git 推送 ----------
    def action_git_push(self):
        """入口：先在后台线程执行 git status，再回主线程弹出确认框"""
        self.set_status("🔍 检查 Git 状态...")

        def worker():
            try:
                r = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=30
                )
                if r.returncode != 0:
                    err = r.stderr.strip() or "git status 失败（可能未初始化 Git 仓库？）"
                    self.root.after(0, lambda: self._git_fail(err))
                    return
                if not r.stdout.strip():
                    self.root.after(
                        0,
                        lambda: (
                            messagebox.showinfo("没有改动", "📭 本地文件没有变化，无需推送到 GitHub。"),
                            self.set_status("没有需要推送的改动")
                        )
                    )
                    return
                changes = r.stdout.strip()
                self.root.after(0, lambda: self._git_confirm_and_push(changes))
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self._git_fail("Git 操作超时，请检查网络连接。"))
            except Exception as e:
                self.root.after(0, lambda: self._git_fail(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _git_confirm_and_push(self, changes):
        """主线程弹确认框，确认后在后台线程继续推送"""
        if not messagebox.askyesno("确认推送", f"以下内容将推送到 GitHub：\n\n{changes}\n\n是否继续？"):
            self.set_status("已取消推送")
            return

        def push_worker():
            try:
                self.root.after(0, lambda: self.set_status("📤 git add ..."))
                r = subprocess.run(["git", "add", "-A"], cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=30)
                if r.returncode != 0:
                    raise Exception(r.stderr.strip() or "git add 失败")

                self.root.after(0, lambda: self.set_status("📝 git commit ..."))
                msg = f"更新文章：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
                r = subprocess.run(["git", "commit", "-m", msg], cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=30)
                if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
                    raise Exception(r.stderr.strip() or "git commit 失败")

                self.root.after(0, lambda: self.set_status("🚀 git push ..."))
                r = subprocess.run(["git", "push"], cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=120)
                if r.returncode != 0:
                    raise Exception(r.stderr.strip() or "git push 失败（可能未关联远程仓库？）")

                self.root.after(0, self._git_success)
            except subprocess.TimeoutExpired:
                self.root.after(0, lambda: self._git_fail("Git 操作超时，请检查网络连接。"))
            except Exception as e:
                self.root.after(0, lambda: self._git_fail(str(e)))

        threading.Thread(target=push_worker, daemon=True).start()

    def _git_success(self):
        self.set_status("✅ 推送成功！Cloudflare 约 2-5 分钟后自动更新")
        messagebox.showinfo(
            "✅ 推送成功",
            "已成功推送到 GitHub！\n\nCloudflare Pages 会自动重新部署，\n大约 2-5 分钟后博客就会更新。"
        )

    def _git_fail(self, err):
        self.set_status("❌ 推送失败")
        messagebox.showerror(
            "推送失败",
            f"❌ {err}\n\n请检查：\n1. 是否已安装 Git\n2. 仓库是否已初始化（git init）\n3. 是否已关联远程仓库（git remote add origin ...）\n4. 是否配置了 Git 账号\n5. 网络是否能访问 GitHub"
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
