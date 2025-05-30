import numpy as np
import imagehash
from PIL import Image
import os
import argparse
import shutil


def average_hash_from_folder(folder_path):
    hashes = []
    for filename in os.listdir(folder_path):
        path = os.path.join(folder_path, filename)
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
            try:
                img = Image.open(path)
                h = imagehash.average_hash(img, hash_size=128)
                hashes.append(h.hash.astype(np.float64))  # 핵심: 내부 numpy 배열 추출
            except Exception as e:
                print(f"[!] 해시 실패: {filename}, 에러: {e}")

    if not hashes:
        return None

    avg_hash_array = np.mean(hashes, axis=0) > 0.5  # 평균 내고 임계값 0.5 초과면 True
    return imagehash.ImageHash(avg_hash_array)


def classify_image(target_path, label_hashes, threshold):
    try:
        img = Image.open(target_path)
        img_hash = imagehash.average_hash(img, hash_size=128)

        best_label = None
        best_score = -1

        for label, ref_hash in label_hashes.items():
            diff = img_hash - ref_hash
            similarity = 1 - (diff / 128**2)
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


def classify_by_folders(target_path, template_root, result_root, threshold):
    # 1. 기준 폴더들 해시화
    label_hashes = {}
    for label in os.listdir(template_root):
        folder_path = os.path.join(template_root, label)
        if os.path.isdir(folder_path):
            h = average_hash_from_folder(folder_path)
            if h:
                label_hashes[label] = h
                print(f"[+] 기준 해시 생성됨: {label}")

    # 2. 분류
    label, score = classify_image(target_path, label_hashes, threshold)
    filename = os.path.basename(target_path)

    dst_dir = os.path.join(result_root, label)
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy(target_path, os.path.join(dst_dir, filename))
    print(f"[→] {filename} → {label} (유사도: {score:.2f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="이미지 → 기준 폴더 자동 분류")
    parser.add_argument("--dir", required=True, help="입력 이미지 (1장)")
    parser.add_argument("--template_dir", required=True, help="기준 폴더 경로 (A/B/C...)")
    parser.add_argument("--result_dir", required=True, help="출력 결과 폴더")
    parser.add_argument("--thresh_hold", type=float, default=0.7, help="유사도 기준")

    args = parser.parse_args()

    classify_by_folders(args.dir, args.template_dir, args.result_dir, args.thresh_hold)


'''
python run.py \
  --dir images/input \
  --template_dir images/reference \
  --result_dir images/output \
  --thresh_hold 0.7
'''
'''
images/input => 분류할 이미지들
images/reference => 각 기준 폴더
images/output => 분류 결과
images/output/unmatched => 유사도 낮은 이미지
'''
