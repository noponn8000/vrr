from components.ai import HostileEnemy;
from components.fighter import Fighter;
from entity import Actor;

player = Actor(
        char="@",
        color=(255, 255, 255),
        name="Player",
        ai_cls=HostileEnemy,
        fighter=Fighter(hp=30, defense=2, power=5),
);

toad = Actor(char="t", color=(25, 150, 25), name="Depraved Toad", ai_cls=HostileEnemy, fighter=Fighter(hp=10, defense=0, power=3));

tortoise = Actor(char="R", color=(25, 25, 150), name="Merciless Tortoise", ai_cls=HostileEnemy, fighter=Fighter(hp=16, defense=1, power=4));
