"""Выбор области цвета для photolab.py; положите оба скрипта рядом.

Запуск: python select_sample.py data/object.jpg --bg data/bg.jpg
В первом окне: протяните рамку мышью, Enter/Space — принять, Esc — выйти.
В окне результата: N/Enter — другая рамка, S — сохранить, Q/Esc — выйти.
"""

import argparse
import json
import shlex
from pathlib import Path

import cv2
import numpy as np
import photolab as pl


def fit(image, width, height):
    h, w = image.shape[:2]
    scale = min(width / w, height / h, 1.0)
    return cv2.resize(image, (max(1, round(w * scale)), max(1, round(h * scale))),
                      interpolation=cv2.INTER_AREA)


def original_roi(roi, original_shape, displayed_shape):
    """Координаты рамки переводятся из уменьшенного окна в исходное фото."""
    x, y, w, h = roi
    if w <= 0 or h <= 0:
        return None
    oh, ow = original_shape[:2]
    dh, dw = displayed_shape[:2]
    x0 = max(0, min(ow - 1, int(np.floor(x * ow / dw))))
    y0 = max(0, min(oh - 1, int(np.floor(y * oh / dh))))
    x1 = max(x0 + 1, min(ow, int(np.ceil((x + w) * ow / dw))))
    y1 = max(y0 + 1, min(oh, int(np.ceil((y + h) * oh / dh))))
    return x0, y0, x1 - x0, y1 - y0


def panel(images, labels):
    tile_w, tile_h, title_h = 560, 350, 30
    canvas = np.full((2 * (tile_h + title_h), 2 * tile_w, 3), 245, np.uint8)
    for index, (image, label) in enumerate(zip(images, labels)):
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        small = fit(image, tile_w, tile_h)
        row, col = divmod(index, 2)
        x = col * tile_w + (tile_w - small.shape[1]) // 2
        y = row * (tile_h + title_h) + title_h + (tile_h - small.shape[0]) // 2
        canvas[y:y + small.shape[0], x:x + small.shape[1]] = small
        cv2.putText(canvas, label, (col * tile_w + 8, row * (tile_h + title_h) + 21),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 1, cv2.LINE_AA)
    return canvas


def main():
    parser = argparse.ArgumentParser(description="Выбор --sample и проверка хромакея")
    parser.add_argument("image", nargs="?", default="data/object.jpg")
    parser.add_argument("--bg", default="data/bg.jpg")
    parser.add_argument("--open", type=int, default=5, dest="open_k")
    parser.add_argument("--close", type=int, default=9, dest="close_k")
    parser.add_argument("--feather", type=float, default=2.0)
    parser.add_argument("--out-dir", default="out/roi_trials")
    args = parser.parse_args()

    image, background = pl.imread(args.image), pl.imread(args.bg)
    displayed = fit(image, 1100, 750)
    selection_window = "Draw a sample INSIDE the object; Enter/Space=accept; Esc=exit"
    result_window = "Preview: N/Enter=new sample, S=save, Q/Esc=exit"
    print("Выбирай небольшой участок цвета ВНУТРИ предмета, без фона и белого блика.")
    print("Исходный размер:", image.shape[1], "x", image.shape[0])
    attempt = 0
    try:
        while True:
            roi = cv2.selectROI(selection_window, displayed, showCrosshair=True, fromCenter=False)
            cv2.destroyWindow(selection_window)
            sample = original_roi(roi, image.shape, displayed.shape)
            if sample is None:
                break
            attempt += 1
            x, y, w, h = sample
            lo, hi = pl.hsv_box_from(image[y:y + h, x:x + w].reshape(-1, 3))
            marked = image.copy()
            cv2.rectangle(marked, (x, y), (x + w - 1, y + h - 1), (0, 255, 255), 2)
            raw = pl.color_mask(image, lo, hi, open_k=0, close_k=0)
            success = True
            try:
                composite, mask, stats = pl.chroma_key(image, background, lo, hi,
                                                      args.open_k, args.close_k, args.feather)
            except ValueError as error:
                success = False
                print("Неудачная рамка:", error)
                mask = pl.color_mask(image, lo, hi, args.open_k, args.close_k)
                composite = image.copy()
                stats = {"error": str(error)}

            sample_text = ",".join(map(str, sample))
            command = shlex.join([
                "python", str(Path(pl.__file__).resolve()), "chromakey", args.image,
                "--bg", args.bg, "--sample", sample_text,
                "--open", str(args.open_k), "--close", str(args.close_k),
                "--feather", str(args.feather), "-o", "out/object_on_bg.jpg",
                "--mask", "out/object_mask.png"])
            record = {"sample": list(sample), "lo": list(lo), "hi": list(hi),
                      "image": args.image, "bg": args.bg, "open": args.open_k,
                      "close": args.close_k, "feather": args.feather, "stats": stats,
                      "command": command}
            print("\nПопытка", attempt, "| --sample", sample_text)
            print(json.dumps(record, ensure_ascii=False, indent=2))
            print("Команда для основного задания:\n" + command)
            preview = panel([marked, raw, mask, composite],
                            ["Original + selected sample", "Raw HSV mask",
                             "Final object mask" if success else "Cleaned mask: NO object",
                             "Composite" if success else "FAILED: choose another sample"])
            cv2.imshow(result_window, preview)
            while True:
                key = cv2.waitKey(50) & 0xFF
                if cv2.getWindowProperty(result_window, cv2.WND_PROP_VISIBLE) < 1:
                    return
                if key in (27, ord("q"), ord("Q")):
                    return
                if key in (13, 10, ord("n"), ord("N")):
                    cv2.destroyWindow(result_window)
                    break
                if key in (ord("s"), ord("S")):
                    if not success:
                        print("Объект не найден — выбери другую рамку клавишей N.")
                        continue
                    directory = Path(args.out_dir)
                    directory.mkdir(parents=True, exist_ok=True)
                    stem = f"sample_{sample_text.replace(',', '_')}_open{args.open_k}_close{args.close_k}_f{args.feather:g}"
                    pl.imwrite(str(directory / (stem + "_mask.png")), mask)
                    pl.imwrite(str(directory / (stem + "_composite.png")), composite)
                    pl.imwrite(str(directory / (stem + "_preview.png")), preview)
                    (directory / (stem + ".json")).write_text(
                        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                    print("Сохранено в", directory, "|", stem)
    finally:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
