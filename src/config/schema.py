
from pydantic import BaseModel, Field
from typing import List, Optional

class Config(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    method: int = 3
    school: int = 0
    enabled_prayers: List[str] = Field(default_factory=lambda: ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"])
    custom_audio_path: Optional[str] = None
    google_calendar_id: Optional[str] = None
    run_mode: str = "background"
    log_level: str = "INFO"

