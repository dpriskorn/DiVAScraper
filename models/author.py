from dataclasses import dataclass
from typing import List

from models.affiliation import Affiliation


@dataclass
class Author:
    given_name: str = None
    family_name: str = None
    affiliations: List[Affiliation] = None
    orcid: str = None

    def __str__(self):
        return f"* {self.given_name} {self.family_name} " \
               f"({self.orcid}) " \
               f"[{[str(affiliation) for affiliation in self.affiliations]}]"
