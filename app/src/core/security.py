import abc
from typing import Any, Union, Optional
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from settings import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


class Tokenizer(abc.ABC):
    @abc.abstractmethod  # pragma: nocover
    def create_access_token(self, subject: Union[str, Any]) -> str:
        pass

    @abc.abstractmethod  # pragma: nocover
    def decode_access_token(self, token: str) -> str:
        pass


class JWTTokenizer(Tokenizer):
    _ALGORITHM = "HS256"
    _EXP_KEY = "exp"
    _SUB_KEY = "sub"

    def create_access_token(
        self, subject: Union[str, Any], expires_delta: timedelta = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        to_encode = {self._EXP_KEY: expire, self._SUB_KEY: str(subject)}
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=self._ALGORITHM
        )
        return encoded_jwt

    def decode_access_token(self, token: str) -> Optional[str]:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self._ALGORITHM])
        username = payload.get(self._SUB_KEY)
        return username
