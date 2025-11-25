import uuid
from pathlib import Path

from src.config import settings
from src.exceptions.base import (
    ObjectUseAsForeignKeyException,
    UnitHaveTransactionsException,
    UnitImagesLimitException,
    UnitImageIsMainException,
)
from src.exceptions.forbidden import (
    UnitModificationInStoreForbiddenException,
    UnitReadInStoreForbiddenException,
)
from src.exceptions.not_found import (
    StoreNotFoundException,
    UnitNotFoundException,
    ObjectNotFoundException,
    UnitImageNotFoundException,
    ForeignKeyNotFoundException,
)
from src.logging_config import logger
from src.models.units import UnitImageStatusEnum
from src.models.users import RoleUserInStoreEnum, RoleUserInCompanyEnum
from src.schemas.types import SortOrder, SortUnitBy, UnitField
from src.schemas.units import (
    AddUnitDTO,
    EditUnitDTO,
    UnitWithFieldsDTO,
    UnitDTO,
    UnitWithMainImageDTO,
)
from src.schemas.unit_images import AddUnitImageDTO, EditUnitImageDTO, UnitImageDTO
from src.services.base import BaseService
from src.services.helpers.access_roles import (
    roles_can_write_unit_in_store,
    roles_can_read_unit_in_store,
    roles_is_administrations,
)
from src.services.images import UnitImagesService
from src.services.stores import StoresService
from src.tasks.manager import task_manager


