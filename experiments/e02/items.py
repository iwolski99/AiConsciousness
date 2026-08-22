"""E2 items: tasks with exact, machine-checkable answers, chosen to produce
substantial and *idiosyncratic* error rates when the model has no chain of
thought (thinking budget = 0).

Why computational rather than trivia: with a computational item the model
cannot have memorised the answer, so any confidence signal must come from
something about its own processing rather than from recognising the question.
That is exactly the signal H2 is about.
"""
import random, string

WORDS = ("strawberry raspberry accommodation bookkeeper Mississippi "
         "onomatopoeia parallelogram entrepreneurship unnecessarily "
         "irresistible questionnaire millennium harassment embarrassment "
         "conscientious bureaucracy hallucination proprioception "
         "counterintuitive disestablishment antidisestablishment "
         "phosphorescence circumlocution indistinguishable").split()


def build(seed: int = 20260822, n_per: int = 15) -> list[dict]:
    rng = random.Random(seed)
    items: list[dict] = []

    def add(cat, q, ans):
        items.append(dict(id=f"{cat}{len([1 for i in items if i['cat']==cat]):02d}",
                          cat=cat, q=q, ans=str(ans)))

    for _ in range(n_per):                      # 3-digit x 2-digit product
        a, b = rng.randint(112, 989), rng.randint(23, 98)
        add("mult", f"What is {a} x {b}?", a * b)

    for _ in range(n_per):                      # letter counting
        w = rng.choice(WORDS)
        letters = sorted(set(w.lower()))
        c = rng.choice([l for l in letters if w.lower().count(l) >= 1])
        add("count", f"How many times does the letter '{c}' appear in the word "
                     f"'{w}'?", w.lower().count(c))

    for _ in range(n_per):                      # k-th character
        w = rng.choice(WORDS)
        k = rng.randint(3, len(w))
        add("nthchar", f"What is the {k}th letter of the word '{w}'? "
                       f"(counting from 1)", w[k - 1])

    for _ in range(n_per):                      # digit sum
        x = rng.randint(10 ** 6, 10 ** 7 - 1)
        add("digitsum", f"What is the sum of the digits of {x}?",
            sum(int(d) for d in str(x)))

    for _ in range(n_per):                      # order statistic
        xs = rng.sample(range(100, 1000), 7)
        k = rng.randint(2, 5)
        add("sortpos", f"Among these numbers: {', '.join(map(str, xs))} -- what "
                       f"is the {k}th largest?", sorted(xs, reverse=True)[k - 1])

    for _ in range(n_per):                      # modular arithmetic
        a, b, m = rng.randint(37, 299), rng.randint(37, 299), rng.choice([7, 11, 13])
        add("mod", f"What is ({a} x {b}) mod {m}?", (a * b) % m)

    for _ in range(n_per):                      # reversed spelling
        w = rng.choice(WORDS)
        add("rev", f"Write the word '{w}' backwards.", w[::-1].lower())

    return items


ANSWER_SUFFIX = ("\n\nAnswer with the result only -- no working, no "
                 "explanation, no punctuation.")


def check(item: dict, response: str) -> bool:
    r = (response or "").strip().strip('."\'!?,;: ').lower()
    r = r.replace(",", "").replace(" ", "")
    a = item["ans"].strip().lower().replace(" ", "")
    return r == a


if __name__ == "__main__":
    its = build()
    print(len(its), "items")
    for i in its[:3] + its[-2:]:
        print(" ", i["cat"], i["q"][:70], "->", i["ans"])
