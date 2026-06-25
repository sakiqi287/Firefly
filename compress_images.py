import os
from PIL import Image

def compress_image(image_path, max_size_mb=2, max_dimension=1920, quality=80):
    try:
        img = Image.open(image_path)
        original_size = os.path.getsize(image_path) / (1024 * 1024)

        if original_size <= max_size_mb and max(img.size) <= max_dimension:
            print(f"  SKIP: {os.path.basename(image_path)} ({original_size:.1f}MB)")
            return False

        print(f"  压缩: {os.path.basename(image_path)} ({original_size:.1f}MB, {img.size[0]}x{img.size[1]})")

        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')

        width, height = img.size
        if max(img.size) > max_dimension:
            ratio = max_dimension / max(width, height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        img.save(image_path, 'JPEG', quality=quality, optimize=True)

        new_size = os.path.getsize(image_path) / (1024 * 1024)
        print(f"  -> {new_size:.1f}MB ({img.size[0]}x{img.size[1]})")
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    posts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'content', 'posts')
    total_compressed = 0
    total_saved_mb = 0

    for root, dirs, files in os.walk(posts_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_path = os.path.join(root, f)
                old_size = os.path.getsize(image_path) / (1024 * 1024)
                if compress_image(image_path):
                    new_size = os.path.getsize(image_path) / (1024 * 1024)
                    total_compressed += 1
                    total_saved_mb += (old_size - new_size)

    print(f"\n完成！共压缩 {total_compressed} 张图片，节省 {total_saved_mb:.1f} MB")

if __name__ == '__main__':
    main()
