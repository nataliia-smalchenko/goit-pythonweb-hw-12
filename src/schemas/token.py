from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# class PasswordResetToken(BaseModel):
#     token: str


# class NewPassword(BaseModel):
#     password: str
#     confirm_password: str
