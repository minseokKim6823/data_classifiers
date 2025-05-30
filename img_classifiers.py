import os
import shutil
from concurrent.futures import ProcessPoolExecutor
from PIL import Image
import imagehash
import glob


def classify_image(target_path, label_hashes, threshold): # 해시값 기반 분류
    try:
        img = Image.open(target_path)
        img_hash = imagehash.average_hash(img, hash_size=128)

        best_label = None
        best_score = -1

        for label, ref_hash in label_hashes.items():
            diff = img_hash - ref_hash
            similarity = 1 - (diff / 16**2)
            print(f"[DEBUG] {label} 유사도: {similarity:.2f}")
            if similarity > best_score:
                best_score = similarity
                best_label = label

        if best_score < threshold:
            return "unmatched", best_score
        return best_label, best_score
    except Exception as e:
        print(f"[!] 이미지 분류 실패: {target_path}, 에러: {e}")
        return "unmatched", 0

def calc_diff(template_path, target_hash):
    try:
        template_image = Image.open(template_path)
        template_hash = imagehash.average_hash(template_image, hash_size=128)
        diff = target_hash - template_hash
        similarity_percentage = 1 - (diff / 128**2)
        return template_path, similarity_percentage
    except Exception as e:
        print(f"이미지 로드 실패: {template_path}, 에러: {e}")
        return template_path, -1

def classify_folder_batch(target_image_path, template_dir, result_dir, thresh_hold):
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
        # ✅ 가장 유사한 reference 이미지의 상위 폴더명
        rel_path = os.path.relpath(best_match, template_dir)
        top_folder = rel_path.split(os.sep)[0]  # ex: '소득금액증명'

        output_dir = os.path.join(result_dir, top_folder)
        os.makedirs(output_dir, exist_ok=True)

        shutil.copy(target_image_path, os.path.join(output_dir, filename))
        print(f"[✓] 저장됨: {os.path.join(output_dir, filename)} (유사도: {best_score:.2f})")
    else:
        unmatched_dir = os.path.join(result_dir, "unmatched")
        os.makedirs(unmatched_dir, exist_ok=True)
        shutil.copy(target_image_path, os.path.join(unmatched_dir, filename))
        print(f"[→] 유사도 미달로 unmatched에 저장됨 (최고 유사도: {best_score:.2f})")


def classify_multiple_images(dir, template_dir, result_dir, threshold):
    if not os.path.exists(dir):
        print(f"[!] 입력 디렉토리가 존재하지 않습니다: {dir}")
        return

    image_paths = [
        os.path.join(dir, filename)
        for filename in os.listdir(dir)
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff"))
    ]

    from functools import partial
    task = partial(classify_folder_batch, template_dir=template_dir, result_dir=result_dir, thresh_hold=threshold)


    with ProcessPoolExecutor(max_workers=4) as executor:
        executor.map(task, image_paths)

