import os
import re

POSTS_DIR = r"d:\2\Firefly\src\content\posts"

BTN_XUNLEI = (
    '<a href="{href}" target="_blank" rel="noopener noreferrer" '
    'style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
    'background:linear-gradient(135deg,#2196F3,#1976D2);color:#fff;border-radius:8px;'
    'text-decoration:none;font-weight:600;box-shadow:0 2px 8px rgba(33,150,243,0.3);'
    'transition:transform .2s,box-shadow .2s;" '
    'onmouseover="this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 4px 12px rgba(33,150,243,0.4)\'" '
    'onmouseout="this.style.transform=\'translateY(0)\';this.style.boxShadow=\'0 2px 8px rgba(33,150,243,0.3)\'">'
    '<span>🌩️</span><span>迅雷下载</span></a>'
)

BTN_QUARK = (
    '<a href="{href}" target="_blank" rel="noopener noreferrer" '
    'style="display:inline-flex;align-items:center;gap:8px;padding:10px 20px;'
    'background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;border-radius:8px;'
    'text-decoration:none;font-weight:600;box-shadow:0 2px 8px rgba(102,126,234,0.3);'
    'transition:transform .2s,box-shadow .2s;" '
    'onmouseover="this.style.transform=\'translateY(-2px)\';this.style.boxShadow=\'0 4px 12px rgba(102,126,234,0.4)\'" '
    'onmouseout="this.style.transform=\'translateY(0)\';this.style.boxShadow=\'0 2px 8px rgba(102,126,234,0.3)\'">'
    '<span>🌀</span><span>夸克下载</span></a>'
)

BTN_WRAP_START = '<div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">'
BTN_WRAP_END = '</div>'


def convert_post(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # 提取迅雷链接（不管前缀文字是什么，直接匹配URL）
    xunlei_url = None
    quark_url = None
    extract_code = None

    xunlei_all = re.findall(r'https?://pan\.xunlei\.com/s/[^\s#"\'>)]+', content)
    if xunlei_all:
        xunlei_url = xunlei_all[0].rstrip('#')

    # 提取夸克链接
    quark_all = re.findall(r'https?://pan\.quark\.cn/s/[^\s#"\'>)\n]+', content)
    if quark_all:
        quark_url = quark_all[0].rstrip('#')

    # 找提取码
    pwd_m = re.search(r'(?:提取码|密码|解压码|pwd)[:：=]?\s*([A-Za-z0-9]{4,8})', content, re.IGNORECASE)
    if pwd_m:
        extract_code = pwd_m.group(1)

    # 没有链接则跳过
    if not xunlei_url and not quark_url:
        return False

    # 检查是否需要更新：已有的按钮URL没问题且没有末尾#，则跳过
    has_btn = 'style="display:inline-flex' in content
    old_hash = re.search(r'href="(https?://pan\.xunlei\.com/s/[^"]+#)"', content)
    if has_btn and not old_hash:
        # 已有按钮且没有#号问题，检查是否有遗漏的纯文本链接
        leftover_link = re.search(r'^\s*(?:迅雷链接|夸克链接|迅雷下载|链接|迅雷|夸克)[:：]\s*https?://', content, re.MULTILINE)
        if not leftover_link:
            return False

    # 构建按钮 HTML
    buttons_html = BTN_WRAP_START
    if xunlei_url:
        buttons_html += BTN_XUNLEI.format(href=xunlei_url)
    if quark_url:
        buttons_html += BTN_QUARK.format(href=quark_url)
    buttons_html += BTN_WRAP_END

    if extract_code and extract_code not in ('迅雷链接', '夸克链接', '链接'):
        buttons_html += f'\n<p style="margin-top:8px;color:#666;font-size:14px;">提取码：<code style="background:#f5f5f5;padding:2px 8px;border-radius:4px;">{extract_code}</code></p>'

    # 清理旧按钮HTML
    new_content = re.sub(
        r'<div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">.*?</div>\s*(?:<p[^>]*>提取码.*?</p>)?',
        '',
        content,
        flags=re.DOTALL
    )

    # 删除纯文本链接行
    new_content = re.sub(
        r'^\s*(?:迅雷链接|夸克链接|迅雷下载|百度网盘链接|阿里云盘链接|链接|迅雷|夸克)[:：]\s*https?://[^\s]+\s*$\n?',
        '',
        new_content,
        flags=re.MULTILINE
    )

    # 删除提取码行
    if extract_code:
        new_content = re.sub(
            rf'^\s*(?:提取码|密码|解压码|pwd)[:：=]?\s*{re.escape(extract_code)}\s*$\n?',
            '',
            new_content,
            flags=re.MULTILINE | re.IGNORECASE
        )

    # 删除迅雷App分享行
    new_content = re.sub(r'^.*复制这段内容后打开手机迅雷App.*$\n?', '', new_content, flags=re.MULTILINE)

    # 在第一张封面图后插入按钮
    parts = new_content.split('---', 2)
    if len(parts) >= 3:
        fm_start = parts[0]
        fm_body = parts[1]
        after_fm = parts[2]
        img_match = re.search(r'!\[.*?\]\(.*?\)', after_fm)
        if img_match:
            img_end = img_match.end()
            newline_after_img = after_fm.find('\n', img_end)
            if newline_after_img == -1:
                newline_after_img = len(after_fm)
            insert_pos = newline_after_img
            after_fm_new = after_fm[:insert_pos] + '\n\n' + buttons_html + '\n\n' + after_fm[insert_pos:].lstrip('\n')
        else:
            after_fm_new = '\n' + buttons_html + '\n\n' + after_fm.lstrip('\n')
        final_content = fm_start + '---' + fm_body + '---' + after_fm_new
    else:
        final_content = new_content + '\n\n' + buttons_html + '\n'

    # 清理多余空行
    final_content = re.sub(r'\n{4,}', '\n\n\n', final_content)

    if final_content.strip() == original.strip():
        return False

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    return True


def main():
    count = 0
    skipped = 0
    errors = 0
    for name in os.listdir(POSTS_DIR):
        md_path = os.path.join(POSTS_DIR, name, "index.md")
        if not os.path.exists(md_path):
            continue
        try:
            changed = convert_post(md_path)
            if changed:
                count += 1
                print(f"✓ 更新: {name}")
            else:
                skipped += 1
                print(f"○ 跳过: {name}")
        except Exception as e:
            errors += 1
            print(f"✗ 错误: {name} - {e}")

    print(f"\n完成: 更新 {count} 个, 跳过 {skipped} 个, 错误 {errors} 个")


if __name__ == "__main__":
    main()
