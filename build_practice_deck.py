"""Builds practice_deck.json - the static content for the daily practice slip.

Run once, and again after editing the word lists / verb tables below:

    py build_practice_deck.py

Spanish conjugations are generated from the tables here rather than typed out
one by one, so a whole tense cannot be half-wrong from a single typo. Gregg
answers are looked up in the dictionaries bundled with the `grascii` package
(built from the 1916 and 1930 Gregg Shorthand Dictionaries), so they are not
hand-authored either.
"""

import json
import pathlib
import random
import re

DECK_PATH = pathlib.Path(__file__).with_name("practice_deck.json")

#############################################################################
################################## SPANISH ##################################

PRONOUNS = ["yo", "tu", "el/ella", "nosotros", "vosotros", "ellos"]

# Regular endings by tense. Future endings attach to the whole infinitive.
REGULAR_ENDINGS = {
    "present":   {"ar": ["o", "as", "a", "amos", "áis", "an"],
                  "er": ["o", "es", "e", "emos", "éis", "en"],
                  "ir": ["o", "es", "e", "imos", "ís", "en"]},
    "preterite": {"ar": ["é", "aste", "ó", "amos", "asteis", "aron"],
                  "er": ["í", "iste", "ió", "imos", "isteis", "ieron"],
                  "ir": ["í", "iste", "ió", "imos", "isteis", "ieron"]},
    "imperfect": {"ar": ["aba", "abas", "aba", "ábamos", "abais", "aban"],
                  "er": ["ía", "ías", "ía", "íamos", "íais", "ían"],
                  "ir": ["ía", "ías", "ía", "íamos", "íais", "ían"]},
}
FUTURE_ENDINGS = ["é", "ás", "á", "emos", "éis", "án"]

REGULAR_VERBS = [("hablar", "to speak"), ("comer", "to eat"), ("vivir", "to live"),
                 ("trabajar", "to work"), ("aprender", "to learn"), ("escribir", "to write")]

# Irregular forms are written out because rules do not produce them.
IRREGULAR_VERBS = {
    "ser": {"gloss": "to be (essence)",
            "present":   ["soy", "eres", "es", "somos", "sois", "son"],
            "preterite": ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"],
            "imperfect": ["era", "eras", "era", "éramos", "erais", "eran"],
            "future":    ["seré", "serás", "será", "seremos", "seréis", "serán"]},
    "estar": {"gloss": "to be (state)",
            "present":   ["estoy", "estás", "está", "estamos", "estáis", "están"],
            "preterite": ["estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron"],
            "imperfect": ["estaba", "estabas", "estaba", "estábamos", "estabais", "estaban"],
            "future":    ["estaré", "estarás", "estará", "estaremos", "estaréis", "estarán"]},
    "ir": {"gloss": "to go",
            "present":   ["voy", "vas", "va", "vamos", "vais", "van"],
            "preterite": ["fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron"],
            "imperfect": ["iba", "ibas", "iba", "íbamos", "ibais", "iban"],
            "future":    ["iré", "irás", "irá", "iremos", "iréis", "irán"]},
    "ver": {"gloss": "to see",
            "present":   ["veo", "ves", "ve", "vemos", "veis", "ven"],
            "preterite": ["vi", "viste", "vio", "vimos", "visteis", "vieron"],
            "imperfect": ["veía", "veías", "veía", "veíamos", "veíais", "veían"],
            "future":    ["veré", "verás", "verá", "veremos", "veréis", "verán"]},
    "tener": {"gloss": "to have",
            "present":   ["tengo", "tienes", "tiene", "tenemos", "tenéis", "tienen"],
            "preterite": ["tuve", "tuviste", "tuvo", "tuvimos", "tuvisteis", "tuvieron"],
            "imperfect": ["tenía", "tenías", "tenía", "teníamos", "teníais", "tenían"],
            "future":    ["tendré", "tendrás", "tendrá", "tendremos", "tendréis", "tendrán"]},
    "hacer": {"gloss": "to do / make",
            "present":   ["hago", "haces", "hace", "hacemos", "hacéis", "hacen"],
            "preterite": ["hice", "hiciste", "hizo", "hicimos", "hicisteis", "hicieron"],
            "imperfect": ["hacía", "hacías", "hacía", "hacíamos", "hacíais", "hacían"],
            "future":    ["haré", "harás", "hará", "haremos", "haréis", "harán"]},
    "decir": {"gloss": "to say",
            "present":   ["digo", "dices", "dice", "decimos", "decís", "dicen"],
            "preterite": ["dije", "dijiste", "dijo", "dijimos", "dijisteis", "dijeron"],
            "imperfect": ["decía", "decías", "decía", "decíamos", "decíais", "decían"],
            "future":    ["diré", "dirás", "dirá", "diremos", "diréis", "dirán"]},
    "poder": {"gloss": "to be able",
            "present":   ["puedo", "puedes", "puede", "podemos", "podéis", "pueden"],
            "preterite": ["pude", "pudiste", "pudo", "pudimos", "pudisteis", "pudieron"],
            "imperfect": ["podía", "podías", "podía", "podíamos", "podíais", "podían"],
            "future":    ["podré", "podrás", "podrá", "podremos", "podréis", "podrán"]},
}

