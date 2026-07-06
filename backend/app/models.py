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


class SetDiffusablePayload(BaseModel):
    appDossierId: int = Field(gt=0)
    diffusable: bool = True
    dryRun: bool = False


class SetValidationPayload(BaseModel):
    appDossierId: int = Field(gt=0)
    state: Literal[0, 1]
    dryRun: bool = False


class PersistHektorStatePayload(BaseModel):
    appDossierId: int = Field(gt=0)
    validationDiffusionState: str | None = None
    diffusable: bool | None = None
    portailsResume: str | None = None
    nbPortailsActifs: int | None = Field(default=None, ge=0)


class AcceptDiffusionPayload(BaseModel):
    appDossierId: int = Field(gt=0)
    dryRun: bool = False


class VerifyPriceDropPayload(BaseModel):
    appDossierId: int = Field(gt=0)
    requestedPrice: str | float | int | None = None
    requestText: str | None = None


class ScanAnnonceSheetPayload(BaseModel):
    imageBase64: str = Field(min_length=80)
    mimeType: str | None = None
    filename: str | None = None
    formVersion: str | None = None


class RedacteurAnnoncePayload(BaseModel):
    # Agent "Redacteur d'annonce" (propose-only). Le front envoie les donnees
    # factuelles deja affichees sur la fiche + les URLs photos ; le backend ne
    # re-derive rien et n'ecrit rien sur l'annonce.
    propertyData: dict = Field(default_factory=dict)
    photoUrls: list[str] = Field(default_factory=list, max_length=8)
    appDossierId: int | None = Field(default=None, gt=0)
    hektorAnnonceId: int | None = Field(default=None, gt=0)
    customIntro: str | None = Field(default=None, max_length=500)


class RedacteurDecisionPayload(BaseModel):
    # Trace de la decision humaine sur une proposition (analytics uniquement,
    # ne declenche aucune ecriture sur l'annonce).
    runId: int = Field(gt=0)
    status: Literal["accepted", "rejected"]
    finalTitle: str | None = Field(default=None, max_length=300)
    finalDescription: str | None = Field(default=None, max_length=8000)


class EstimationRedactionPayload(BaseModel):
    # Agent "Avis de valeur" (propose-only) : ameliore les notes brutes d'estimation
    # (issues d'une fiche manuscrite). texts = notes actuelles ; propertyData = faits.
    texts: dict = Field(default_factory=dict)
    propertyData: dict = Field(default_factory=dict)
    appDossierId: int | None = Field(default=None, gt=0)
    hektorAnnonceId: int | None = Field(default=None, gt=0)


class AppointmentRequestCreatePayload(BaseModel):
    clientName: str = Field(min_length=1, max_length=160)
    clientEmail: EmailStr | None = None
    clientPhone: str = Field(min_length=6, max_length=40)
    requestedStartAt: str = Field(min_length=10)
    requestedEndAt: str | None = None
    message: str | None = Field(default=None, max_length=4000)


class EstimationRequestCreatePayload(BaseModel):
    propertyAddress: str = Field(min_length=3, max_length=240)
    clientName: str = Field(min_length=1, max_length=160)
    clientEmail: EmailStr | None = None
    clientPhone: str = Field(min_length=6, max_length=40)
    requestedStartAt: str = Field(min_length=10)
    requestedEndAt: str | None = None
    message: str | None = Field(default=None, max_length=4000)
