import os

MB = 1024 * 1024

def cleanup_tmp_files(base_dir):
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith('.tmp'):
                tmp_path = os.path.join(root, f)
                original_path = tmp_path[:-4]
                if os.path.exists(original_path):
                    orig_size = os.path.getsize(original_path)
                    tmp_size = os.path.getsize(tmp_path)
                    print(f"Replacing {original_path}")
                    print(f"  Original: {orig_size/MB:.2f} MB -> New: {tmp_size/MB:.2f} MB")
                    os.remove(original_path)
                    os.rename(tmp_path, original_path)

if __name__ == '__main__':
    cleanup_tmp_files('src/content/posts')