# Only these person slots become cards - drilling all six persons of every
# tense is 200+ near-identical cards. 1sg / 3sg / 3pl carry most of the load.
DRILLED_PERSONS = [0, 2, 5]

VOCABULARY = [
    ("the government", "el gobierno"), ("the war", "la guerra"),
    ("the border", "la frontera"), ("the agreement", "el acuerdo"),
    ("the news", "las noticias"), ("the price", "el precio"),
    ("the meeting", "la reunión"), ("the law", "la ley"),
    ("to grow", "crecer"), ("to owe / ought", "deber"),
    ("to bring", "traer"), ("to leave", "salir"),
    ("to put", "poner"), ("to know (a fact)", "saber"),
    ("to know (a person)", "conocer"), ("to want", "querer"),
    ("tomorrow", "mañana"), ("yesterday", "ayer"),
    ("now", "ahora"), ("always", "siempre"),
    ("never", "nunca"), ("although", "aunque"),
    ("besides", "además"), ("therefore", "por lo tanto"),
    ("however", "sin embargo"), ("while", "mientras"),
    ("enough", "bastante"), ("almost", "casi"),
]

CLOZE = [
    ("Ayer ____ (ir) al mercado.", "fui", "preterite of ir, 1sg"),
    ("Cuando era niño, ____ (vivir) en Tucson.", "vivía", "imperfect, habit"),
    ("Mañana ____ (hablar) con el jefe.", "hablaré", "future, 1sg"),
    ("Ellos ____ (tener) que salir temprano.", "tienen", "present of tener"),
    ("Nosotros no ____ (poder) esperar más.", "podemos", "present of poder"),
    ("¿Qué ____ (decir) el presidente?", "dijo", "preterite of decir, 3sg"),
    ("El acuerdo ____ (ser) firmado el lunes.", "fue", "preterite of ser, 3sg"),
    ("Siempre ____ (hacer) lo mismo.", "hace", "present of hacer, 3sg"),
    ("Yo ____ (estar) leyendo cuando llamó.", "estaba", "imperfect, was-doing"),
    ("Hace dos años que ____ (trabajar) aquí.", "trabajo", "present, duration"),
    ("No ____ (ver) la noticia hasta ayer.", "vi", "preterite of ver, 1sg"),
]

GRAMMAR_NOTES = [
    ("ser vs estar?",
     "ser = identity, essence, origin. estar = state, location, was-doing."),
    ("preterite vs imperfect?",
     "preterite = completed event. imperfect = habit, background, was-doing."),
    ("future of any regular verb?",
     "infinitive + e as a emos eis an (accent on all but nosotros)"),
    ("which verbs are irregular in the imperfect?",
     "only ser (era), ir (iba), ver (veia)"),
]


def spanish_cards():
    cards = []

    def add(prompt, answer, tag):
        cards.append({"id": f"sp-{len(cards) + 1:04d}", "prompt": prompt,
                      "answer": answer, "tag": tag})

    for verb, gloss in REGULAR_VERBS:
        stem, group = verb[:-2], verb[-2:]
        for tense, by_group in REGULAR_ENDINGS.items():
            for person in DRILLED_PERSONS:
                add(f"{verb} ({gloss}) - {tense}, {PRONOUNS[person]}",
                    stem + by_group[group][person], f"regular -{group} {tense}")
        for person in DRILLED_PERSONS:
            add(f"{verb} ({gloss}) - future, {PRONOUNS[person]}",
                verb + FUTURE_ENDINGS[person], f"regular -{group} future")

    for verb, forms in IRREGULAR_VERBS.items():
        for tense in ("present", "preterite", "imperfect", "future"):
            for person in DRILLED_PERSONS:
                add(f"{verb} ({forms['gloss']}) - {tense}, {PRONOUNS[person]}",
                    forms[tense][person], f"irregular {tense}")

    for english, spanish in VOCABULARY:
        add(f"in Spanish: {english}", spanish, "vocabulary")
    for sentence, answer, tag in CLOZE:
        add(sentence, answer, f"cloze - {tag}")
    for question, answer in GRAMMAR_NOTES:
        add(question, answer, "grammar")
    # Cards are generated verb by verb, so in deck order the first week would
    # be nothing but hablar. Shuffle with a fixed seed: new cards come out
    # interleaved across verbs and tenses, but the order is reproducible.
    random.Random(0).shuffle(cards)
    return cards


