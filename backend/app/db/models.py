"""
################################################################################
#                                                                              #
#                        SQLALCHEMY ORM MODELS                                 #
#                                                                              #
#   3 normalized tables:                                                       #
#     1. patient_registry    — Identity (name, phone, DOB)                     #
#     2. patient_assessment  — Health info per visit (complaint, smoking, etc) #
#     3. patient_visits      — Visit log linking registry ↔ assessment         #
#                                                                              #
################################################################################
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass

# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                      TABLE 1: PATIENT REGISTRY                           ║
# ║                                                                          ║
# ║   General identity — created once per patient.                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class PatientRegistry(Base):
    __tablename__ = "patient_registry"

    #So this part is purely database schema definition.
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    date_of_birth = Column(Date)
    age = Column(Integer)

    # Relationships
    visits = relationship("PatientVisit", back_populates="patient", lazy="selectin")
    assessments = relationship("PatientAssessment", back_populates="patient", lazy="selectin")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> dict:
        return {
            'patient_id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'age': self.age,
        }


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                  TABLE 2: PATIENT PRE-ASSESSMENT                         ║
# ║                                                                          ║
# ║   Health/pre-assessment info — one per visit.                            ║
# ║   chief_complaint, smoking, alcohol, medical history.                    ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class PatientAssessment(Base):
    __tablename__ = "patient_assessment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_registry.id"), nullable=False)
    chief_complaint = Column(String)
    past_medical_history = Column(String)
    smoking_status = Column(String)
    alcohol_use = Column(String)

    # Relationships
    patient = relationship("PatientRegistry", back_populates="assessments")

    def to_dict(self) -> dict:
        return {
            'assessment_id': self.id,
            'patient_id': self.patient_id,
            'chief_complaint': self.chief_complaint,
            'past_medical_history': self.past_medical_history,
            'smoking_status': self.smoking_status,
            'alcohol_use': self.alcohol_use,
        }


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║                      TABLE 3: PATIENT VISITS                             ║
# ║                                                                          ║
# ║   Visit log — links patient to their assessment per visit.               ║
# ║   Tracks visit number and date.                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

class PatientVisit(Base):
    __tablename__ = "patient_visits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_registry.id"), nullable=False)
    patient_name = Column(String)
    visit_date = Column(DateTime, default=datetime.utcnow)
    visit_number = Column(Integer, default=1)

    # Relationships
    patient = relationship("PatientRegistry", back_populates="visits")

    def to_dict(self) -> dict:
        return {
            'visit_id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient_name,
            'visit_date': self.visit_date.isoformat() if self.visit_date else None,
            'visit_number': self.visit_number,
        }
