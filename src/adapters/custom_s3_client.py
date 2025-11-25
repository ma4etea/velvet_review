from aiobotocore.client import AioBaseClient  # type: ignore[reportMissingTypeStubs]
from aioboto3 import Session  # type: ignore[reportMissingTypeStubs]


class CustomAIOBoto3Session(Session): ...


class CustomAioBaseClient(AioBaseClient): ...
