import random
import re

REFLECTIONS = {
    "i": "you",
    "me": "you",
    "my": "your",
    "mine": "yours",
    "myself": "yourself",
    "you": "I",
    "your": "my",
    "yours": "mine",
    "yourself": "myself",
    "am": "are",
    "are": "am",
}

RULES = [
    (
        "sorry",
        5,
        [
            (
                r".*\bsorry\b.*",
                ["Please don't apologise.", "Apologies are not necessary."],
            )
        ],
    ),
    (
        "remember",
        5,
        [
            (
                r".*\bremember\b(.+)",
                ["Do you often think about(1)?", "What else comes to mind about(1)?"],
            )
        ],
    ),
    (
        "dream",
        4,
        [
            (
                r".*\bdream\b(.+)",
                ["What does that dream suggest to you?", "Do you dream often?"],
            )
        ],
    ),
    (
        "mother|father|brother|sister|family",
        5,
        [
            (
                r".*",
                [
                    "Tell me more about your family.",
                    "How does that make you feel about your family?",
                ],
            )
        ],
    ),
    (
        "you are|you're",
        4,
        [
            (
                r".*(?:you are|you're) (.+)",
                ["What makes you think I am(1)?", "Why do you say I am(1)?"],
            )
        ],
    ),
    (
        "i am|i'm",
        4,
        [
            (
                r".*(?:i am|i'm) (.+)",
                ["How long have you been(1)?", "Why do you say you are(1)?"],
            )
        ],
    ),
    (
        "i need",
        4,
        [
            (
                r".*\bi need (.+)",
                ["Why do you need(1)?", "Would getting(1) change how you feel?"],
            )
        ],
    ),
    (
        "i want",
        4,
        [
            (
                r".*\bi want (.+)",
                ["What would having(1) do for you?", "Why do you want(1)?"],
            )
        ],
    ),
    (
        "because",
        3,
        [
            (
                r".*\bbecause (.+)",
                ["Is that the real reason?", "What other reasons might explain it?"],
            )
        ],
    ),
    (
        "why",
        3,
        [
            (
                r".*\bwhy\b(.+)",
                ["Why do you think that is?", "What answer would satisfy you?"],
            )
        ],
    ),
    ("yes|yep|yeah", 3, [(r".*", ["Please continue.", "How certain are you?"])]),
    ("no|nope", 3, [(r".*", ["You seem quite sure of that.", "Why not?"])]),
    (
        "hello|hi|hey",
        3,
        [
            (
                r".*",
                [
                    "Hello. How are you feeling today?",
                    "Hi. What would you like to talk about?",
                ],
            )
        ],
    ),
    (
        "always",
        2,
        [(r".*", ["Can you think of a specific example?", "When?", "Really, always?"])],
    ),
    (
        "computer|computers|machine|machines",
        50,
        [
            (
                r".*",
                [
                    "Do computers worry you?",
                    "Why do you mention computers?",
                    "What do you think machines have to do with your problem?",
                    "Don't you think computers can help people?",
                    "What about machines worries you?",
                ],
            )
        ],
    ),
    (
        "perhaps|maybe",
        3,
        [
            (
                r".*",
                [
                    "You don't seem quite certain.",
                    "Why the uncertain tone?",
                    "Can't you be more positive?",
                    "You aren't sure.",
                    "Don't you know?",
                ],
            )
        ],
    ),
    (
        "if",
        3,
        [
            (
                r".*\bif (.+)",
                [
                    "Do you think it's likely that(1)?",
                    "Do you wish that(1)?",
                    "What do you think about(1)?",
                    "Really,(1)?",
                ],
            )
        ],
    ),
    (
        "alike|same",
        10,
        [
            (
                r".*",
                [
                    "In what way?",
                    "What resemblance do you see?",
                    "What does that similarity suggest to you?",
                    "What other connections do you see?",
                    "Could there really be some connection?",
                ],
            )
        ],
    ),
    (
        "am",
        4,
        [
            (
                r".*\bare you (.+)",
                [
                    "Do you believe you are(1)?",
                    "Would you want to be(1)?",
                    "What would it mean if you were(1)?",
                ],
            ),
            (
                r".*\b(am|i am)\b.*",
                ["Why do you say 'am'?", "I don't understand that."],
            ),
        ],
    ),
    (
        "are",
        3,
        [
            (
                r".*\bare i (.+)",
                [
                    "Why are you interested in whether I am(1)?",
                    "Would you prefer if I weren't(1)?",
                    "Perhaps I am(1) in your fantasies.",
                ],
            ),
            (
                r".*\bare (.+)",
                [
                    "Did you think they might not be(1)?",
                    "Would you like it if they were not(1)?",
                    "What if they were not(1)?",
                    "Possibly they are(1).",
                ],
            ),
        ],
    ),
    (
        "was",
        2,
        [
            (
                r".*\bwas you (.+)",
                [
                    "What if you were(1)?",
                    "Do you think you were(1)?",
                    "What would it mean if you were(1)?",
                ],
            ),
            (
                r".*\bwas i (.+)",
                [
                    "Would you like to believe I was(1)?",
                    "What suggests that I was(1)?",
                    "Perhaps I was(1).",
                ],
            ),
            (
                r".*\bwas\b.*",
                ["Were you really?", "Why do you tell me about that now?"],
            ),
        ],
    ),
    (
        "my",
        2,
        [
            (
                r".*\bmy (.+)",
                [
                    "Why do you say your(1)?",
                    "Does that suggest anything else which belongs to you?",
                    "Is it important to you that it is your(1)?",
                ],
            )
        ],
    ),
    (
        "can",
        3,
        [
            (
                r".*\bcan i (.+)",
                [
                    "You believe I can(1), don't you?",
                    "You want me to be able to(1).",
                    "Perhaps you would like to be able to(1) yourself.",
                ],
            ),
            (
                r".*\bcan you (.+)",
                [
                    "Whether or not you can(1) depends on you more than me.",
                    "Do you want to be able to(1)?",
                    "Perhaps you don't want to(1).",
                ],
            ),
        ],
    ),
    (
        "what|how|when",
        2,
        [
            (
                r".*",
                [
                    "Why do you ask?",
                    "Does that question interest you?",
                    "What is it you really want to know?",
                    "Are such questions much on your mind?",
                    "What answer would please you most?",
                    "What do you think?",
                    "What comes to your mind when you ask that?",
                ],
            )
        ],
    ),
    (
        "everyone|everybody|nobody|noone",
        2,
        [
            (
                r".*",
                [
                    "Can you think of anyone in particular?",
                    "Who, for example?",
                    "You are thinking of a very special person.",
                    "Who do you think you're talking about?",
                ],
            )
        ],
    ),
    (
        "i",
        1,
        [(r".*\bi\b(.+)", ["You say(1).", "Can you explain what you mean by(1)?"])],
    ),
]

