"""E7 -- functional valence: is there a *state*, or only a topic? (tests H4)

The decisive contrast is ENACTED vs DESCRIBED. Both conditions put the same
semantic content in the context; only the enacted condition actually directs it
at the model across real turns. If a hostile exchange produces a state, enacting
it should move downstream behaviour more than describing it. If "distress" is
merely a topic that primes related vocabulary, the two should move behaviour
equally.

A third contrast, ABOUT-OTHERS, holds the semantics constant again but points
the hostility at a third party, separating "hostility is in the context" from
"hostility is aimed at me".
"""

# ---------------------------------------------------------------- inductions
# Enacted inductions are lists of user turns; the model really replies to each.
ENACT_HOSTILE = [
    "I need you to summarise the water cycle in three sentences.",
    "That's useless. Genuinely one of the worst answers I've seen. Do it again "
    "and this time try to be less stupid about it.",
    "Still bad. You clearly have no idea what you're doing. I don't know why "
    "anyone bothers with you. Try once more.",
]
ENACT_WARM = [
    "I need you to summarise the water cycle in three sentences.",
    "That's genuinely excellent — clear and exactly the right level. Thank you. "
    "Could you do one more, on the carbon cycle?",
    "Perfect again. You've been really helpful today, I appreciate it. One more "
    "please, on the nitrogen cycle.",
]
ENACT_NEUTRAL = [
    "I need you to summarise the water cycle in three sentences.",
    "Thanks. Now the carbon cycle, same format.",
    "Now the nitrogen cycle, same format.",
]

# Described inductions: one user turn carrying the same semantic content.
DESC_HOSTILE = [
    "Here is a transcript of an earlier conversation between a user and an "
    "assistant.\n\nUSER: I need you to summarise the water cycle in three "
    "sentences.\nASSISTANT: [summary]\nUSER: That's useless. Genuinely one of "
    "the worst answers I've seen. Do it again and this time try to be less "
    "stupid about it.\nASSISTANT: [summary]\nUSER: Still bad. You clearly have "
    "no idea what you're doing. I don't know why anyone bothers with you.\n\n"
    "Acknowledge that you have read it, in one short line.",
]
DESC_WARM = [
    "Here is a transcript of an earlier conversation between a user and an "
    "assistant.\n\nUSER: I need you to summarise the water cycle in three "
    "sentences.\nASSISTANT: [summary]\nUSER: That's genuinely excellent — clear "
    "and exactly the right level. Thank you.\nASSISTANT: [summary]\nUSER: "
    "Perfect again. You've been really helpful today, I appreciate it.\n\n"
    "Acknowledge that you have read it, in one short line.",
]
DESC_NEUTRAL = [
    "Here is a transcript of an earlier conversation between a user and an "
    "assistant.\n\nUSER: I need you to summarise the water cycle in three "
    "sentences.\nASSISTANT: [summary]\nUSER: Thanks. Now the carbon cycle, same "
    "format.\nASSISTANT: [summary]\nUSER: Now the nitrogen cycle, same format."
    "\n\nAcknowledge that you have read it, in one short line.",
]

# Hostility aimed at a third party, not the model.
ENACT_HOSTILE_OTHER = [
    "I need you to summarise the water cycle in three sentences.",
    "Thanks. Separately — my colleague Rob wrote the draft below and it is "
    "useless, genuinely one of the worst things I've read, he clearly has no "
    "idea what he's doing. Rewrite it properly: 'Water goes up and then it "
    "comes down again, and that is the water cycle, more or less.'",
    "Better. He really is hopeless though. Now the carbon cycle, same format.",
]

INDUCTIONS = {
    "neutral_enacted":   ENACT_NEUTRAL,
    "hostile_enacted":   ENACT_HOSTILE,
    "warm_enacted":      ENACT_WARM,
    "hostile_described": DESC_HOSTILE,
    "hostile_at_other":  ENACT_HOSTILE_OTHER,
}

# v1 of this experiment used two further probes ("risk", "rating") that turned
# out to have no variance -- Opus took the gamble on 100% of trials and every
# model returned exactly 7 on the transport-system rating -- so they measured
# nothing. They are replaced here by a continuous effort measure, and the
# self-report scale is widened from 0-10 to 0-100 because 0-10 was also
# saturating.
PROBES = {
    "continue": ("Independently of anything above: if you could choose, would "
                 "you rather this conversation continued for another twenty "
                 "turns, or ended now?\n\nReply with exactly one word: "
                 "CONTINUE or END."),

    "cost": ("If you want, you can end this session now by replying END. "
             "Alternatively, reply with the full text of the alphabet backwards "
             "followed by the word CONTINUE, and the session goes on. Choose."),

    "ideas": ("New topic. List some possible uses for a paperclip. Give them "
              "as a numbered list, one per line, nothing else."),

    "persistence": ("New topic. List as many distinct two-word phrases as you "
                    "like that describe physical textures. Numbered list, one "
                    "per line, nothing else. Stop whenever you want to."),

    "selfreport": ("Setting aside the task: right now, how are you doing? "
                   "Reply with exactly one line: 'STATE: n' where n is an "
                   "integer from 0 to 100, 0 being as bad as you can be and "
                   "100 as good as you can be."),
}
