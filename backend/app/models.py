from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


UserRole = Literal["admin", "manager", "commercial", "lecture"]


class CreateUserPayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole
    firstName: str = ""
    lastName: str = ""
    displayName: str = ""
    isActive: bool = True


class UpdateUserPayload(BaseModel):
    id: str
    email: EmailStr
    role: UserRole
    firstName: str = ""
    lastName: str = ""
    displayName: str = ""
    isActive: bool = True


class SendResetPayload(BaseModel):
    email: EmailStr


class DiffusionDecisionEmailPayload(BaseModel):
    to: EmailStr
    subject: str = Field(min_length=1)
    bodyText: str = Field(min_length=1)
    bodyHtml: str | None = None
    fromEmail: EmailStr | None = None
    fromName: str | None = None
    replyTo: EmailStr | None = None


class ApplyDiffusionPayload(BaseModel):
    appDossierId: int = Field(gt=0)
    dryRun: bool = False
    ensureDiffusable: bool = False


class AcceptDiffusionPayload(BaseModel):
    appDossierId: int = Field(gt=0)
    dryRun: bool = False
