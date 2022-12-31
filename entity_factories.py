import copy;

from components.ai import HostileEnemy, StaticObjectAI;
from components import consumable, equippable;
from components.fighter import Fighter;
from components.inventory import Inventory, Slot;
from components.level import Level;
from components.equipment import Equipment, EquipmentType;
from components.dialogue import Dialogue;
from components.attributes import Attributes;
from entity import Actor, Entity, Item;
import dialogue_factories;
import color;

basalt_rock = Item(
    char="o",
    color=(20, 20, 20),
    name="Basalt Rock",
    description="A small piece of hardened magma. Due to its relative scarcity and durabilty, it is valued by merchants as tender.",
    equippable=equippable.Equippable(EquipmentType.WEAPON,power_bonus=1, defense_bonus=0)
);

pickaxe = Item(
    char="^",
    color=color.steel,
    description="A well-worn pickaxe. Countless such tools were given out to the condemned who were sent to work in the Tar Pits. Little did their overseers know that these same tools would then be used by the enslaved to decimate their masters once the noxious fumes of the Ferrum deprived them of their wits.",
    equippable=equippable.Equippable(EquipmentType.WEAPON, power_bonus=3, defense_bonus=0)
)

toad = Actor(char="t",
             color=(25, 150, 25),
             name="Depraved Toad",
             description="This restless amphibian scours the obscure corners of Varr, constantly being driven back and forth by the migrations of more powerful beings. Even though nothing is known about these creatures' moral compass, or lack thereof, their depravity is a generally accepted fact, even constituting the greater part of its name.",
             ai_cls=HostileEnemy,
             equipment=Equipment(),
             fighter=Fighter(),
             inventory=Inventory(capacity=2),
             level=Level(xp_given=35),
             dialogue=dialogue_factories.toad_dialogue,
             attributes=Attributes({"vitality": 1, "strength": 1, "resistance": 1})
             );

tortoise = Actor(char="R",
                 color=(25, 25, 150),
                 name="Merciless Tortoise",
                 description="One can barely make out a small, dessicated head lurking beneath the thick armor of this plated reptile. Curiously, almost all of the specimen alive today are hundreds of years old and their population shrinks constantly, in part thanks to you. One can only wonder why this creature takes such pleasure in brutalizing travellers.",
                 ai_cls=HostileEnemy,
                 equipment=Equipment(),
                 fighter=Fighter(),
                 inventory=Inventory(capacity=0),
                 level=Level(xp_given=100),
                 dialogue=Dialogue(),
                 attributes=Attributes({"vitality": 1, "strength": 1, "resistance": 1})
                 );

miner = Actor(char="M",
              color=(220, 0, 50),
              name="Lapidified Miner",
              description="The hard crust of compressed volcanic ash mixed with centuries-old mud and grime hides a hollow interior which may once have housed a soul.",
              ai_cls=HostileEnemy,
              equipment=Equipment(),
              inventory=Inventory(capacity=2),
              fighter=Fighter(),
              level=Level(xp_given=250),
              dialogue=Dialogue(),
              attributes=Attributes({"vitality": 1, "strength": 1, "resistance": 1})
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

dagger = Item(
    char=",",
    color=color.tin,
    name="Tin Dagger",
    description="This shoddy knife is an average traveller's best friend, as its ease of production and low material cost have made it the go-to equipment for civilians wishing for self-defense in the wild parts of Varr.",
    equippable=equippable.TinDagger()
);

sword = Item(
    char="/",
    color=color.tin,
    name="Tin Sword",
    description="You can faintly see your reflection in the rough blade of this worn blade. The cutting-edge is full of cracks and blunt enough that the weapon could be considered a blunt tool.",
    equippable=equippable.TinSword()
);

leather_topcoat = Item(
    char="{",
    color=color.leather,
    name="Leather Topcoat",
    description="A staple of the average adventurer's attire, this coat protects you from the elements, but not much more.",
    equippable=equippable.LeatherTopcoat()
);

chain_mail = Item(
    char="{",
    color=color.steel,
    name="Chain Mail",
    description="A marker of a new recruit in the army. The previous owner must have had his career cut short.",
    equippable=equippable.ChainMail()
);

player = Actor(
        char="@",
        color=(255, 255, 255),
        name="Player",
        description="It's you. An enigmatic character, you appear suspicious even to yourself.",
        ai_cls=HostileEnemy,
        equipment=Equipment(),
        fighter=Fighter(),
        inventory=Inventory(capacity=26, items=[Slot(copy.deepcopy(dagger)), Slot(copy.deepcopy(leather_topcoat))]),
        level=Level(level_up_base=200),
        dialogue=Dialogue(),
        attributes=Attributes(),
);

chest = Entity(
    char="#",
    color=(255, 255, 255),
    name="Chest",
    description="A collection of thin, wooden planks held together by a few rusty strips of iron. The lock probably does not hold anymore.",
    blocks_movement=False,
    inventory=Inventory(capacity=26, items=[Slot(copy.deepcopy(chain_mail))], accessible=True),
);
