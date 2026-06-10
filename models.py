from dataclasses import dataclass
from typing import Optional

@dataclass
class Job:
    title: str
    company: str
    location: str
    link: str
    source_platform: str
    salary: Optional[str] = None

    def __post_init__(self):
        # Edge Case handling: Ensure fields are cast to strings (or None for salary)
        # to prevent downstream errors if scrapers return unexpected types.
        self.title = str(self.title) if self.title is not None else "Unknown Title"
        self.company = str(self.company) if self.company is not None else "Unknown Company"
        self.location = str(self.location) if self.location is not None else "Unknown Location"
        self.link = str(self.link) if self.link is not None else ""
        self.source_platform = str(self.source_platform) if self.source_platform is not None else "Unknown Platform"
        
        if self.salary is not None:
            self.salary = str(self.salary)
