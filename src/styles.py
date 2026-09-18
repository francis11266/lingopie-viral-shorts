"""Locked creative presets for the three viral styles (hook + CTA copy + voiceover).

Brand is spelled "Drama Riz" in the spoken lines so the TTS says *rizz* (rhymes with
"is"), not "rice"; on-screen text stays "DramaRizz".
"""

CTA_COMMON = {
    "tag": "Learn Spanish <b>just by watching drama.</b>",
    "btn": "⬇ Get DramaRizz free",
    "store": "📲 iOS — free on the App Store",
    "follow": "＋ Follow for a new word every day",
}
CTA_VO_COMMON = "Learn Spanish just by watching drama! Get Drama Riz, free!"

STYLES = {
    "s2": {  # POV / identity-call
        "hook": {"badge": "❚❚ PAUSED", "big1": "POV: you learn Spanish",
                 "big2": "from telenovelas 🇪🇸", "sub": "watch the 3 words 👇"},
        "hook_vo": "POV: you're learning Spanish from telenovelas!",
        "cta": dict(CTA_COMMON), "cta_vo": CTA_VO_COMMON,
    },
    "s3": {  # challenge / curiosity-gap
        "hook": {"badge": "CAN YOU CATCH 3?", "big1": "3 Spanish words are",
                 "big2": "hiding in this scene", "sub": "can you catch them? 👇"},
        "hook_vo": "Can you catch three Spanish words in this scene?!",
        "cta": dict(CTA_COMMON), "cta_vo": CTA_VO_COMMON,
    },
    "s4": {  # collect-the-words gamified counter
        "hook": {"badge": "⏱ BEAT THE SCENE", "big1": "Catch all 3 Spanish",
                 "big2": "words in this scene", "sub": "count with me 👇"},
        "hook_vo": "Catch all three Spanish words before this scene ends!",
        "cta": {"recap": "🎉 You just learned <b>3 Spanish words</b>",
                "tag": "Learn Spanish <b>just by watching drama.</b>",
                "btn": "⬇ Get 1000+ more, free",
                "store": "📲 iOS — free on the App Store"},
        "cta_vo": "That's three Spanish words! Learn more on Drama Riz, free!",
    },
}

# Friendly voice name -> real ElevenLabs library voice_id (American-first).
VOICES = {
    "adam (m, deep american)": "pNInz6obpgDQGcFmaJgB",
    "brian (m, american narrator)": "nPczCjzI2devNBz1zQrb",
    "bill (m, warm american)": "pqHfZKP75CvOlQylNhV4",
    "rachel (f, american)": "21m00Tcm4TlvDq8ikWAM",
    "jessica (f, energetic american)": "cgSgspJ2msm6clMCkdW9",
}
DEFAULT_VOICE = "pNInz6obpgDQGcFmaJgB"  # Adam
