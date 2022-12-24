from components.ai import HostileEnemy;
from components import consumable;
from components.fighter import Fighter;
from components.inventory import Inventory;
from components.level import Level;
from entity import Actor, Item;
import color;

player = Actor(
        char="@",
        color=(255, 255, 255),
        name="Player",
        description="It's you. An enigmatic character, you appear suspicious even to yourself.",
        ai_cls=HostileEnemy,
        fighter=Fighter(hp=30, defense=2, power=5),
        inventory=Inventory(capacity=26),
        level=Level(level_up_base=200)
);

toad = Actor(char="t",
             color=(25, 150, 25),
             name="Depraved Toad",
             description="This restless amphibian scours the obscure corners of Varr, constantly being driven back and forth by the migrations of more powerful beings. Even though nothing is known about these creatures' moral compass, or lack thereof, their depravity is a generally accepted fact, even constituting the greater part of its name.",
             ai_cls=HostileEnemy,
             fighter=Fighter(hp=10, defense=0, power=3),
             inventory=Inventory(capacity=0),
             level=Level(xp_given=35)
             );

tortoise = Actor(char="R",
                 color=(25, 25, 150),
                 name="Merciless Tortoise",
                 description="One can barely make out a small, dessicated head lurking beneath the thick armor of this plated reptile. Curiously, almost all of the specimen alive today are hundreds of years old and their population shrinks constantly, in part thanks to you. One can only wonder why this creature takes such pleasure in brutalizing travellers.",
                 ai_cls=HostileEnemy,
                 fighter=Fighter(hp=16, defense=1, power=4),
                 inventory=Inventory(capacity=0),
                 level=Level(xp_given=100)
                 );

health_potion = Item(
        char="!",
        color=(127, 0, 255),
        name="Health Potion",
        description="A sturdy phial containing distilled Spirit. Once open, the smell would put off anyone who is not in true need of its powers, perhaps as a means of ensuring that it is used properly. The viscous liquid swirls around in the phial, a mysterious concoction teeming with concentrated life. Why these helpful flasks are in abundance inside all manner of dungeons, caves and other unexplored places of Varr remains a mystery.",
        consumable=consumable.HealingConsumable(amount=4)
);

lightning_scroll = Item(
    char="~",
    color=color.lightning,
    name="Lightning Scroll",
    description="This hazardous sheaf of aged parchment uses the caster's body as a vessel to concentrate vast amounts of electrical energy, which is then grounded through the assistance of the nearest bystander. However, it is not unheard of that the caster is affected as well.",
    consumable=consumable.LightningDamageConsumable(damage=20, maximum_range=5)
);

confusion_scroll = Item(
    char="~",
    color=color.confusion,
    name="Confusion Scroll",
    description="Legends of old tell many stories of intrepid mages who managed to storm entire forts without being discovered through scrolls whose effect imitated that of a joyful soldier's evening in the tavern after being dismissed from duty.",
    consumable=consumable.ConfusionConsumable(number_of_turns=10)
);

fireball_scroll = Item(
    char="~",
    color=color.fireball,
    name="Fireball Scroll",
    description="The court overseeing the laws regarding magic enforced a rule stating that all scribes must add the words `use with care` to their fireball scrolls after one soon-to-be emperor made a fiery start to his arcane education with one of such spells.",
    consumable=consumable.FireballDamageConsumable(damage=12, radius=3)
);
