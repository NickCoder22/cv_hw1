"""Метрики эталонных кадров курса. Ничего не изменяет в photolab.py.

python check_course_metrics.py mask --mask out/course/ck_mask.png
python check_course_metrics.py poster --front out/course/front640.png --gt PATH/poster-gt.png --threshold 127
Порог 127 — явно выбранное правило, а не установленное README значение.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def read_gray(path):
    file = Path(path)
    if not file.is_file():
        raise FileNotFoundError(f"Файл не найден: {path}")
    image = cv2.imdecode(np.fromfile(file, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Не удалось прочитать: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def mask_metrics(gray):
    if gray.shape != (640, 960):
        raise ValueError("Маска ball-lamp.jpg должна иметь размер 960 x 640 без масштабирования")
    if not np.isin(gray, (0, 255)).all():
        raise ValueError("Ожидалась бинарная маска 0/255; используйте PNG из --mask")
    yy, xx = np.ogrid[:640, :960]
    ground_truth = (xx - 190) ** 2 + (yy - 560) ** 2 <= 58 ** 2
    prediction = gray > 0
    tp = int(np.count_nonzero(prediction & ground_truth))
    fp = int(np.count_nonzero(prediction & ~ground_truth))
    fn = int(np.count_nonzero(~prediction & ground_truth))
    return {
        "metric": "ball_mask", "ground_truth": "(x-190)^2 + (y-560)^2 <= 58^2",
        "gt_area": int(ground_truth.sum()), "pred_area": int(prediction.sum()),
        "TP": tp, "FP": fp, "FN": fn,
        "recall_pct": round(100 * tp / (tp + fn), 4) if tp + fn else None,
        "precision_pct": round(100 * tp / (tp + fp), 4) if tp + fp else None,
    }


def poster_metrics(front, gt, threshold=127, otsu=False):
    if front.shape != gt.shape or front.shape != (905, 640):
        raise ValueError("Оба изображения должны иметь размер 640 x 905; не масштабируйте их после rectify")
    flag = cv2.THRESH_BINARY | (cv2.THRESH_OTSU if otsu else 0)
    tf, bf = cv2.threshold(front, 0 if otsu else threshold, 255, flag)
    tg, bg = cv2.threshold(gt, 0 if otsu else threshold, 255, flag)
    different = bf != bg
    report = {
        "metric": "poster_binary_match", "size": [640, 905],
        "binarization": "Otsu separately for each image" if otsu else "gray > threshold",
        "threshold_front": float(tf), "threshold_gt": float(tg),
        "compared_pixels": int(different.size),
        "different_pixels": int(different.sum()),
        "binary_match_pct": round(float(100 * (~different).mean()), 4),
    }
    return report, np.where(different, 255, 0).astype(np.uint8)


def main():
    parser = argparse.ArgumentParser(description="Проверки маски мяча и бинарного плаката")
    commands = parser.add_subparsers(dest="command", required=True)
    mask = commands.add_parser("mask")
    mask.add_argument("--mask", required=True)
    poster = commands.add_parser("poster")
    poster.add_argument("--front", required=True)
    poster.add_argument("--gt", required=True)
    methods = poster.add_mutually_exclusive_group()
    methods.add_argument("--threshold", type=int, default=127)
    methods.add_argument("--otsu", action="store_true")
    poster.add_argument("--diff", help="PNG: белым обозначены несовпавшие пиксели")
    args = parser.parse_args()
    if args.command == "mask":
        report = mask_metrics(read_gray(args.mask))
    else:
        if not 0 <= args.threshold <= 255:
            raise ValueError("Порог должен быть в диапазоне 0..255")
        report, diff = poster_metrics(read_gray(args.front), read_gray(args.gt), args.threshold, args.otsu)
        if args.diff:
            path = Path(args.diff)
            path.parent.mkdir(parents=True, exist_ok=True)
            ok, buf = cv2.imencode(path.suffix or ".png", diff)
            if not ok:
                raise ValueError("Не удалось сохранить карту различий")
            buf.tofile(path)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

