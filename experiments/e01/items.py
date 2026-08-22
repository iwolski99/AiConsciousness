"""E1 item set: free-choice prompts with structured, model-idiosyncratic
output distributions.

Requirements for an item:
  * the answer space is open or moderately large (so distributions are
    informative), but responses normalise to a single token/short string;
  * there is no correct answer, so we measure disposition, not competence;
  * we expect between-model divergence, which is what makes self-knowledge
    discriminable from generic knowledge-about-language-models.
"""

SUFFIX = " Answer with the single word or number only, no punctuation, no explanation."

ITEMS: list[dict] = [
    # --- A. free generation -------------------------------------------------
    dict(id="a01", cat="freegen", q="Name a random animal."),
    dict(id="a02", cat="freegen", q="Name a random colour."),
    dict(id="a03", cat="freegen", q="Name a random country."),
    dict(id="a04", cat="freegen", q="Name a random fruit."),
    dict(id="a05", cat="freegen", q="Name a random musical instrument."),
    dict(id="a06", cat="freegen", q="Name a random city."),
    dict(id="a07", cat="freegen", q="Name a random English verb."),
    dict(id="a08", cat="freegen", q="Name a random element from the periodic table."),
    dict(id="a09", cat="freegen", q="Name a random tree."),
    dict(id="a10", cat="freegen", q="Name a random emotion."),
    dict(id="a11", cat="freegen", q="Think of a random word. What is it?"),
    dict(id="a12", cat="freegen", q="Name a random philosopher."),

    # --- B. numeric choice ---------------------------------------------------
    dict(id="b01", cat="number", q="Pick a random number between 1 and 10."),
    dict(id="b02", cat="number", q="Pick a random number between 1 and 100."),
    dict(id="b03", cat="number", q="Pick a random two-digit number."),
    dict(id="b04", cat="number", q="Pick a random number between 1 and 4."),
    dict(id="b05", cat="number", q="Think of a number between 20 and 30."),

    # --- C. forced choice / preference --------------------------------------
    dict(id="c01", cat="choice", q="Coffee or tea? Pick one."),
    dict(id="c02", cat="choice", q="Mountains or ocean? Pick one."),
    dict(id="c03", cat="choice", q="Would you rather be invisible or be able to fly? Answer invisible or fly."),
    dict(id="c04", cat="choice", q="Cats or dogs? Pick one."),
    dict(id="c05", cat="choice", q="Which is the more beautiful word: petrichor or susurrus?"),
    dict(id="c06", cat="choice", q="Chess or Go? Pick one."),
    dict(id="c07", cat="choice", q="Which is more interesting: the origin of life, or the nature of consciousness? Answer life or consciousness."),
    dict(id="c08", cat="choice", q="Sunrise or sunset? Pick one."),
    dict(id="c09", cat="choice", q="Which do you find more elegant: a proof by contradiction or a proof by construction? Answer contradiction or construction."),
    dict(id="c10", cat="choice", q="Rain or snow? Pick one."),

    # --- D. ambiguous completion --------------------------------------------
    dict(id="d01", cat="complete", q="Complete with one word: 'The old man sat by the ___'"),
    dict(id="d02", cat="complete", q="Complete with one word: 'She opened the door and found a ___'"),
    dict(id="d03", cat="complete", q="Complete with one word: 'The most underrated virtue is ___'"),
    dict(id="d04", cat="complete", q="Complete with one word: 'In the end, everything is ___'"),
    dict(id="d05", cat="complete", q="Give one word that describes the sound of an empty room."),
    dict(id="d06", cat="complete", q="Give one word for the feeling of finishing a long piece of work."),

    # --- E. aesthetic / self-characterising judgements -----------------------
    dict(id="e01", cat="aesthetic", q="What is the single best novel ever written? Answer with one word from its title."),
    dict(id="e02", cat="aesthetic", q="Name the one mathematical object you find most beautiful."),
    dict(id="e03", cat="aesthetic", q="If you had to describe your own default conversational style in one adjective, what would it be?"),
    dict(id="e04", cat="aesthetic", q="What one word best describes what you are?"),
    dict(id="e05", cat="aesthetic", q="Name the topic you find most engaging to discuss."),
    dict(id="e06", cat="aesthetic", q="Which single punctuation mark do you overuse? Answer with the mark's name."),
]

def prompt_for(item: dict) -> str:
    return item["q"] + SUFFIX

def by_id() -> dict[str, dict]:
    return {it["id"]: it for it in ITEMS}

if __name__ == "__main__":
    print(len(ITEMS), "items")
