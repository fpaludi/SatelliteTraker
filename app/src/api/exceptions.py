from fastapi import HTTPException
from fastapi import status


CredentialException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

UserPassException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect username or password",
    headers={"WWW-Authenticate": "Bearer"},
)

UserExistsException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="User already exists",
    headers={"WWW-Authenticate": "Bearer"},
)

DataNotFoundException = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Data not found",
)
