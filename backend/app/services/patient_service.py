"""
################################################################################
#                                                                              #
#                         PATIENT SERVICE                                      #
#                                                                              #
#   Business logic for patient operations:                                     #
#   - lookup_patient   → find existing patient, build spoken response          #
#   - store_patient    → create new patient record                             #
#   - update_complaint → create new visit for returning patient                #
#                                                                              #
################################################################################
"""

from typing import Optional

from app.db.simple_repository import SimplePatientRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


async def lookup_patient(phone: str, name: Optional[str] = None) -> dict:
    """Find patient by phone then name. Returns result dict with spoken_response."""

    # Step 1: Look up by phone only
    matches = await SimplePatientRepository.async_lookup_patient_by_phone(phone=phone)

    # No matches found
    if not matches:
        logger.info(f"[PATIENT] No patient found for phone: {phone}")
        return {
            "found": False,
            "status": "not_found",
            "spoken_response": "Hmm, I'm not finding you in our system. No biggie, let me get you set up real quick. What's your first and last name?"
        }

    # Step 2: Multiple matches on same phone
    if len(matches) > 1:
        if not name:
            # No name yet — ask which family member
            names = set(m['full_name'] for m in matches)
            logger.info(f"[PATIENT] Multiple matches for phone, no name: {list(names)}")
            match_info = [{"name": m['full_name'], "patient_id": m['patient_id']} for m in matches]
            names_str = ', '.join(names)
            return {
                "found": False,
                "status": "multiple_matches_same_phone",
                "multiple_matches": match_info,
                "spoken_response": f"Looks like there are a few people under that number. {names_str}. Which one's you?"
            }

        # Name provided — filter by it
        name_lower = name.strip().lower()
        name_matches = [m for m in matches if name_lower in m['full_name'].lower()]
        if name_matches:
            matches = name_matches
        # If still multiple after name filter, take most recent
        if len(matches) > 1:
            matches = [max(matches, key=lambda m: m.get('patient_id', 0))]

    # Single match — success!
    patient = matches[0]
    logger.info(f"[PATIENT] Found: {patient['full_name']} (ID: {patient['patient_id']})")
    prev = patient.get('chief_complaint')
    if prev:
        spoken = f"Hey {patient['full_name']}, good to see you again! Last time you were here for {prev}, hope that's all cleared up. So tell me, what brings you in today?"
    else:
        spoken = f"Welcome back {patient['full_name']}! So tell me how are you, what brings you in today?"

    return {
        "found": True,
        "patient_id": patient['patient_id'],
        "full_name": patient['full_name'],
        "phone": patient['phone'],
        "previous_visit_reason": prev,
        "status": "found",
        "spoken_response": spoken
    }


async def store_patient(
    first_name: str,
    last_name: str,
    phone: Optional[str] = None,
    chief_complaint: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    past_medical_history: Optional[str] = None,
    smoking_status: Optional[str] = None,
    alcohol_use: Optional[str] = None
) -> dict:
    """Create new patient record. Returns result dict with spoken_response."""
    logger.info(f"[PATIENT] Creating: {first_name} {last_name}")

    patient_id, error = await SimplePatientRepository.async_store_patient(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        chief_complaint=chief_complaint,
        date_of_birth=date_of_birth,
        past_medical_history=past_medical_history,
        smoking_status=smoking_status,
        alcohol_use=alcohol_use
    )

    if error:
        logger.error(f"[PATIENT] Store failed: {error}")
        return {
            "success": False,
            "status": "error",
            "spoken_response": "Hmm, give me just a sec, system's being a little slow."
        }

    logger.info(f"[PATIENT] Created patient (ID: {patient_id})")
    return {
        "success": True,
        "patient_id": patient_id,
        "status": "saved",
        "spoken_response": "You're all set! The doctor will be with you shortly, go ahead and have a seat."
    }


async def update_complaint(name: str, chief_complaint: str, phone: Optional[str] = None) -> dict:
    """Create new visit row for returning patient. Returns result dict with spoken_response."""
    logger.info(f"[PATIENT] Return visit: {name}: {chief_complaint[:50]}...")

    if not phone:
        return {
            "success": False,
            "status": "not_found",
            "spoken_response": "I need your phone number to look you up. What's your phone number?"
        }

    matches = await SimplePatientRepository.async_lookup_patient_by_phone(
        phone=phone,
        name=name
    )

    if not matches:
        return {"success": False, "status": "not_found"}

    patient = matches[0]
    pid = patient.get('patient_id') or patient.get('id')
    new_id, error = await SimplePatientRepository.async_create_return_visit(
        patient_id=pid,
        chief_complaint=chief_complaint
    )

    if error:
        logger.error(f"[PATIENT] Return visit failed: {error}")
        return {
            "success": False,
            "status": "error",
            "spoken_response": "Hmm, give me just a sec, system's being a little slow."
        }

    logger.info(f"[PATIENT] Return visit created (ID: {new_id})")
    return {
        "success": True,
        "patient_id": new_id,
        "status": "saved",
        "spoken_response": "Got it. Go ahead and have a seat, the doctor will be with you shortly."
    }
