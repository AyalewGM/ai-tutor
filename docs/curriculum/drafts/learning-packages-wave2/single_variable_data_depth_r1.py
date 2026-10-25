"""Original draft-only one-variable data question families; no runtime or mastery authority."""
from __future__ import annotations

import random
import re
from collections import Counter
from fractions import Fraction

STATUS = "DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION = False
QUARTILE_METHOD = "MEDIAN_OF_HALVES_EXCLUDE_ODD_MIDDLE"
MODES = ("diagnostic", "guided", "independent", "mastery")
FAMILIES = ("DATA_TYPE", "GRAPH_CHOICE", "CENTER_CHOICE", "CONSTRUCT_SET",
            "QUARTILES", "ORDINARY_BOX", "MODIFIED_BOX", "COMPARE_BOXES")
SOCRATIC = {
    "DATA_TYPE": "Are the values categories, measured quantities or separate permitted steps?",
    "GRAPH_CHOICE": "What must the display show: categories, intervals, proportions or quartiles?",
    "CENTER_CHOICE": "Which center is least affected by the unusually extreme observation?",
    "CONSTRUCT_SET": "Does the sum divided by five equal the requested mean?",
    "QUARTILES": "Where are the medians of the two halves, not their endpoints?",
    "ORDINARY_BOX": "Where does the left whisker of an ordinary plot end?",
    "MODIFIED_BOX": "Which observed value is the most extreme one still inside the fence on the outlier's side?",
    "COMPARE_BOXES": "Compare Q3 minus Q1 for each group, not the full ranges.",
}
DATA_TYPE_CATEGORIES = (
    ("favourite lunch option", ("soup", "salad", "wrap", "pasta", "rice bowl")),
    ("preferred route to school", ("north path", "river trail", "main road", "bus loop")),
    ("primary phone brand", ("brand A", "brand B", "brand C", "brand D", "brand E")),
    ("club joined", ("chess", "robotics", "drama", "choir", "debate")),
    ("eye colour", ("brown", "blue", "green", "hazel", "grey")),
    ("transport mode", ("walk", "bike", "bus", "car", "train")),
)
DATA_TYPE_CODES = ("jersey number", "locker number", "postal zone code", "bus route number")
DATA_TYPE_COUNTS = ("number of bicycle repairs this month", "number of siblings",
                    "number of books borrowed this term", "number of goals scored per game",
                    "number of messages received today")
DATA_TYPE_STEPPED = ("shoe size", "ticket price in dollars", "parking fee in dollars",
                     "quiz score with partial credit")
DATA_TYPE_MEASURED = (("commute distance", "km"), ("plant height", "cm"),
                      ("reaction time", "s"), ("backpack mass", "kg"),
                      ("water temperature", "°C"))
DATA_TYPE_GROUPS = ("Class A", "Class B", "the morning shift", "the evening shift",
                    "Team North", "Team South")
NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:[.][0-9]+)?|[0-9]+/[1-9][0-9]*)$")


def exact(value):
    if type(value) is bool or not isinstance(value, (str, int, Fraction)):
        raise ValueError("exact rational required, no float")
    if isinstance(value, str):
        value = value.strip()
        if not NUMBER.fullmatch(value):
            raise ValueError("invalid rational")
    return Fraction(value)


