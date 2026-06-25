import os
from PIL import Image

def compress_image(input_path, max_size_mb=8, max_dim=1920):
    try:
        img = Image.open(input_path)
        original_size = os.path.getsize(input_path)
        original_size_mb = original_size / (1024 * 1024)
        
        if original_size_mb <= max_size_mb:
            return None
        
        w, h = img.size
        scale = min(max_dim / w, max_dim / h, 1)
        
        if scale < 1:
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)
        
        quality = 85
        ext = os.path.splitext(input_path)[1].lower()
        tmp_path = input_path + ".tmp"
        
        if ext == '.png':
            img.save(tmp_path, optimize=True)
        else:
            img.save(tmp_path, quality=quality, optimize=True)
        
        new_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        
        if new_size_mb > max_size_mb:
            while new_size_mb > max_size_mb and quality > 10:
                quality -= 10
                if ext == '.png':
                    img.save(tmp_path, optimize=True)
                else:
                    img.save(tmp_path, quality=quality, optimize=True)
                new_size_mb = os.path.getsize(tmp_path) / (1024 * 1024)
        
        os.remove(input_path)
        os.rename(tmp_path, input_path)
        return (original_size_mb, new_size_mb)
    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return None

def main():
    base_dir = 'src/content/posts'
    extensions = ('.jpg', '.jpeg', '.png')
    total_original = 0
    total_new = 0
    count = 0
    
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.lower().endswith(extensions):
                if f.endswith('.tmp'):
                    continue
                filepath = os.path.join(root, f)
                result = compress_image(filepath)
                if result:
                    orig, new = result
                    saved = orig - new
                    print(f"Compressed: {filepath}")
                    print(f"  {orig:.2f} MB -> {new:.2f} MB (saved {saved:.2f} MB)")
                    total_original += orig
                    total_new += new
                    count += 1
    
    print(f"\nTotal processed: {count} files")
    print(f"Total original: {total_original:.2f} MB")
    print(f"Total new: {total_new:.2f} MB")
    print(f"Total saved: {total_original - total_new:.2f} MB")

if __name__ == '__main__':
    main()