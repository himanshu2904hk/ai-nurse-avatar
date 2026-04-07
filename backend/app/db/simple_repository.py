"""
################################################################################
#                                                                              #
#                       PATIENT DATABASE REPOSITORY                            #
#                                                                              #
#   Repository using SQLAlchemy ORM for 3 normalized tables:                   #
#     1. patient_registry    — Identity (name, phone, DOB)                     #
#     2. patient_assessment  — Pre-assessment info per visit                   #
#     3. patient_visits      — Visit log                                       #
#                                                                              #
################################################################################
"""

from typing import Optional, Dict, List, Any, Tuple
from datetime import date
import unicodedata
import re

from sqlalchemy import select, func

from app.db.postgres_base import get_session
from app.db.models import PatientRegistry, PatientAssessment, PatientVisit
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimplePatientRepository:
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                    PATIENT DATABASE OPERATIONS                           ║
    ║                                                                          ║
    ║   All methods use SQLAlchemy ORM with 3 normalized tables.               ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                     TEXT NORMALIZATION                                 │
    # │                                                                        │
    # │  Strip diacritics/accents from speech-to-text output.                  │
    # │  "Rāđi Čermā" → "Radi Cerma"                                           │
    # └────────────────────────────────────────────────────────────────────────┘

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Strip diacritics and normalize Unicode for fuzzy matching."""
        nfkd = unicodedata.normalize('NFKD', text)
        ascii_text = ''.join(c for c in nfkd if not unicodedata.combining(c))
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', ascii_text)
        return cleaned.strip()

    @staticmethod
    def _calculate_age(date_of_birth: Optional[str]) -> Optional[int]:
        """Calculate age from date of birth string (YYYY-MM-DD)."""
        if not date_of_birth:
            return None
        try:
            dob = date.fromisoformat(date_of_birth)
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        except (ValueError, TypeError):
            return None

    @classmethod
    def _build_patient_dict(cls, patient: PatientRegistry, assessment: Optional[PatientAssessment] = None) -> Dict[str, Any]:
        """Build combined dict from registry + latest assessment."""
        result = patient.to_dict()
        if assessment:
            result['chief_complaint'] = assessment.chief_complaint
            result['past_medical_history'] = assessment.past_medical_history
            result['smoking_status'] = assessment.smoking_status
            result['alcohol_use'] = assessment.alcohol_use
        else:
            result['chief_complaint'] = None
            result['past_medical_history'] = None
            result['smoking_status'] = None
            result['alcohol_use'] = None
        return result

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                   LOOKUP PATIENT BY PHONE                              │
    # │                                                                        │
    # │  Primary lookup: search by phone number first.                         │
    # │  If multiple matches (family members), use name to verify.             │
    # │  Joins latest assessment to get previous complaint.                    │
    # └────────────────────────────────────────────────────────────────────────┘

    @classmethod
    async def async_lookup_patient_by_phone(
        cls,
        phone: str,
        name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for patient by phone, join latest assessment for previous complaint."""
        try:
            clean_phone = ''.join(c for c in phone if c.isdigit())
            if not clean_phone:
                logger.warning("[DB] Empty phone after cleaning")
                return []

            logger.info(f"[DB] Phone-first lookup: phone={clean_phone}, name={name}")

            async with get_session() as session:
                query = (
                    select(PatientRegistry)
                    .where(PatientRegistry.phone.like(f'%{clean_phone}%'))
                    .limit(10)
                )

                result = await session.execute(query)
                patients = result.scalars().all()

                # For each patient, get their latest assessment
                results = []
                for p in patients:
                    latest_assessment = await cls._get_latest_assessment(session, p.id)
                    results.append(cls._build_patient_dict(p, latest_assessment))

                logger.info(f"[DB] Phone lookup: {len(results)} result(s) for phone={clean_phone}")

                # If name provided and multiple matches, filter by name
                if name and len(results) > 1:
                    normalized_name = cls._normalize_text(name)
                    name_words = normalized_name.lower().split()
                    name_filtered = []
                    for r in results:
                        full = f"{r['first_name']} {r['last_name']}".lower()
                        normalized_full = cls._normalize_text(full).lower()
                        if all(w in normalized_full for w in name_words if len(w) >= 2):
                            name_filtered.append(r)
                    if name_filtered:
                        logger.info(f"[DB] Name filter narrowed {len(results)} → {len(name_filtered)}")
                        results = name_filtered

                return results

        except Exception as e:
            logger.error(f"[DB] Phone lookup error: {e}")
            return []

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                        STORE PATIENT                                   │
    # │                                                                        │
    # │  New patient: INSERT into registry + assessment + visits.              │
    # └────────────────────────────────────────────────────────────────────────┘

    @classmethod
    async def async_store_patient(
        cls,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        chief_complaint: Optional[str] = None,
        date_of_birth: Optional[str] = None,
        past_medical_history: Optional[str] = None,
        smoking_status: Optional[str] = None,
        alcohol_use: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Create new patient across all 3 tables.

        Returns:
            Tuple of (patient_id, error_message)
        """
        try:
            age = cls._calculate_age(date_of_birth)

            async with get_session() as session:
                # 1. Create registry entry (identity)
                dob_value = None
                if date_of_birth:
                    try:
                        dob_value = date.fromisoformat(date_of_birth)
                    except (ValueError, TypeError):
                        dob_value = None

                registry = PatientRegistry(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    date_of_birth=dob_value,
                    age=age,
                )
                session.add(registry)
                await session.flush()  # Get the ID before inserting assessment

                # 2. Create pre-assessment entry (health info)
                assessment = PatientAssessment(
                    patient_id=registry.id,
                    chief_complaint=chief_complaint,
                    past_medical_history=past_medical_history,
                    smoking_status=smoking_status,
                    alcohol_use=alcohol_use,
                )
                session.add(assessment)

                await session.commit()
                await session.refresh(registry)

                logger.info(f"[DB] Stored new patient: {registry.full_name} (ID: {registry.id})")
                return registry.id, None

        except Exception as e:
            logger.error(f"[DB] Store error: {e}")
            return None, str(e)

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                    CREATE RETURN VISIT                                  │
    # │                                                                         │
    # │  Returning patient: new assessment + new visit row.                    │
    # │  Identity stays in registry (no duplication).                          │
    # └────────────────────────────────────────────────────────────────────────┘

    @classmethod
    async def async_create_return_visit(
        cls,
        patient_id: int,
        chief_complaint: str,
        past_medical_history: Optional[str] = None,
        smoking_status: Optional[str] = None,
        alcohol_use: Optional[str] = None
    ) -> Tuple[Optional[int], Optional[str]]:
        """
        Create new visit for returning patient (new assessment + visit row).

        Returns:
            Tuple of (patient_id, error_message)
        """
        try:
            async with get_session() as session:
                # Verify patient exists
                existing = await session.get(PatientRegistry, patient_id)
                if not existing:
                    return None, f"Patient ID {patient_id} not found"

                # Get current visit count
                visit_count_query = (
                    select(func.count(PatientVisit.id))
                    .where(PatientVisit.patient_id == patient_id)
                )
                result = await session.execute(visit_count_query)
                current_visits = result.scalar() or 0

                # 1. Create new assessment
                assessment = PatientAssessment(
                    patient_id=patient_id,
                    chief_complaint=chief_complaint,
                    past_medical_history=past_medical_history,
                    smoking_status=smoking_status,
                    alcohol_use=alcohol_use,
                )
                session.add(assessment)

                # 2. Create new visit row
                visit = PatientVisit(
                    patient_id=patient_id,
                    patient_name=existing.full_name,
                    visit_number=current_visits + 1,
                )
                session.add(visit)

                # Update age if DOB exists
                if existing.date_of_birth:
                    dob_str = existing.date_of_birth.isoformat()
                    existing.age = cls._calculate_age(dob_str)

                await session.commit()

                logger.info(f"[DB] Return visit #{current_visits + 1} for {existing.full_name}")
                return existing.id, None

        except Exception as e:
            logger.error(f"[DB] Return visit error: {e}")
            return None, str(e)

    # ┌────────────────────────────────────────────────────────────────────────┐
    # │                       HELPER: GET LATEST ASSESSMENT                    │
    # └────────────────────────────────────────────────────────────────────────┘

    @staticmethod
    async def _get_latest_assessment(session, patient_id: int) -> Optional[PatientAssessment]:
        """Get the most recent assessment for a patient."""
        query = (
            select(PatientAssessment)
            .where(PatientAssessment.patient_id == patient_id)
            .order_by(PatientAssessment.id.desc())
            .limit(1)
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
