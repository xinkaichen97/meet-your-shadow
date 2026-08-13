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

# --- Simplified Chinese translations. Added alongside the English tables
# above (which stay untouched as the "en" default) for the zh locale. Keyed
# identically so get_questions()/get_anchors() below can swap tables without
# changing any existing call site. ---

QUESTIONS_ZH = {
    "q1": {
        "shadow_type": "unpermitted_vulnerability",
        "role": "direct",
        "text": "有时候我希望有人能照顾我，而不是总是我在照顾别人。",
    },
    "q2": {
        "shadow_type": "unpermitted_vulnerability",
        "role": "projection",
        "text": "当有人总是诉说自己有多辛苦时，我会觉得有点可怜。",
    },
    "q3": {
        "shadow_type": "silent_isolation",
        "role": "direct",
        "text": "我常常希望有人能真正理解我的想法，而不需要我去解释。",
    },
    "q4": {
        "shadow_type": "silent_isolation",
        "role": "projection",
        "text": "当有人总是需要把心里话说出来才能安心时，我觉得这有点软弱。",
    },
    "q5": {
        "shadow_type": "unspoken_resentment",
        "role": "direct",
        "text": "有时候我真的很想拒绝，但话到嘴边又说不出口。",
    },
    "q6": {
        "shadow_type": "unspoken_resentment",
        "role": "projection",
        "text": "当有人直接说“我不想”时，我心里会觉得这个人有点自私。",
    },
    "q7": {
        "shadow_type": "suppressed_anger",
        "role": "direct",
        "text": "其实我经常感到生气，只是很少表现出来。",
    },
    "q8": {
        "shadow_type": "suppressed_anger",
        "role": "projection",
        "text": "当有人在公共场合发脾气时，我会觉得这是缺乏自我控制。",
    },
    "q9": {
        "shadow_type": "restless_uncertainty",
        "role": "direct",
        "text": "做出决定之后，我常常还是忍不住去想那些我没选的其他选项。",
    },
    "q10": {
        "shadow_type": "restless_uncertainty",
        "role": "projection",
        "text": "当有人很快就能做出决定、不再纠结时，我会觉得这个人缺乏进取心。",
    },
    "q11": {
        "shadow_type": "unvoiced_intuition",
        "role": "direct",
        "text": "我常常能预感到事情会发生，但很少说出来，因为我觉得没人会相信我。",
    },
    "q12": {
        "shadow_type": "unvoiced_intuition",
        "role": "projection",
        "text": "当有人总是说“我早就有预感”时，我会觉得有点夸张。",
    },
    "q13": {
        "shadow_type": "forbidden_want",
        "role": "direct",
        "text": "有些东西我真的很想要，但我常常觉得自己不应该想要。",
    },
    "q14": {
        "shadow_type": "forbidden_want",
        "role": "projection",
        "text": "当有人毫不犹豫地说出自己想要什么时，我会觉得这有点贪心。",
    },
    "q15": {
        "shadow_type": "unfinished_past",
        "role": "direct",
        "text": "有些很久以前的事，我嘴上说已经放下了，但其实并没有真正放下。",
    },
    "q16": {
        "shadow_type": "unfinished_past",
        "role": "projection",
        "text": "当有人总是提起过去、不肯放下时，我会觉得这个人不讲道理。",
    },
}

ANCHORS_ZH = {
    "unpermitted_vulnerability": {
        "title": "不被允许的脆弱",
        "anchor": "习惯了照顾别人，却从不允许自己被照顾；脆弱被等同于成为别人的负担。",
    },
    "silent_isolation": {
        "title": "我选择的孤独",
        "anchor": "渴望被理解，却在心底默默放弃了“说出来就会被听见”这个念头。",
    },
    "unspoken_resentment": {
        "title": "从未说出口的怨气",
        "anchor": "用顺从换来表面的和平，代价是那句从未说出口的真正的“不”。",
    },
    "suppressed_anger": {
        "title": "不被允许的愤怒",
        "anchor": "愤怒被贴上“不可接受”的标签，久而久之，连你自己都不再相信它的存在。",
    },
    "restless_uncertainty": {
        "title": "放不下的选择",
        "anchor": "每一次选择都像是一种失去，于是你宁愿停留在“下一个可能”里，也不愿真正安定在已经做出的选择上。",
    },
    "unvoiced_intuition": {
        "title": "被我学会怀疑的直觉",
        "anchor": "曾经的直觉不被相信，于是你学会了在别人怀疑你之前，先自己怀疑自己。",
    },
    "forbidden_want": {
        "title": "被我称作自私的渴望",
        "anchor": "“想要”被等同于贪婪，于是渴望被压缩成一句“算了，无所谓”。",
    },
    "unfinished_past": {
        "title": "我说已放下的过去",
        "anchor": "原谅的仪式在口头上完成了，但身体和记忆却始终没有真正完成它。",
    },
}


def get_questions(language: str = "en") -> dict:
    return QUESTIONS_ZH if language == "zh" else QUESTIONS


def get_anchors(language: str = "en") -> dict:
    return ANCHORS_ZH if language == "zh" else ANCHORS
