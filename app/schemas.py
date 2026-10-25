
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class LeadCreate(BaseModel):
    student_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=10, max_length=15)
    interested_course: str = Field(min_length=2, max_length=100)
    enquiry_message: str = Field(min_length=5, max_length=1000)


class LeadStatusUpdate(BaseModel):
    status: Literal[
        "new",
        "contacted",
        "interested",
        "admitted",
        "not_interested",
    ]


class FollowUpUpdate(BaseModel):
    follow_up_at: datetime
