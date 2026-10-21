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
    "TYPE": "Are the values categories, measured quantities or separate permitted steps?",
    "GRAPH": "What must the display show: categories, intervals, proportions or quartiles?",
    "CENTER": "Which center is least affected by the unusually large observation?",
    "CONSTRUCT": "Does the sum divided by five equal the requested mean?",
    "QUARTILES": "Where are the medians of the two halves, not their endpoints?",
    "ORDINARY": "Where does the left whisker of an ordinary plot end?",
    "MODIFIED": "What is the largest observed value inside the upper fence?",
    "COMPARE": "Compare Q3 minus Q1 for each group, not the full ranges.",
}
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
    return dict(minimum=str(lo), q1=str(q1), median=str(q2), q3=str(q3),
                maximum=str(hi), iqr=str(iqr), lower_fence=str(lower),
                upper_fence=str(upper),
                left_whisker=str(min(inside) if modified else lo),
                right_whisker=str(max(inside) if modified else hi),
                outliers=sorted(v for v in values if v < lower or v > upper) if modified else [])


def generate(family, seed, mode, *, transfer=False):
    """Return separate public problem and private teacher oracle, never persisted."""
    if family not in FAMILIES or type(seed) is not int or seed < 0 or mode not in MODES or type(transfer) is not bool:
        raise ValueError("invalid draft request")
    rng = random.Random(f"mihur:svd-r1:{family}:{mode}:{seed}:{transfer}")
    if family == "DATA_TYPE":
        cases = [
            ("distance measured at arbitrary precision", "CONTINUOUS", "DISCRETE"),
            ("price allowed only in 0.25-unit steps", "DISCRETE", "CONTINUOUS"),
            ("preferred route name", "CATEGORICAL", "CONTINUOUS"),
            ("number of bicycle repairs", "DISCRETE", "CONTINUOUS"),
        ]
        context, result, wrong = rng.choice(cases)
        prompt = f"Classify {context}: CATEGORICAL, DISCRETE or CONTINUOUS."
        answer = {"classification": result}
        error = {"classification": wrong}
    elif family == "GRAPH_CHOICE":
        cases = [
            ("counts across named categories", "BAR", "HISTOGRAM"),
            ("numerical measurements grouped in adjacent intervals", "HISTOGRAM", "BAR"),
            ("median and IQR for two groups", "BOXPLOT", "BAR"),
            ("mutually exclusive categories partitioning one whole", "CIRCLE", "HISTOGRAM"),
        ]
        purpose, result, wrong = rng.choice(cases)
        prompt = f"Choose BAR, HISTOGRAM, BOXPLOT or CIRCLE to display {purpose}."
        answer = {"graph": result}
        error = {"graph": wrong}
    elif family == "CENTER_CHOICE":
        start = rng.randint(8, 24)
        values = [start + 2 * i for i in range(5)] + [start + rng.randint(58, 81)]
        rng.shuffle(values)
        prompt = f"Service times in minutes: {values}. Find mean, median, mode, range and resistant typical center."
        answer = dict(mean=str(Fraction(sum(values), 6)), median=str(median(values)),
                      mode="NONE", range=str(max(values) - min(values)), center="MEDIAN")
        error = dict(answer, center="MEAN")
    elif family == "CONSTRUCT_SET":
        m, d = rng.randint(12, 29), rng.randint(2, 8)
        prompt = f"Construct ANY five nonnegative integers with mean {m}, median {m}, unique mode {m} and range {2*d}."
        answer = {"values": [m-d, m, m, m, m+d]}
        error = {"values": [m-d, m, m, m, m+d+1]}
    elif family in ("QUARTILES", "ORDINARY_BOX"):
        values = sorted(rng.sample(range(4, 67), rng.choice((9, 10, 11, 12))))
        e = box(values)
        keys = ("q1", "median", "q3", "iqr") if family == "QUARTILES" else (
            "minimum", "q1", "median", "q3", "maximum", "left_whisker", "right_whisker")
        answer = {k: e[k] for k in keys}
        error = dict(answer)
        if family == "QUARTILES":
            error.update(q1=e["minimum"], q3=e["maximum"])
        else:
            error["left_whisker"] = e["q1"]
        prompt = (f"Data: {values}. Give {'quartiles and IQR' if family == 'QUARTILES' else 'ORDINARY min-to-max box-plot landmarks'}. "
                  "Use median-of-halves, excluding the overall median for odd n.")
    elif family == "MODIFIED_BOX":
        start = rng.randint(8, 28)
        values = [start + v for v in rng.sample(range(17), 10)] + [start + rng.randint(72, 90)]
        rng.shuffle(values)
        e = box(values, True)
        keys = ("q1", "median", "q3", "iqr", "lower_fence", "upper_fence",
                "left_whisker", "right_whisker", "outliers")
        answer = {k: e[k] for k in keys}
        error = dict(answer, right_whisker=e["maximum"])
        prompt = (f"Data: {values}. Give quartiles, IQR, 1.5×IQR fences, "
                  "non-outlier whiskers and outlier dots for a MODIFIED box plot.")
    else:
        center = rng.randint(30, 55)
        sa, sb = rng.sample((1, 2, 3, 4), 2)
        a = [center + sa*i for i in range(-4, 5)]
        b = [center + sb*i for i in range(-4, 5)]
        rng.shuffle(a)
        rng.shuffle(b)
        ai, bi = exact(box(a)["iqr"]), exact(box(b)["iqr"])
        answer = dict(median_a=str(median(a)), median_b=str(median(b)),
                      iqr_a=str(ai), iqr_b=str(bi),
                      wider="A" if ai > bi else "B")
        error = dict(answer, wider="B" if ai > bi else "A")
        prompt = f"Group A: {a}; Group B: {b}. Compare medians and IQRs. Which has wider middle 50%?"
    if transfer:
        prompt += " Explain your reasoning using a different representation."
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
    return {"public": public, "private": {"answer": answer, "wrong_signature": error},
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
        original = expected["values"]
        m, d = original[2], original[-1] - original[2]
        counts = Counter(values)
        top = max(counts.values())
        return (Fraction(sum(values), 5) == m and median(values) == m
                and [k for k, n in counts.items() if n == top] == [m]
                and top >= 2 and max(values) - min(values) == 2*d)
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
        if candidate["public"]["prompt"] != source["public"]["prompt"] and candidate["private"] != source["private"]:
            return candidate
    raise ValueError("fresh transfer unavailable")
