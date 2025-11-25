from fastapi import APIRouter
from starlette.responses import Response

from src.config import settings
from src.exceptions.base import (
    UserAlreadyExistsException,
    UnconfirmedRegistrationAlreadyExistsException,
    InvalidConfirmCodeException,
    ExpiredConfirmCodeException,
    InvalidPasswordException,
    ResendLimitAlreadyExistsException,
    CooldownForgotAlreadyExistsException,
    DeviceMismatchException,
)
from src.exceptions.not_found import (
    UnconfirmedRegistrationNotFoundException,
    UserNotFoundException,
    UserSessionNotFoundException,
    ForgotPasswordNotFoundException,
)
from src.routers.dependencies import DepDB, DepCache, DepRefresh, DepDeviceID
from src.routers.http_exceptions.base import (
    InvalidConfirmCodeHTTPException,
    ExpiredConfirmCodeHTTPException,
    InvalidCredentialsHTTPException,
    DeviceMismatchHTTPException,
)
from src.routers.http_exceptions.conflict import (
    UserAlreadyExistsHTTPException,
    UnconfirmedRegistrationAlreadyExistsHTTPException,
    ResendLimitAlreadyExistsHTTPException,
    CooldownForgotAlreadyExistsHTTPException,
)
from src.routers.http_exceptions.not_found import (
    UnconfirmedRegistrationNotFoundHTTPException,
    UserSessionNotFoundHTTPException,
    UserNotFoundHTTPException,
    ForgotPasswordNotFoundHTTPException,
)
from src.routers.cookies import set_tokens_in_cookie
from src.schemas.base import StandardResponse, NullDataResponse
from src.schemas.auths import (
    CredsUserDTO,
    ResendConfirmCodeDTO,
    ConfirmRegisterDTO,
    ResetPasswordDTO,
    ResponseTokens,
)
from src.services.auths import AuthsService
from src.utils.files import get_md
from src.utils.swagger_exceptions import exceptions_to_openapi

auth_router = APIRouter(prefix="/auth", tags=["Авторизация и аутентификация пользователя"])


@auth_router.post(
    "/register",
    description=get_md(
        path_to_md_file="docs/register_user_description.md",
        expire_register=str(round(settings.UNCONFIRMED_REGISTRATION_EXPIRE_MINUTES / 60)),
        expire_code=str(settings.CONFIRM_CODE_EXPIRE_MINUTES),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        UserAlreadyExistsHTTPException, UnconfirmedRegistrationAlreadyExistsHTTPException
    ),
)
async def register_user(db: DepDB, cache: DepCache, creds: CredsUserDTO) -> NullDataResponse:
    try:
        await AuthsService(db=db, cache=cache).register_user(creds)
    except (
        UserAlreadyExistsException
    ):  # todo Оба 409, значит нужно доп. поле для фронта что бы различать исключения
        raise UserAlreadyExistsHTTPException
    except UnconfirmedRegistrationAlreadyExistsException:
        raise UnconfirmedRegistrationAlreadyExistsHTTPException
    return NullDataResponse(
        message=f"Успешная заявка на регистрацию. Выслан код подтверждения на email:{creds.email}"
    )


@auth_router.post(
    "/confirm",
    description=get_md("docs/confirm_email_description.md"),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        UnconfirmedRegistrationNotFoundHTTPException,
        InvalidConfirmCodeHTTPException,
        ExpiredConfirmCodeHTTPException,
    ),
)
async def confirm_email(
    db: DepDB, cache: DepCache, confirm_register: ConfirmRegisterDTO
) -> NullDataResponse:
    try:
        message = await AuthsService(db=db, cache=cache).confirm_email(confirm_register)
    except UnconfirmedRegistrationNotFoundException:
        raise UnconfirmedRegistrationNotFoundHTTPException
    except InvalidConfirmCodeException:
        raise InvalidConfirmCodeHTTPException
    except ExpiredConfirmCodeException:
        raise ExpiredConfirmCodeHTTPException

    return NullDataResponse(message=message)


