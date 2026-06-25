from PIL import Image
import os
import shutil
import tempfile

files = [
    'src/content/posts/images/1_2.jpg',
    'src/content/posts/images/1_3.jpg',
    'src/content/posts/images/1_4.jpg',
    'src/content/posts/images/1_5.jpg',
    'src/content/posts/愚夜密函-W/images/17.jpg'
]

with tempfile.TemporaryDirectory() as tmpdir:
    for filepath in files:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            temp_path = os.path.join(tmpdir, filename)
            
            shutil.copy(filepath, temp_path)
            img = Image.open(temp_path)
            original_size = os.path.getsize(temp_path) / 1024 / 1024
            print(f'压缩: {filename} ({img.size[0]}x{img.size[1]}, {original_size:.1f}MB)')
            
            img.thumbnail((1920, 1920))
            img.save(temp_path, format='JPEG', quality=80)
            
            new_size = os.path.getsize(temp_path) / 1024 / 1024
            print(f'-> {new_size:.1f}MB')
            
            shutil.move(temp_path, filepath)

print('完成！')