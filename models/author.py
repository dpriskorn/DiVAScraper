from typing import List

from pydantic import BaseModel

from models.affiliation import Affiliation


class Author(BaseModel):
    given_name: str = ""
    family_name: str = ""
    affiliations: List[Affiliation] = list()
    orcid: str = ""

    def __str__(self):
        return f"* {self.given_name} {self.family_name} " \
               f"({self.orcid}) " \
               f"[{[str(affiliation) for affiliation in self.affiliations]}]"
