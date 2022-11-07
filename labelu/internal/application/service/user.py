from datetime import timedelta

from fastapi import status
from sqlalchemy.orm import Session

from labelu.internal.common.config import settings
from labelu.internal.domain.models.user import User
from labelu.internal.adapter.persistence import crud_user
from labelu.internal.common.security import AccessToken
from labelu.internal.common.security import verify_password
from labelu.internal.common.security import get_password_hash
from labelu.internal.common.security import create_access_token
from labelu.internal.application.command.user import LoginCommand
from labelu.internal.application.command.user import SignupCommand
from labelu.internal.application.response.user import SignupResponse
from labelu.internal.application.response.user import LoginResponse
from labelu.internal.application.response.error_code import ErrorCode
from labelu.internal.application.response.error_code import UnicornException


async def signup(db: Session, cmd: SignupCommand) -> SignupResponse:
    # check user alredy exists
    user = crud_user.get_user_by_username(db, username=cmd.username)
    if user:
        raise UnicornException(
            code=ErrorCode.CODE_40001_USERNAME_ALREADY_EXISTS,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # new a user
    user = crud_user.create_user(
        db,
        User(
            username=cmd.username,
            hashed_password=get_password_hash(cmd.password),
        ),
    )

    # response
    return SignupResponse(id=user.id, username=user.username)


async def login(db: Session, cmd: LoginCommand) -> LoginResponse:

    # check user exsit and verify password
    user = crud_user.get_user_by_username(db, cmd.username)
    if not user or not verify_password(cmd.password, user.hashed_password):
        raise UnicornException(
            code=ErrorCode.CODE_40000_USERNAME_OR_PASSWORD_INCORRECT,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # create access token
    access_token_expires = timedelta(minutes=settings.TOKEN_ACCESS_EXPIRE_MINUTES)
    access_token = create_access_token(
        token=AccessToken(id=user.id, username=user.username),
        expires_delta=access_token_expires,
    )

    # response
    return LoginResponse(token=f"{settings.TOKEN_TYPE} {access_token}")