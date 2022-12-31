from __future__ import annotations;

from components.base_component import BaseComponent;

class DialogueNode():
    def __init__(self, text: str = "<No Dialogue>", choice_text = "<No Choice Text>", choices: List[DialogueNode]=[]):
        self.text = text;
        self.choice_text = choice_text;
        self.choices = choices;

class Dialogue(BaseComponent):
    def __init__(self, initial_node: DialogueNode=DialogueNode()):
        self.initial_node = initial_node;
        self.node = self.initial_node;

    @property
    def choices(self) -> List[DialogueNode]:
        return self.node.choices;

    @property
    def text(self) -> str:
        return self.node.text;

    def make_choice(self, index: int):
        if index >= len(self.choices):
            return;

        self.node  = self.node.choices[index];

    def reset(self):
        self.node = self.initial_node;