# todo добавить docs что None нужен так как роли может не быть по ключу
class UnitsService(BaseService):
    def check_user_role_write_unit_in_store(
        self, user_role_in_store: RoleUserInStoreEnum | None
    ) -> None:
        """
        Проверяет доступ пользователя к добавлению товара, изменению, удалению в конкретном store
        :raise UnitModificationInStoreForbiddenException: Если доступ к созданию, изменению, удалению товара запрещен.
        """
        if user_role_in_store not in roles_can_write_unit_in_store:
            raise UnitModificationInStoreForbiddenException

    def check_user_role_read_unit_in_store(
        self, user_role_in_store: RoleUserInStoreEnum | None
    ) -> None:
        """
        Проверяет доступ пользователя к просмотру товара в конкретном store
        :raise UnitReadInStoreForbiddenException: Если доступ к просмотру товара в этом магазине запрещен.
        """
        if user_role_in_store not in roles_can_read_unit_in_store:
            raise UnitReadInStoreForbiddenException

    async def add_unit(
        self,
        dto: AddUnitDTO,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> UnitDTO:
        """
        :param dto: Добавляемый товар.
        :param user_roles_in_stores: Это Map: key = id магазина, value = роль.
        :param user_role_in_company: Роль пользователя в компании.

        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise UnitModificationForbidden: Если доступ к созданию, изменению, удалению товара запрещен.
        """
        if user_role_in_company not in roles_is_administrations:
            self.check_user_role_write_unit_in_store(user_roles_in_stores.get(dto.store_id))
        try:
            unit = await self.db.units.add(dto)
        except ForeignKeyNotFoundException as exc:
            raise StoreNotFoundException from exc
        await self.db.commit()
        return unit

    async def get_units(
        self,
        offset: int,
        limit: int,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
        sort_order: SortOrder,
        sort_by: SortUnitBy,
        search_term: str | None = None,
        store_id: int | None = None,
    ) -> list[UnitWithMainImageDTO]:
        """
        :param offset: Смещение, получить от какого элемента в запросе.
        :param limit: Сколько получить элементов из запроса.
        :param user_roles_in_stores: Это Map: key = id магазина, value = роль.
        :param user_role_in_company: Роль пользователя в компании.
        :param sort_order: Порядок по возрастанию или убываю
        :param sort_by: Сортировка по определенному полю
        :param search_term: Поисковая строка ищет по title и description одновременно
        :param store_id: ID магазина. Если None тогда получает товары из всех магазинам
        :return: Список товаров с главной картинкой
        :raise StoreNotFoundException: Если магазин с указанным ID не найден.
        :raise UnitNotFoundException: Если ни одного товара не найдено.
        :raise UnitReadInAllStoresForbiddenException: Если доступ к просмотру товаров во всех магазинах запрещен.
        :raise UnitReadInStoreForbiddenException: Если доступ к просмотру товара в этом магазине запрещен.

        """
        if user_role_in_company in roles_is_administrations:
            # Админ — можно всё, только проверяем, если store_id указан, что магазин существует
            if store_id:
                await StoresService(db=self.db, cache=self.cache).check_get_store_by_id(
                    store_id=store_id
                )
        else:
            # Не админ — store_id обязателен
            if not store_id:
                raise UnitReadInStoreForbiddenException
            else:
                await StoresService(db=self.db, cache=self.cache).check_get_store_by_id(
                    store_id=store_id
                )
                self.check_user_role_read_unit_in_store(user_roles_in_stores.get(store_id))

        units_with_main_image = await self.db.units.get_units(
            offset=offset,
            limit=limit,
            search_term=search_term,
            store_id=store_id,
            sort_unit_by=sort_by,
            sort_order=sort_order,
        )

        if not units_with_main_image:
            raise UnitNotFoundException
        return units_with_main_image

    async def get_unit(
        self,
        unit_id: int,
        user_role_in_company: RoleUserInCompanyEnum,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        fields: tuple[UnitField, ...] | None,
    ) -> UnitWithFieldsDTO:
        """

        :param user_role_in_company: Роль пользователя в компании.
        :param unit_id:
        :param user_roles_in_stores: Для проверки прав доступа.
        :param fields: Дополнительные поля.
        :return: Товар с опциональными дополнительными полями
        :raise UnitNotFoundException: Если товар не найден.
        :raise UnitReadInStoreForbiddenException: Если доступ к просмотру товара в этом магазине запрещен.
        """

        try:
            unit_with_fields = await self.db.units.get_unit_with_fields(
                unit_id=unit_id, fields=fields
            )
        except ObjectNotFoundException as exc:
            raise UnitNotFoundException from exc

        if user_role_in_company not in roles_is_administrations:
            self.check_user_role_read_unit_in_store(
                user_roles_in_stores.get(unit_with_fields.store_id)
            )

        return unit_with_fields

    async def edit_unit(
        self,
        dto: EditUnitDTO,
        unit_id: int,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> UnitDTO:
        """
        :param dto: Поля для изменения товара.
        :param user_role_in_company: Роль пользователя в компании.
        :param unit_id: Id товара.
        :param user_roles_in_stores: Это Map: key = id магазина, value = роль.
        :return: Товар dto
        :raise UnitNotFoundException: Если товар не найден по id.
        :raise UnitImageNotFoundException: Если картинка товара не найдена.
        :raise UnitModificationForbidden: Если доступ к созданию, изменению, удалению товара запрещен.
        """
        unit = await self.check_get_unit_by_id(unit_id=unit_id)
        if user_role_in_company not in roles_is_administrations:
            self.check_user_role_write_unit_in_store(user_roles_in_stores.get(unit.store_id))

        if dto.main_image_id:
            await UnitImagesService(db=self.db).check_get_unit_image(
                unit_id=unit_id, image_id=dto.main_image_id
            )

        unit = await self.db.units.edit_unit(unit_id=unit_id, dto=dto)
        await self.db.commit()
        return unit

    async def delete_unit(
        self,
        unit_id: int,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> None:
        """
        Удаляет товар с картинками из s3 и базы данных, если у товара нет транзакций.
        :raise UnitNotFoundException: Если товар не найден по id.
        :raise UnitModificationInStoreForbiddenException: Если доступ к удалению товара запрещен.
        :raise UnitHaveTransactionsException: Если у товара есть транзакции
        """
        unit = await self.check_get_unit_by_id(unit_id=unit_id)
        if user_role_in_company not in roles_is_administrations:
            self.check_user_role_write_unit_in_store(user_roles_in_stores.get(unit.store_id))

        unit_images: list[UnitImageDTO] = await self.db.unit_images.get_all(unit_id=unit_id)

        try:
            await self.db.units.delete(id=unit_id)
        except ObjectUseAsForeignKeyException as exc:
            raise UnitHaveTransactionsException from exc

        try:
            for image in unit_images:
                await self.s3.unit_images.delete_unit_image(dto=image)
        except:
            raise

        await self.s3.commit()
        await self.db.commit()

    # todo возможно стоит за кешировать метод на 1 минутку хотя бы.
    async def check_get_unit_by_id(self, unit_id: int) -> UnitDTO:
        """
        :raise UnitNotFoundException:
        """
        try:
            unit: UnitDTO = await self.db.units.get_one(id=unit_id)
        except ObjectNotFoundException as exc:
            raise UnitNotFoundException from exc

        return unit

    async def create_task_upload_images(
        self,
        path_to_folder_with_images: str,
        total_images: int,
        unit_id: int,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ):
        """
        :param user_role_in_company: Роль пользователя в компании.
        :param total_images: Количество image, которое ожидает в папке tmp
        :param path_to_folder_with_images: путь до папки с файлами
        :param unit_id:
        :param user_roles_in_stores: Роль для проверки прав

        :raise UnitNotFoundException: Если товар не найден
        :raise UnitModificationForbidden: если запрещено изменять unit
        :raise UnitImagesLimitException: если лимит изображений достигнут
        :return:
        """
        unit = await self.check_get_unit_by_id(unit_id=unit_id)
        if user_role_in_company not in roles_is_administrations:
            self.check_user_role_write_unit_in_store(user_roles_in_stores.get(unit.store_id))

        quantity_unit_images = await self.db.unit_images.get_total(unit_id=unit_id)
        if (
            quantity_unit_images >= settings.UNIT_IMAGES_LIMIT
            or quantity_unit_images + total_images > settings.UNIT_IMAGES_LIMIT
        ):
            raise UnitImagesLimitException

        start = quantity_unit_images + 1
        stop = quantity_unit_images + total_images + 1
        pending_unit_images = [
            AddUnitImageDTO(
                unit_id=unit_id,
                status=UnitImageStatusEnum.pending,
            )
            for _ in range(start, stop)
        ]

        unit_images: list[UnitImageDTO] = await self.db.unit_images.add_bulk(*pending_unit_images)
        unit_images_ids = [image.id for image in unit_images]

        if unit.main_image_id is None:
            edit_unit = EditUnitDTO(main_image_id=unit_images_ids[0])

            await self.db.units.edit(dto=edit_unit, exclude_unset=True, id=unit_id)

        task_manager.saving_resized_unit_images_in_s3(
            unit_images_ids=unit_images_ids, src_path=path_to_folder_with_images, unit_id=unit_id
        )

        await self.db.commit()

    async def upload_unit_images_in_s3(
        self,
        unit_images_ids: list[int],
        resized_files_path: list[dict[int, str] | None],
        unit_id: int,
    ):
        """
        Источником правды о состоянии image является база данных
        :param unit_images_ids: Список id изображений в базе данных
        :param resized_files_path: Список map где key = размер изображения, value = путь до файла
        :param unit_id: к какому товару привязаны изображения
        :return:
        """

        unit_image_with_status_error = EditUnitImageDTO(
            status=UnitImageStatusEnum.error,
        )

        try:
            for image_id, file_paths in zip(unit_images_ids, resized_files_path):
                if file_paths is None:
                    await self.db.unit_images.edit(
                        dto=unit_image_with_status_error, exclude_unset=True, id=image_id
                    )
                    await self.db.commit()

                else:
                    try:
                        keys: dict[int, str] = dict()
                        uuid_ = uuid.uuid4()
                        for size, path in file_paths.items():
                            s3_key = f"units/{unit_id}/images/{uuid_}/{size}{Path(path).suffix}"
                            unit_image_key = await self.s3.unit_images.add_unit_image(
                                src_file_path=path, key=s3_key
                            )
                            keys |= {size: unit_image_key}

                        edit_unit_image = EditUnitImageDTO(
                            status=UnitImageStatusEnum.done,
                            key_1280=keys[1280],
                            key_300=keys[300],
                            key_100=keys[100],
                        )

                        await self.db.unit_images.edit(
                            dto=edit_unit_image, exclude_unset=True, id=image_id
                        )
                        await self.db.commit()
                        await self.s3.commit()

                    except Exception as exc:
                        logger.warning(exc, exc_info=True)
                        await self.db.unit_images.edit(
                            dto=unit_image_with_status_error, exclude_unset=True, id=image_id
                        )
                        await self.db.commit()
                        await self.s3.rollback()

        except Exception as exc:
            logger.warning(exc, exc_info=True)

    async def delete_unit_image(
        self,
        unit_id: int,
        image_id: int,
        user_roles_in_stores: dict[int, RoleUserInStoreEnum],
        user_role_in_company: RoleUserInCompanyEnum,
    ) -> None:
        """
        :raise UnitNotFoundException: если товар не найден
        :raise UnitModificationInStoreForbiddenException: если запрещено изменять unit
        :raise UnitImageNotFoundException: если image не найден
        :raise UnitImageIsMainException: если image является главной для товара
        """

        unit = await self.check_get_unit_by_id(unit_id=unit_id)
        if user_role_in_company not in roles_is_administrations:
            self.check_user_role_write_unit_in_store(user_roles_in_stores.get(unit.store_id))

        try:
            unit_image = await self.db.unit_images.get_one(id=image_id, unit_id=unit_id)
        except ObjectNotFoundException as exc:
            raise UnitImageNotFoundException from exc

        try:
            await self.db.unit_images.delete(id=image_id, unit_id=unit_id)
        except ObjectUseAsForeignKeyException as exc:
            raise UnitImageIsMainException from exc

        await self.s3.unit_images.delete_unit_image(dto=unit_image)

        await self.s3.commit()
        await self.db.commit()