def median(values):
    s = sorted(values)
    if not s:
        raise ValueError("empty data")
    n = len(s)
    return Fraction(s[n // 2]) if n % 2 else Fraction(s[n // 2 - 1] + s[n // 2], 2)


def five_number(values):
    if len(values) < 5:
        raise ValueError("at least five observations")
    s = sorted(values)
    h = len(s) // 2
    return Fraction(s[0]), median(s[:h]), median(s), median(s[-h:]), Fraction(s[-1])


def box(values, modified=False):
    lo, q1, q2, q3, hi = five_number(values)
    iqr = q3 - q1
    lower, upper = q1 - Fraction(3, 2) * iqr, q3 + Fraction(3, 2) * iqr
    inside = [v for v in values if lower <= v <= upper]
    if not inside:
        raise ValueError("no non-outlier values")
    return {"minimum": str(lo), "q1": str(q1), "median": str(q2), "q3": str(q3),
            "maximum": str(hi), "iqr": str(iqr), "lower_fence": str(lower),
            "upper_fence": str(upper),
            "left_whisker": str(min(inside) if modified else lo),
            "right_whisker": str(max(inside) if modified else hi),
            "outliers": sorted(v for v in values if v < lower or v > upper) if modified else []}


def generate(family, seed, mode, *, transfer=False):
    """Return separate public problem and private teacher oracle, never persisted."""
    if family not in FAMILIES or type(seed) is not int or seed < 0 or mode not in MODES or type(transfer) is not bool:
        raise ValueError("invalid draft request")
    rng = random.Random(f"mihur:svd-r1:{family}:{mode}:{seed}:{transfer}")
    if family == "DATA_TYPE":
        kind = rng.choice(("CATEGORICAL", "CATEGORICAL_CODED", "COUNT", "STEPPED", "MEASURED"))
        n = rng.randint(5, 7)
        if kind == "CATEGORICAL":
            variable, labels = rng.choice(DATA_TYPE_CATEGORIES)
            observations = [rng.choice(labels) for _ in range(n)]
            result, wrong = "CATEGORICAL", "DISCRETE"
        elif kind == "CATEGORICAL_CODED":
            variable = rng.choice(DATA_TYPE_CODES)
            observations = [str(v) for v in rng.sample(range(10, 100), n)]
            result, wrong = "CATEGORICAL", "DISCRETE"
        elif kind == "COUNT":
            variable = rng.choice(DATA_TYPE_COUNTS)
            observations = [str(rng.randint(0, 30)) for _ in range(n)]
            result, wrong = "DISCRETE", "CONTINUOUS"
        elif kind == "STEPPED":
            variable = rng.choice(DATA_TYPE_STEPPED)
            step = rng.choice((Fraction(1, 4), Fraction(1, 2), Fraction(1, 5)))
            observations = [f"{float(step * rng.randint(4, 60)):g}" for _ in range(n)]
            variable = f"{variable}, which can only take values in steps of {float(step):g}"
            result, wrong = "DISCRETE", "CONTINUOUS"
        else:
            variable, unit = rng.choice(DATA_TYPE_MEASURED)
            observations = [f"{rng.randint(100, 999) / 10:.1f} {unit}" for _ in range(n)]
            variable = f"{variable}, recorded to the nearest 0.1 {unit}"
            result, wrong = "CONTINUOUS", "DISCRETE"
        prompt = (f"A survey records {variable}. Sample: {', '.join(observations)}. "
                  "Classify the variable: CATEGORICAL, DISCRETE or CONTINUOUS.")
        answer = {"classification": result}
        error = {"classification": wrong}
        structure = kind
    elif family == "GRAPH_CHOICE":
        result = rng.choice(("BAR", "HISTOGRAM", "BOXPLOT", "CIRCLE"))
        if result in ("BAR", "CIRCLE"):
            variable, labels = rng.choice(DATA_TYPE_CATEGORIES)
            chosen = rng.sample(labels, rng.randint(3, min(5, len(labels))))
            counts = {label: rng.randint(2, 40) for label in chosen}
            table = ", ".join(f"{k}: {v}" for k, v in counts.items())
            if result == "BAR":
                purpose = f"Counts of {variable} ({table}). Goal: compare the counts across categories."
                wrong = "HISTOGRAM"
            else:
                purpose = (f"Counts of {variable} ({table}, total {sum(counts.values())}). "
                           "Goal: show each category's share of the whole.")
                wrong = "HISTOGRAM"
        else:
            variable, unit = rng.choice(DATA_TYPE_MEASURED)
            if result == "HISTOGRAM":
                width = rng.choice((5, 10, 20))
                values = [rng.randint(10, 99) for _ in range(rng.randint(18, 30))]
                purpose = (f"{len(values)} values of {variable} in {unit}, from {min(values)} to {max(values)}. "
                           f"Goal: show the shape of the distribution in intervals of width {width}.")
                wrong = "BAR"
            else:
                a, b = rng.sample(DATA_TYPE_GROUPS, 2)
                purpose = (f"{variable} in {unit} measured for {rng.randint(12, 40)} cases in {a} "
                           f"and {rng.randint(12, 40)} in {b}. "
                           "Goal: compare the medians and middle-50% spreads of the two groups.")
                wrong = "BAR"
        prompt = f"{purpose} Choose BAR, HISTOGRAM, BOXPLOT or CIRCLE."
        answer = {"graph": result}
        error = {"graph": wrong}
        structure = result
    elif family == "CENTER_CHOICE":
        side, repeat = rng.choice(("HIGH", "LOW")), rng.choice((False, True))
        start = rng.randint(8, 24) if side == "HIGH" else rng.randint(70, 90)
        values = [start + 2 * i for i in range(5)]
        if repeat:
            values[3] = values[2]
        values.append(start + rng.randint(58, 81) if side == "HIGH" else start - rng.randint(55, 65))
        structure = f"{side}_EXTREME_{'REPEATED_VALUE' if repeat else 'NO_REPEAT'}"
        rng.shuffle(values)
        prompt = (f"Service times in minutes: {values}. Find mean, median, mode (NONE if no value repeats), "
                  "range and resistant typical center.")
        answer = {"mean": str(Fraction(sum(values), 6)), "median": str(median(values)),
                  "mode": str(start + 4) if repeat else "NONE",
                  "range": str(max(values) - min(values)), "center": "MEDIAN"}
        error = dict(answer, center="MEAN")
    elif family == "CONSTRUCT_SET":
        m = rng.randint(16, 29)
        structure = rng.choice(("MEAN_EQUALS_MEDIAN", "MEAN_ABOVE_MEDIAN", "MEAN_BELOW_MEDIAN"))
        if structure == "MEAN_EQUALS_MEDIAN":
            d = rng.randint(2, 8)
            values, mean = [m - d, m, m, m, m + d], m
        else:
            t = rng.randint(1, 3)
            k2 = rng.randint((5 * t + 1) // 2 + 1, 5 * t)
            values, mean = [m - 1, m, m, m + 5 * t + 1 - k2, m + k2], m + t
            if structure == "MEAN_BELOW_MEDIAN":
                values, mean = [2 * m - v for v in reversed(values)], m - t
        spread = max(values) - min(values)
        constraints = {"mean": str(mean), "median": str(m), "mode": str(m), "range": str(spread)}
        prompt = (f"Construct ANY five nonnegative integers with mean {mean}, median {m}, "
                  f"unique mode {m} and range {spread}.")
        answer = {"values": values}
        error = {"values": values[:-1] + [values[-1] + 1]}
    elif family in ("QUARTILES", "ORDINARY_BOX"):
        layout = rng.choice(("LIST", "FREQUENCY_TABLE"))
        n = rng.choice((9, 10, 11, 12))
        while True:
            values = sorted(rng.sample(range(4, 67), n) if layout == "LIST" else rng.choices(range(4, 30), k=n))
            e = box(values)
            if (e["q1"] != e["minimum"] and e["q3"] != e["maximum"]
                    and (layout == "LIST" or max(Counter(values).values()) >= 2)):
                break
        structure = f"{layout}_{'ODD' if n % 2 else 'EVEN'}_N"
        data = str(values) if layout == "LIST" else "frequency table (value: count) " + ", ".join(
            f"{v}: {c}" for v, c in sorted(Counter(values).items()))
        keys = ("q1", "median", "q3", "iqr") if family == "QUARTILES" else (
            "minimum", "q1", "median", "q3", "maximum", "left_whisker", "right_whisker")
        answer = {k: e[k] for k in keys}
        error = dict(answer)
        if family == "QUARTILES":
            error.update(q1=e["minimum"], q3=e["maximum"])
        else:
            error["left_whisker"] = e["q1"]
        prompt = (f"Data: {data}. Give {'quartiles and IQR' if family == 'QUARTILES' else 'ORDINARY min-to-max box-plot landmarks'}. "
                  "Use median-of-halves, excluding the overall median for odd n.")
    elif family == "MODIFIED_BOX":
        side = rng.choice(("HIGH", "LOW"))
        start = rng.randint(8, 28) if side == "HIGH" else rng.randint(80, 100)
        values = [start + v for v in rng.sample(range(17), 10)]
        values.append(start + rng.randint(72, 90) if side == "HIGH" else start - rng.randint(72, 79))
        rng.shuffle(values)
        structure = f"{side}_OUTLIER"
        e = box(values, True)
        keys = ("q1", "median", "q3", "iqr", "lower_fence", "upper_fence",
                "left_whisker", "right_whisker", "outliers")
        answer = {k: e[k] for k in keys}
        error = (dict(answer, right_whisker=e["maximum"]) if side == "HIGH"
                 else dict(answer, left_whisker=e["minimum"]))
        prompt = (f"Data: {values}. Give quartiles, IQR, 1.5×IQR fences, "
                  "non-outlier whiskers and outlier dots for a MODIFIED box plot. "
                  "Use median-of-halves, excluding the overall median for odd n.")
    else:
        center = rng.randint(30, 55)
        sa, sb = rng.sample((1, 2, 3, 4), 2)
        a = [center + sa*i for i in range(-4, 5)]
        b = [center + sb*i for i in range(-4, 5)]
        rng.shuffle(a)
        rng.shuffle(b)
        ai, bi = exact(box(a)["iqr"]), exact(box(b)["iqr"])
        answer = {"median_a": str(median(a)), "median_b": str(median(b)),
                  "iqr_a": str(ai), "iqr_b": str(bi),
                  "wider": "A" if ai > bi else "B"}
        error = dict(answer, wider="B" if ai > bi else "A")
        structure = rng.choice(("RAW_BOTH", "RAW_AND_SUMMARY"))
        if structure == "RAW_BOTH":
            groups = f"Group A: {a}; Group B: {b}."
        else:
            eb = box(b)
            groups = (f"Group A raw data: {a}; Group B five-number summary: min {eb['minimum']}, "
                      f"Q1 {eb['q1']}, median {eb['median']}, Q3 {eb['q3']}, max {eb['maximum']}.")
        prompt = (f"{groups} Compare medians and IQRs. Which has wider middle 50%? "
                  "Use median-of-halves, excluding the overall median for odd n.")
    public = {
        "status": STATUS, "runtime_activation": False, "mastery_credit": False,
        "family": family, "mode": mode, "prompt": prompt,
        "response_fields": list(answer),
        "representation_progression": ["CONCRETE", "VISUAL", "SYMBOLIC"],
        "support_prompts": [],
        "accessibility": {"keyboard": "Structured inputs, no dragging required",
                          "screen_reader": "Ordered observations, units, axes and landmarks",
                          "text_equivalent": "Sorted table and plot landmarks",
                          "focus": "Preserve work and focus on invalid field",
                          "reduced_motion": "Static state and announcements",
                          "non_colour": "Labels and patterns"},
    }
    private = {"answer": answer, "wrong_signature": error, "structure": structure}
    if family == "CONSTRUCT_SET":
        private["constraints"] = constraints
    return {"public": public, "private": private,
            "seed": seed, "family": family, "mode": mode}


def review_equivalent(item, response):
    """Author-only oracle, not trusted server scoring."""
    if not isinstance(response, dict):
        return False
    expected = item["private"]["answer"]
    if set(response) != set(expected):
        return False
    if item["family"] == "CONSTRUCT_SET":
        values = response["values"]
        if not isinstance(values, list) or len(values) != 5 or any(type(v) is not int or v < 0 for v in values):
            return False
        c = item["private"]["constraints"]
        counts = Counter(values)
        top = max(counts.values())
        return (Fraction(sum(values), 5) == exact(c["mean"]) and median(values) == exact(c["median"])
                and [k for k, n in counts.items() if n == top] == [int(c["mode"])]
                and top >= 2 and max(values) - min(values) == int(c["range"]))
    for key, target in expected.items():
        value = response[key]
        if isinstance(target, list):
            if not isinstance(value, list) or len(value) != len(target):
                return False
            try:
                if sorted(exact(v) for v in value) != sorted(exact(v) for v in target):
                    return False
            except ValueError:
                return False
        elif key in ("classification", "graph", "mode", "center", "wider"):
            if not isinstance(value, str) or value.strip().upper() != target:
                return False
        else:
            try:
                if exact(value) != exact(target):
                    return False
            except ValueError:
                return False
    return True


def guided_response(item, observed):
    if item["mode"] != "guided" or not isinstance(observed, dict):
        return None
    if set(observed) != set(item["private"]["answer"]):
        return None
    if review_equivalent(item, observed):
        return {"classification": "CORRECT_NO_REPAIR", "questions": [], "mastery_credit": False}
    signature = item["private"]["wrong_signature"]
    if item["family"] == "CONSTRUCT_SET":
        matches = observed == signature
    else:
        probe = dict(item, private=dict(item["private"], answer=signature))
        matches = review_equivalent(probe, observed)
    code = item["family"] if matches else "AMBIGUOUS_OR_UNCLASSIFIED"
    return {"classification": code, "questions": [SOCRATIC[code] if matches else
            "Which values and definitions did you use? Show your reasoning."], "mastery_credit": False}


def independent_transfer(source, seed):
    if source["mode"] not in ("guided", "diagnostic") or type(seed) is not int or seed < 0:
        raise ValueError("invalid transfer source")
    for offset in range(64):
        candidate = generate(source["family"], seed + 1_000_003 + offset,
                             "independent", transfer=True)
        if (candidate["public"]["prompt"] != source["public"]["prompt"]
                and candidate["private"] != source["private"]
                and candidate["private"]["structure"] != source["private"]["structure"]):
            return candidate
    raise ValueError("fresh transfer unavailable")