#############################################################################
################################### GREGG ###################################

# Common English words. Any word missing from the dictionary is reported and
# skipped rather than guessed at. Order here does not matter - the cards are
# sorted by outline length afterwards so short outlines come up first.
GREGG_WORDS = """
    day go he she we me my by see say so no know now new man men can come
    give get good great made make may more most much must name need note
    part play read room same send show sit stand take talk tell time told
    took under until upon want week well went were what when where which
    while will wish word work world write year young able about above
    after again against almost along already also always among answer
    appear around aside asked avoid became because become before began
    begin being believe better between both bring broken brought build
    business call called carry case cause certain change charge check
    child choice church city class clear close committee company complete
    concern consider continue cost country course court cover
    decide demand desire detail develop difference direct discuss doubt
    during early effect either enough enter equal even event ever every
    example expect experience explain express
    fact family favor field figure fill final find first follow force
    form found four free full further future
    general glad government group grow hand happen hard heard help high
    history hold home hope hour house however
    idea important increase indeed industry inform interest issue
    keep kind labor land large last late lead learn least leave less
    letter level life light like line little live local long look
    market matter mean measure meet member mention method mind minute
    money month morning move
    nation nature near necessary next night north nothing notice number
    object offer office often open opinion order other over own
    page paper party pass past pay people perhaps period person place
    plan please point position possible power prepare present press
    price private probably problem produce program progress proper
    public purpose
    question quite rather reach real reason receive record refer regard
    remain remember report request result return right rise river road
    round rule
    school season second section seem sell sense serve service set
    several short should side sign simple since single small social
    some soon sorry sound south special speak spend spirit start state
    still stock stop street strong study subject such suggest supply
    support suppose sure system
    table term test thank think third though thought through today
    together toward town trade train true trust turn type
    union unit use usual value various view visit voice vote
    wait walk watch water weather west whether white whole
    whose wide wife window winter within without woman wonder
    wood wrong
"""


def gregg_cards():
    import grascii
    dictionary_dir = pathlib.Path(grascii.__file__).parent / "dictionary" / "preanniversary"
    if not dictionary_dir.is_dir():
        raise SystemExit(f"grascii dictionary not found at {dictionary_dir}")

    # English word -> shortest plain-notation outline for it.
    outlines = {}
    for source in sorted(dictionary_dir.iterdir()):
        if not source.is_file():
            continue
        for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
            parts = line.split(" ", 1)
            if len(parts) != 2:
                continue
            notation, english = parts[0], parts[1].strip().lower()
            # Plain A-Z notation, plus ' for the H sound - too common to drop
            # (hand, help, house, hope). The remaining Grascii symbols mark
            # advanced distinctions a starter deck should not quiz: ~ reversed
            # circle vowel, | looped, ^ disjoined or above the line, _ a W
            # before the vowel, & compound vowels, () directionality.
            if not re.fullmatch(r"[A-Z']+", notation) or " " in english:
                continue
            if english not in outlines or len(notation) < len(outlines[english]):
                outlines[english] = notation

    cards, missing = [], []
    for word in GREGG_WORDS.split():
        notation = outlines.get(word)
        if notation is None:
            missing.append(word)
            continue
        cards.append({"id": "", "prompt": word, "answer": notation,
                      "tag": f"{len(notation.replace(chr(39), ''))} strokes"})
    cards.sort(key=lambda card: (len(card["answer"]), card["prompt"]))
    for index, card in enumerate(cards, 1):
        card["id"] = f"gg-{index:04d}"
    if missing:
        print(f"not in dictionary, skipped ({len(missing)}): {' '.join(missing)}")
    return cards


if __name__ == "__main__":
    deck = {
        # Printed under the Gregg answers so the notation is readable.
        "gregg_legend": "' = H sound; outlines are phonetic, not spelled",
        # Spanish practice removed from the slip. The tables and
        # spanish_cards() above are left intact - uncomment to bring it back.
        # "spanish": spanish_cards(),
        "gregg": gregg_cards(),
    }
    DECK_PATH.write_text(
        json.dumps(deck, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"wrote {DECK_PATH.name}: "
          + ", ".join(f"{len(cards)} {name}" for name, cards in deck.items()
                        if isinstance(cards, list)))