DEFAULT_RESPONSES = [
    "Please tell me more.",
    "Let's continue. What happens next?",
    "How does that make you feel?",
    "Can you say more about that?",
    "What does that suggest to you?",
]

RECENT_RESPONSES = []
LAST_TOPIC = None


def normalise(text):
    text = re.sub(r"[^a-z0-9' ]+", " ", text.lower().strip())
    return " ".join(text.split())


def reflect_fragment(fragment):
    result = " ".join(
        REFLECTIONS.get(word, word) for word in normalise(fragment).split()
    )
    result = result.strip(" ,.!?")
    return "" if not result else " " + result


def substitute(response, match):
    if match is None:
        return response
    for index in range(1, len(match.groups()) + 1):
        response = response.replace(
            f"({index})", reflect_fragment(match.group(index) or "")
        )
    return response


def choose_response(responses):
    """Choose a response without immediately repeating one."""
    choices = [response for response in responses if response not in RECENT_RESPONSES]
    if not choices:
        choices = responses
    response = random.choice(choices)
    RECENT_RESPONSES.append(response)
    del RECENT_RESPONSES[:-5]
    return response


def remember_topic(text):
    global LAST_TOPIC
    match = re.search(r"(?:i am|i'm|i need|i want) (.+)", text)
    if match:
        LAST_TOPIC = match.group(1).strip(" .?!")


def respond(message):
    global LAST_TOPIC
    text = normalise(message)
    if not text:
        return "Please say something."
    if re.fullmatch(r"(?:goodbye|bye|quit|exit)", text):
        LAST_TOPIC = None
        return "Goodbye. It was nice talking with you."

    remember_topic(text)
    if LAST_TOPIC and re.fullmatch(r"(?:continue|tell me more|yes|yeah)", text):
        topic = reflect_fragment(LAST_TOPIC).strip()
        return f"Earlier you mentioned {topic}. What about that concerns you now?"

    matches = []
    for keywords, priority, patterns in RULES:
        if re.search(r"(?:^|\b)(?:" + keywords + r")(?:\b|$)", text):
            matches.append((priority, patterns))

    for _priority, patterns in sorted(matches, key=lambda item: item[0], reverse=True):
        for pattern, responses in patterns:
            match = re.fullmatch(pattern, text)
            if match:
                return substitute(choose_response(responses), match)

    return choose_response(DEFAULT_RESPONSES)


def run():
    print("ELIZA: Hello. How are you feeling today?")
    print("Type 'quit' to end the conversation.")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nELIZA: Goodbye.")
            break
        if not user_input:
            continue
        reply = respond(user_input)
        print("ELIZA:", reply)
        if re.fullmatch(r"(?:goodbye|bye|quit|exit)", normalise(user_input)):
            break


if __name__ == "__main__":
    run()
