import argparse
from img_classifiers import classify_multiple_images


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="이미지 → 기준 폴더 자동 분류")
    parser.add_argument("--dir", required=True, help="입력 이미지 (1장)")
    parser.add_argument("--template_dir", required=True, help="기준 폴더 경로 (A/B/C...)")
    parser.add_argument("--result_dir", required=True, help="출력 결과 폴더")
    parser.add_argument("--thresh_hold", type=float, default=0.7, help="유사도 기준")

    args = parser.parse_args()

    classify_multiple_images(args.dir, args.template_dir, args.result_dir, args.thresh_hold)


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
