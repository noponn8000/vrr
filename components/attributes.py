from __future__ import annotations;

from components.base_component import BaseComponent;
from typing import Dict, TYPE_CHECKING;

if TYPE_CHECKING:
    from entity import Actor;

class Attributes(BaseComponent):
    parent: Actor;

    def __init__(self, attributes: Dict[str, int] = {}):
        self.attributes = attributes;