@auth_router.post(
    "/resend",
    description=get_md(
        path_to_md_file="docs/resend_confirm_code_description.md",
        expire_code=str(settings.CONFIRM_CODE_EXPIRE_MINUTES),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        ResendLimitAlreadyExistsHTTPException, UnconfirmedRegistrationNotFoundHTTPException
    ),
)
async def resend_confirm_code(
    db: DepDB, cache: DepCache, data: ResendConfirmCodeDTO
) -> NullDataResponse:
    try:
        await AuthsService(db=db, cache=cache).resend_confirm_code(data)
    except UnconfirmedRegistrationNotFoundException:
        raise UnconfirmedRegistrationNotFoundHTTPException
    except ResendLimitAlreadyExistsException:
        raise ResendLimitAlreadyExistsHTTPException
    return NullDataResponse(message=f"Код подтверждения отправлен на email:{data.email}")


@auth_router.post(
    "/forgot",
    description=get_md(
        path_to_md_file="docs/forgot_password_description.md",
        expire_code=str(settings.FORGOT_PASSWORD_EXPIRE_MINUTES),
    ),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        UserNotFoundHTTPException, CooldownForgotAlreadyExistsHTTPException
    ),
)
async def forgot_password(
    db: DepDB, cache: DepCache, data: ResendConfirmCodeDTO
) -> NullDataResponse:
    try:
        await AuthsService(db=db, cache=cache).forgot_password(data)
    except UserNotFoundException:
        raise UserNotFoundHTTPException  # todo вопрос стоит ли маскировать ответ, для защиты от брудфорс
    except CooldownForgotAlreadyExistsException:
        raise CooldownForgotAlreadyExistsHTTPException
    return NullDataResponse(message=f"Код подтверждения отправлен на email:{data.email}")


@auth_router.post(
    "/reset",
    description=get_md("docs/reset_password_description.md"),
    response_model=NullDataResponse,
    responses=exceptions_to_openapi(
        ForgotPasswordNotFoundHTTPException,
        UserNotFoundHTTPException,
        InvalidConfirmCodeHTTPException,
    ),
)
async def reset_password(db: DepDB, cache: DepCache, data: ResetPasswordDTO) -> NullDataResponse:
    try:
        await AuthsService(db=db, cache=cache).reset_password(data)
    except ForgotPasswordNotFoundException:
        raise ForgotPasswordNotFoundHTTPException
    except InvalidConfirmCodeException:
        raise InvalidConfirmCodeHTTPException
    except UserNotFoundException:
        raise UserNotFoundHTTPException
    return NullDataResponse(message=f"Пароль сброшен для email:{data.email}")


@auth_router.post(
    "/login",
    description=get_md("docs/login_user_description.md"),
    response_model=StandardResponse[ResponseTokens],
    responses=exceptions_to_openapi(
        InvalidCredentialsHTTPException,
    ),
)
async def login_user(
    db: DepDB, device_id: DepDeviceID, creds: CredsUserDTO, response: Response
) -> StandardResponse[ResponseTokens]:
    try:
        tokens = await AuthsService(db).login_user(creds=creds, device_id=device_id)
    except (InvalidPasswordException, UserNotFoundException):
        raise InvalidCredentialsHTTPException
    set_tokens_in_cookie(response, tokens)

    return StandardResponse(data=ResponseTokens(tokens=tokens))


@auth_router.post(
    "/refresh",
    description=get_md("docs/refresh_user_tokens_description.md"),
    response_model=StandardResponse[ResponseTokens],
    responses=exceptions_to_openapi(UserSessionNotFoundHTTPException, DeviceMismatchHTTPException),
)
async def refresh_user_tokens(
    db: DepDB,
    cache: DepCache,
    payload_refresh: DepRefresh,
    device_id: DepDeviceID,
    response: Response,
) -> StandardResponse[ResponseTokens]:
    try:
        tokens = await AuthsService(db=db, cache=cache).refresh_user_tokens(
            session_id=payload_refresh.session_id, device_id=device_id
        )
    except UserSessionNotFoundException:
        raise UserSessionNotFoundHTTPException
    except DeviceMismatchException:
        raise DeviceMismatchHTTPException
    set_tokens_in_cookie(response, tokens)

    return StandardResponse(data=ResponseTokens(tokens=tokens))
