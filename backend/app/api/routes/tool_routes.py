"""
################################################################################
#                                                                              #
#                         TOOL API ROUTES                                      #
#                                                                              #
#   FastAPI route handlers for all Tavus tool endpoints.                       #
#   Routes call services — no business logic here.                             #
#                                                                              #
#   Routes:                                                                    #
#   - POST /tool/lookup_patient      → find existing patient                  #
#   - POST /tool/store_patient       → create new patient                     #
#   - POST /tool/update_complaint    → new visit for returning patient         #
#   - POST /tool/create_conversation → create Tavus avatar session             #
#   - POST /tool/end_conversation    → end Tavus avatar session                #
#   - GET  /tool/health              → health check                            #
#                                                                              #
################################################################################
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services import patient_service, tavus_service

logger = get_logger(__name__)

router = APIRouter(prefix="/tool", tags=["Tavus Tools"])


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         REQUEST SCHEMAS                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class LookupRequest(BaseModel):
    phone: str = Field(..., description="Patient phone number (primary lookup field)")
    name: Optional[str] = Field(None, description="Patient name for verification/disambiguation")


class StoreRequest(BaseModel):
    first_name: str = Field(..., description="Patient's first name")
    last_name: str = Field(..., description="Patient's last name")
    phone: Optional[str] = Field(None, description="Phone number")
    chief_complaint: Optional[str] = Field(None, description="Reason for visit")
    date_of_birth: Optional[str] = Field(None, description="Date of birth (YYYY-MM-DD)")
    past_medical_history: Optional[str] = Field(None, description="Ongoing health conditions")
    smoking_status: Optional[str] = Field(None, description="Smoking/tobacco use status")
    alcohol_use: Optional[str] = Field(None, description="Alcohol consumption frequency")


class UpdateComplaintRequest(BaseModel):
    name: str = Field(..., description="Patient's full name")
    phone: Optional[str] = Field(None, description="Phone number")
    chief_complaint: str = Field(..., description="Reason for visit")


class CreateConversationRequest(BaseModel):
    custom_greeting: Optional[str] = None


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                         AUTHENTICATION                                   ║
# ║   NOTE: Disabled for Tavus (Tavus doesn't send custom headers)           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        return True
    if x_api_key != settings.AVATAR_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return True


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                            ROUTES                                         ║
# ╚══════════════════════════════════════════════════════════════════════════╝

@router.post("/lookup_patient")
async def lookup_patient(request: LookupRequest, auth: bool = Depends(verify_api_key)):
    try:
        return await patient_service.lookup_patient(
            phone=request.phone,
            name=request.name
        )
    except Exception as e:
        logger.error(f"[LOOKUP] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store_patient")
async def store_patient(request: StoreRequest, auth: bool = Depends(verify_api_key)):
    try:
        return await patient_service.store_patient(
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            chief_complaint=request.chief_complaint,
            date_of_birth=request.date_of_birth,
            past_medical_history=request.past_medical_history,
            smoking_status=request.smoking_status,
            alcohol_use=request.alcohol_use
        )
    except Exception as e:
        logger.error(f"[STORE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update_complaint")
async def update_complaint(request: UpdateComplaintRequest, auth: bool = Depends(verify_api_key)):
    try:
        return await patient_service.update_complaint(
            name=request.name,
            chief_complaint=request.chief_complaint,
            phone=request.phone
        )
    except Exception as e:
        logger.error(f"[UPDATE] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_conversation", include_in_schema=False)
async def create_conversation(request: CreateConversationRequest = CreateConversationRequest()):
    return await tavus_service.create_conversation(custom_greeting=request.custom_greeting)


@router.post("/end_conversation/{conversation_id}", include_in_schema=False)
async def end_conversation(conversation_id: str):
    return await tavus_service.end_conversation(conversation_id=conversation_id)


@router.get("/health")
async def tools_health():
    return {
        "status": "ok",
        "tools": ["lookup_patient", "store_patient", "update_complaint"]
    }
