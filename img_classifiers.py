import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import imagehash
import glob

def ensure_output_structure(template_dir, result_dir):
    os.makedirs(os.path.join(result_dir, "unmatched"), exist_ok=True)
    for root, dirs, _ in os.walk(template_dir):
        for dir_name in dirs:
            rel_path = os.path.relpath(os.path.join(root, dir_name), template_dir)
            target_path = os.path.join(result_dir, rel_path)
            os.makedirs(target_path, exist_ok=True)

def classify_folder_batch(target_image_path, template_dir, result_dir, thresh_hold, progress_callback=None):
    target_image = Image.open(target_image_path)
    target_hash = imagehash.average_hash(target_image, hash_size=128)

    image_files = glob.glob(os.path.join(template_dir, "**", "*.*"), recursive=True)
    image_files = [f for f in image_files if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff"))]

    if not image_files:
        print(f"[!] 템플릿 디렉토리에 이미지 파일이 없습니다: {template_dir}")
        return

    best_match = None
    best_score = -1

    for template_path in image_files:
        try:
            template_image = Image.open(template_path)
            template_hash = imagehash.average_hash(template_image, hash_size=128)
            diff = target_hash - template_hash
            similarity = 1 - (diff / 128**2)
            print(f"[→] {os.path.basename(template_path)}: 유사도 {similarity:.2f}")

            if similarity > best_score:
                best_score = similarity
                best_match = template_path
        except Exception as e:
            print(f"[!] 비교 실패: {template_path}, 에러: {e}")

        # 저장 로직
    filename = os.path.basename(target_image_path)

    if best_match and best_score >= thresh_hold:
        rel_path = os.path.relpath(best_match, template_dir)
        top_folder = rel_path.split(os.sep)[0]

        output_dir = os.path.join(result_dir, top_folder)
        os.makedirs(output_dir, exist_ok=True)

        shutil.copy(target_image_path, os.path.join(output_dir, filename))
        print(f"[✓] 저장됨: {os.path.join(output_dir, filename)} (유사도: {best_score:.2f})")
    else:
        unmatched_dir = os.path.join(result_dir, "unmatched")
        os.makedirs(unmatched_dir, exist_ok=True)
        shutil.copy(target_image_path, os.path.join(unmatched_dir, filename))
        print(f"[→] 유사도 미달로 unmatched에 저장됨 (최고 유사도: {best_score:.2f})")

    if progress_callback:
        progress_callback()

def _task(args):
    image_path, template_dir, result_dir, threshold, callback = args
    classify_folder_batch(image_path, template_dir, result_dir, threshold, callback)

def classify_multiple_images(dir, template_dir, result_dir, threshold, progress_callback=None):
    if not os.path.exists(dir):
        print(f"[!] 입력 디렉토리가 존재하지 않습니다: {dir}")
        return

    ensure_output_structure(template_dir, result_dir)

    image_paths = [
        os.path.join(dir, filename)
        for filename in os.listdir(dir)
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff"))
    ]

    tasks = [(img_path, template_dir, result_dir, threshold, progress_callback) for img_path in image_paths]

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(_task, tasks)