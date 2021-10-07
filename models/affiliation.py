from dataclasses import dataclass


@dataclass
class Affiliation:
    id: int = None
    name: str = None

    def __str__(self):
        return f"{self.name} id:{self.id}"