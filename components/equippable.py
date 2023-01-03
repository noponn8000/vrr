from __future__ import annotations;

from typing import TYPE_CHECKING;
import random;

from components.base_component import BaseComponent;
from equipment_types import EquipmentType;

if TYPE_CHECKING:
    from entity import Item;

class Equippable(BaseComponent):
    parent: Item;

    def __init__(
            self,
            equipment_type: EquipmentType,
            penetration: int = 0,
            damage_roll = 0,
            roll_number = 0,
            defense_bonus: int = 0
    ):
        self.equipment_type = equipment_type;

        self.penetration = penetration;
        self.damage_roll = damage_roll;
        self.roll_number = roll_number;
        self.defense_bonus = defense_bonus;

    def calculate_damage(self, user_strength: int, enemy_defense: int) -> int:
        damage = 0;
        for i in range(self.roll_number):
            damage += max(0, (random.randint(0, self.damage_roll + 1) + user_strength * (self.penetration * enemy_defense)));

        return damage;

class TinDagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, penetration=2, damage_roll=6, roll_number=1)

class TinSword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.WEAPON, penetration=4, damage_roll=8, roll_number=1);

class LeatherTopcoat(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=1);

class ChainMail(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.ARMOR, defense_bonus=3);
