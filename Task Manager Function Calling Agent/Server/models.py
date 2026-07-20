from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Task:
    id: int
    title: str
    description: str
    task_type: str
    start_date: Optional[str]
    end_date: Optional[str]
    status: str

    def to_dict(self):
        return asdict(self)