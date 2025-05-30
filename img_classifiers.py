import os

import shutil
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
import imagehash


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




def calc_diff(template_path, target_hash):
    try:
        template_image = Image.open(template_path)
        template_hash = imagehash.average_hash(template_image, hash_size=128)
        diff = target_hash - template_hash
        similarity_percentage = 1 - (diff / 128**2)
        return template_path, similarity_percentage
    except Exception as e:
        print(f"이미지 로드 실패: {template_path}, 에러: {e}")
        return template_path, float("inf")


def classify_by_hash(dir, template_dir, result_dir, thresh_hold):
    timage = Image.open(dir)
    target_hash = imagehash.average_hash(timage, hash_size=128)

    image_files = [
        os.path.join(template_dir, filename)
        for filename in os.listdir(template_dir)
        if filename.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff"))
    ]#이미지 해시화

    # 결과 저장 경로 생성
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    # 결과 저장 경로 생성

    with ThreadPoolExecutor() as executor:
        # 병렬로 작업 실행
        results = executor.map(calc_diff, image_files, [target_hash] * len(image_files))

        for template_path, similarity_percentage in results:
            if similarity_percentage > thresh_hold:
                try:
                    # 유사한 이미지 저장 (파일명에 일치율 포함)
                    filename = os.path.basename(template_path)
                    name, ext = os.path.splitext(filename)
                    new_filename = f"{name}_similarity_{similarity_percentage:.2f}{ext}"
                    destination_path = os.path.join(result_dir, new_filename)
                    shutil.copy(template_path, destination_path)
                    print(
                        f"유사 이미지 저장: {destination_path} (차이: {similarity_percentage})"
                    )
                except Exception as e:
                    print(f"이미지 복사 실패: {template_path}, 에러: {e}")
            else:
                try:
                    # 유사한 이미지 저장 (파일명에 일치율 포함)
                    filename = os.path.basename(template_path)
                    name, ext = os.path.splitext(filename)
                    new_filename = f"{name}_similarity_{similarity_percentage:.2f}{ext}"
                    destination_path = os.path.join(result_dir, new_filename)
                    shutil.copy(template_path, destination_path)
                    print(
                        f"유사 이미지 저장: {destination_path} (차이: {similarity_percentage})"
                    )
                except Exception as e:
                    print(f"이미지 복사 실패: {template_path}, 에러: {e}")


