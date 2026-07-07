"""Static content for the Shadow Self-Reflection Agent.

Source of truth: shadow_test_agent_spec.md (project root), sections 3, 5, 6.
"""

QUESTIONS = {
    "q1": {
        "shadow_type": "unpermitted_vulnerability",
        "role": "direct",
        "text": "Sometimes I wish someone would take care of me, instead of me always being the one taking care of others.",
    },
    "q2": {
        "shadow_type": "unpermitted_vulnerability",
        "role": "projection",
        "text": "When someone constantly talks about how hard things are for them, I find it a little pathetic.",
    },
    "q3": {
        "shadow_type": "silent_isolation",
        "role": "direct",
        "text": "I often wish someone could truly understand what I'm thinking without me having to explain.",
    },
    "q4": {
        "shadow_type": "silent_isolation",
        "role": "projection",
        "text": "When someone always needs to say what's on their mind to feel okay, I find that a bit weak.",
    },
    "q5": {
        "shadow_type": "unspoken_resentment",
        "role": "direct",
        "text": "There are times I really want to say no, but the words get stuck before I say them.",
    },
    "q6": {
        "shadow_type": "unspoken_resentment",
        "role": "projection",
        "text": "When someone flatly says \"I don't want to,\" I secretly think they're a bit selfish.",
    },
    "q7": {
        "shadow_type": "suppressed_anger",
        "role": "direct",
        "text": "I actually feel angry fairly often, I just rarely show it.",
    },
    "q8": {
        "shadow_type": "suppressed_anger",
        "role": "projection",
        "text": "When someone loses their temper in public, I think that's poor self-control.",
    },
    "q9": {
        "shadow_type": "restless_uncertainty",
        "role": "direct",
        "text": "After making a decision, I often still can't stop thinking about the other options I didn't choose.",
    },
    "q10": {
        "shadow_type": "restless_uncertainty",
        "role": "projection",
        "text": "When someone settles into a decision quickly and stops second-guessing, I think they lack ambition.",
    },
    "q11": {
        "shadow_type": "unvoiced_intuition",
        "role": "direct",
        "text": "I often sense things are going to happen before they do, but I rarely say so because I doubt anyone would believe me.",
    },
    "q12": {
        "shadow_type": "unvoiced_intuition",
        "role": "projection",
        "text": "When someone keeps saying \"I had a feeling about this,\" I find it a bit theatrical.",
    },
    "q13": {
        "shadow_type": "forbidden_want",
        "role": "direct",
        "text": "There are things I genuinely want, but I often feel I shouldn't want them.",
    },
    "q14": {
        "shadow_type": "forbidden_want",
        "role": "projection",
        "text": "When someone openly says what they want without hesitation, I think that's a little greedy.",
    },
    "q15": {
        "shadow_type": "unfinished_past",
        "role": "direct",
        "text": "There are things from a long time ago that I say I've let go of, but I haven't, not really.",
    },
    "q16": {
        "shadow_type": "unfinished_past",
        "role": "projection",
        "text": "When someone keeps bringing up the past and won't let it go, I think they're being unreasonable.",
    },
}

# shadow_type -> (direct_question_id, projection_question_id)
SHADOW_PAIRS = {
    "unpermitted_vulnerability": ("q1", "q2"),
    "silent_isolation": ("q3", "q4"),
    "unspoken_resentment": ("q5", "q6"),
    "suppressed_anger": ("q7", "q8"),
    "restless_uncertainty": ("q9", "q10"),
    "unvoiced_intuition": ("q11", "q12"),
    "forbidden_want": ("q13", "q14"),
    "unfinished_past": ("q15", "q16"),
}

