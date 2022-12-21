from components.ai import HostileEnemy;
from components import consumable;
from components.fighter import Fighter;
from components.inventory import Inventory;
from entity import Actor, Item;
import color;

player = Actor(
        char="@",
        color=(255, 255, 255),
        name="Player",
        ai_cls=HostileEnemy,
        fighter=Fighter(hp=30, defense=2, power=5),
        inventory=Inventory(capacity=26)
);

toad = Actor(char="t", color=(25, 150, 25), name="Depraved Toad", ai_cls=HostileEnemy, fighter=Fighter(hp=10, defense=0, power=3), inventory=Inventory(capacity=0));

tortoise = Actor(char="R", color=(25, 25, 150), name="Merciless Tortoise", ai_cls=HostileEnemy, fighter=Fighter(hp=16, defense=1, power=4), inventory=Inventory(capacity=0));

health_potion = Item(
        char="!",
        color=(127, 0, 255),
        name="Health Potion",
        consumable=consumable.HealingConsumable(amount=4)
);

lightning_scroll = Item(
    char="~",
    color=color.lightning,
    name="Lightning Scroll",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5)
);

confusion_scroll = Item(
    char="~",
    color=color.confusion,
    name="Confusion Scroll",
    consumable=consumable.ConfusionConsumable(number_of_turns=10)
);

fireball_scroll = Item(
    char="~",
    color=color.fireball,
    name="Fireball Scroll",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3)
);
