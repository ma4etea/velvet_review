from pathlib import Path
import cv2
from src.logging_config import logger


# def image_filter(image):
#     # --- Локальный контраст CLAHE ---
#     lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
#     l_channel, a_channel, b_channel = cv2.split(lab)
#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
#     l_channel_ = clahe.apply(l_channel)
#     lab = cv2.merge((l_channel_, a_channel, b_channel))
#     img_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
#
#     # --- Уменьшение шума ---
#     img_denoised = cv2.fastNlMeansDenoisingColored(img_enhanced, None, 10, 10, 7, 21)
#
#     # --- Лёгкая резкость через Unsharp Masking ---
#     blurred = cv2.GaussianBlur(img_denoised, (0, 0), 3)
#     img_sharp = cv2.addWeighted(img_denoised, 1.5, blurred, -0.5, 0)
#
#     return img_sharp


def resized_images(*sizes: int, src_file_path: str, dst_folder_path: str) -> dict[int, str] | None:
    """
    :exception ValueError: Если файл отсутствует.
    :return: {100: "src/tmp/100/1.txt", 300: "src/tmp/300/1.txt"}
    """
    dst_resized_paths_map: dict[int, str] = dict()
    try:
        img = cv2.imread(src_file_path)
        if img is None:
            raise ValueError(f"Cannot read image {src_file_path}")

        # image_sharp = image_filter(img)

        image_sharp = img

        # base_name и расширение
        base_name = Path(src_file_path).name
        name, ext = Path(base_name).stem, Path(base_name).suffix
        # --- Цикл по размерам ---
        for size in sizes:
            # вычисляем пропорциональный масштаб
            h, w = image_sharp.shape[:2]
            new_w = size
            new_h = int(h * (size / w))
            resized = cv2.resize(image_sharp, (new_w, new_h))

            file_path = f"{size}/{name}{ext}"
            dst_path = Path(dst_folder_path) / file_path

            # Создаём папку, если её нет
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            cv2.imwrite(str(dst_path), resized)

            dst_resized_paths_map |= {size: (str(dst_path))}
    except Exception as exc:
        logger.warning(exc, exc_info=True)
        return None

    return dst_resized_paths_map
