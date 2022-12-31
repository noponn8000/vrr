from components.dialogue import Dialogue, DialogueNode;

toad_dialogue = Dialogue(DialogueNode(text="*The toad wishes not to speak to you*",
                                      choices=[
                                          DialogueNode(text="*Hiss*", choice_text="I bid thee farewell, amphibian."),
                                          DialogueNode(text="*The toad looks at you scornfully*", choice_text="How do you like it here in the Basalt Mines?"),
                                          DialogueNode(text="*The eyes of the wild animal show no sign of comprehension*", choice_text="Do you have anything to trade?"),
                                      ]
));
