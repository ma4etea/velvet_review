from starlette.responses import Response

from src.schemas.auths import TokensDTO


def set_tokens_in_cookie(response: Response, tokens: TokensDTO) -> Response:
    for key, value in tokens.model_dump(exclude_none=True).items():
        response.set_cookie(key=key, value=str(value))
    return response
