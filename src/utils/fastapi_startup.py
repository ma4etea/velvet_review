from pathlib import Path

from src.logging_config import logger
from src.utils.images import resized_images
from src.utils.s3_manager import get_s3_manager_fabric


async def load_placeholders_in_s3():
    PLACEHOLDER_IMAGES = {
        "error.jpg": "resources/placeholders/error_image.jpg",
    }
    for key_file_name, path in PLACEHOLDER_IMAGES.items():
        async with get_s3_manager_fabric() as s3:
            sizes = [100, 300, 1280]

            exists = True
            for size in sizes:
                exist_key = await s3.adapter.check_key(
                    bucket="velvet", key=f"placeholders/{size}/{key_file_name}"
                )
                if not exist_key:
                    exists = False
                    break

            if not exists:
                logger.info("placeholders не найдены: будут созданы новые в s3")
                dst_folder_path_without_extension = Path(path).stem
                files_paths = resized_images(
                    *sizes, src_file_path=path, dst_folder_path=dst_folder_path_without_extension
                )

                if files_paths is None:
                    raise FileNotFoundError(f"File not found: {path}")

                for size, file_path in files_paths.items():
                    await s3.adapter.upload_file(
                        file_path=file_path,
                        bucket="velvet",
                        key=f"placeholders/{size}/{key_file_name}",
                    )
                await s3.adapter.commit()
