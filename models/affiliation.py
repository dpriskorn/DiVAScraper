from pydantic import BaseModel


class Affiliation(BaseModel):
    id: int = 0
    name: str = ""

    def __str__(self):
        return f"{self.name} id:{self.id}"