FOLLOWUP_TEMPLATES = {
    "unpermitted_vulnerability": {
        "prompt": "You said you rarely wish to be cared for, but also find it a bit pathetic when others openly share how hard things are. Which feels closer to you right now?",
        "option_a": "I do wish I could be taken care of sometimes — it's just hard to ask.",
        "option_b": "Taking care of myself is still something I'd rather handle alone.",
    },
    "silent_isolation": {
        "prompt": "You said you wish to be truly understood, but also find it a bit weak when others always need to voice what's on their mind. Which feels closer to you right now?",
        "option_a": "Some things I haven't said, because I'm afraid it wouldn't matter anyway.",
        "option_b": "Some things don't need saying — no one would really get it regardless.",
    },
    "unspoken_resentment": {
        "prompt": "You said you often want to say no but the words get stuck, but also think people who flatly refuse are a bit selfish. Which feels closer to you right now?",
        "option_a": "There are more moments than I'd like to admit where I wanted to say no and didn't.",
        "option_b": "When it comes to refusing, I'd rather just let it go.",
    },
    "suppressed_anger": {
        "prompt": "You said you feel angry often but rarely show it, but also think losing your temper in public shows poor self-control. Which feels closer to you right now?",
        "option_a": "There might be more anger in me than I've let myself admit.",
        "option_b": "I'd honestly rather that anger didn't exist at all.",
    },
    "restless_uncertainty": {
        "prompt": "You said you can't stop thinking about other options after deciding, but also think people who settle quickly lack ambition. Which feels closer to you right now?",
        "option_a": "I may never have really let myself settle on anything.",
        "option_b": "Keeping other possibilities open is what makes me feel safe.",
    },
    "unvoiced_intuition": {
        "prompt": "You said you often sense things before they happen but rarely say so, but also find it theatrical when others claim the same. Which feels closer to you right now?",
        "option_a": "There's probably more unspoken intuition in me than I admit.",
        "option_b": "Saying it out loud doesn't really change anything anyway.",
    },
    "forbidden_want": {
        "prompt": "You said you want things you feel you shouldn't want, but also think people who openly want things are a bit greedy. Which feels closer to you right now?",
        "option_a": "I probably want more than I'm comfortable admitting.",
        "option_b": "It's better to keep wanting things quietly.",
    },
    "unfinished_past": {
        "prompt": "You said you claim to have let go of old things but haven't really, but also think people who keep bringing up the past are being unreasonable. Which feels closer to you right now?",
        "option_a": "There may be more I haven't let go of than I thought.",
        "option_b": "Bringing up the past doesn't really help — better to move forward.",
    },
}

ANCHORS = {
    "unpermitted_vulnerability": {
        "title": "The Vulnerability I Wasn't Allowed",
        "anchor": "Used to taking care of others, never allowing yourself to be taken care of; vulnerability got equated with being a burden.",
    },
    "silent_isolation": {
        "title": "The Isolation I Chose",
        "anchor": "Craving to be understood, but having quietly given up on the idea that saying it out loud would ever be heard.",
    },
    "unspoken_resentment": {
        "title": "The Resentment I Never Said",
        "anchor": "Keeping the peace through compliance, at the cost of a real \"no\" that was never voiced.",
    },
    "suppressed_anger": {
        "title": "The Anger I Wasn't Allowed",
        "anchor": "Anger got labeled as unacceptable, so eventually even you stopped believing it was there.",
    },
    "restless_uncertainty": {
        "title": "The Choice I Can't Let Go Of",
        "anchor": "Every choice feels like a loss, so you stay in the next possibility instead of the one you already made.",
    },
    "unvoiced_intuition": {
        "title": "The Knowing I Learned to Doubt",
        "anchor": "Intuition once went unbelieved, so you learned to doubt yourself before anyone else could.",
    },
    "forbidden_want": {
        "title": "The Wanting I Called Selfish",
        "anchor": "Wanting got equated with greed, so desire got compressed into \"never mind, it doesn't matter.\"",
    },
    "unfinished_past": {
        "title": "The Past I Said I'd Let Go",
        "anchor": "The ritual of forgiving happened out loud, but the body and memory never quite finished it.",
    },
}
