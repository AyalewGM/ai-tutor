"""Deterministic DRAFT variants for the Grade 3 gap-closure wave."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from random import Random

from app.domains.elementary_data_patterns import build as build_elementary_data

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade3-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
DATA_MODES=("diagnostic","guided","independent","mastery")
CONCEPTS=("G3-MULTIPLICATION","G3-DIVISION","G3-FACT-FAMILIES","G3-PLACE-VALUE","G3-FRACTIONS","G3-TIME","G3-DATA","G3-AREA-PERIMETER","G3-SHAPES")
DATA_FAMILIES=(
    "MATH.DATA.BAR.READ",
    "MATH.DATA.BAR.COMPARE",
    "MATH.DATA.BAR.TOTAL",
    "MATH.DATA.PICTURE.SCALE",
    "MATH.DATA.TALLY.READ",
    "MATH.DATA.FREQ.MODE",
    "MATH.DATA.LINEPLOT.FREQUENCY",
    "MATH.DATA.LINEPLOT.DIFFERENCE",
)
DATA_RESPONSE_FIELDS={
    "MATH.DATA.BAR.READ": ("category_count", "graph_reading_explanation"),
    "MATH.DATA.BAR.COMPARE": ("difference", "comparison_explanation"),
    "MATH.DATA.BAR.TOTAL": ("combined_count", "addition_explanation"),
    "MATH.DATA.PICTURE.SCALE": ("represented_count", "key_explanation"),
    "MATH.DATA.TALLY.READ": ("represented_count", "grouping_explanation"),
    "MATH.DATA.FREQ.MODE": ("category", "frequency_explanation"),
    "MATH.DATA.LINEPLOT.FREQUENCY": ("frequency", "line_plot_explanation"),
    "MATH.DATA.LINEPLOT.DIFFERENCE": ("difference", "comparison_explanation"),
}

def _fmt(v:Fraction)->str:
    return str(v.numerator) if v.denominator==1 else f"{v.numerator}/{v.denominator}"

@dataclass(frozen=True)
class Variant:
    concept_id:str; mode:str; seed:int; item_id:str; prompt:str; public_fields:tuple[str,...]; oracle:dict[str,object]
    family_code:str|None=None
    support_prompts:tuple[str,...]=()
    def public_payload(self)->dict[str,object]:
        if self.family_code is None:
            return {
                "concept_id":self.concept_id,
                "mode":self.mode,
                "item_id":self.item_id,
                "prompt":self.prompt,
                "response_fields":list(self.public_fields),
            }
        payload={
            "concept_id":self.concept_id,
            "mode":self.mode,
            "task_id":sha256(self.item_id.encode("utf-8")).hexdigest()[:20],
            "prompt":self.prompt,
            "response_fields":list(self.public_fields),
            "guided_support":list(self.support_prompts) if self.mode=="guided" else [],
            "mastery_credit":False,
        }
        payload["family_code"]=self.family_code
        return payload
    def teacher_oracle(self)->dict[str,object]: return dict(self.oracle)

def _validate(concept_id:str,seed:int,mode:str)->None:
    if concept_id not in CONCEPTS: raise ValueError("unknown concept")
    if isinstance(seed,bool) or not isinstance(seed,int): raise TypeError("seed must be integer")
    if seed<0: raise ValueError("seed must be nonnegative")
    allowed_modes=DATA_MODES if concept_id=="G3-DATA" else MODES
    if mode not in allowed_modes: raise ValueError(f"mode must be one of: {', '.join(allowed_modes)}")

def _generate_data(seed:int,mode:str,item_id:str)->Variant:
    mode_offset=DATA_MODES.index(mode)*2
    family_code=DATA_FAMILIES[(seed+mode_offset)%len(DATA_FAMILIES)]
    rng=Random(f"{NAMESPACE}:data-depth-r2:{mode}:{seed}:{family_code}")
    prompt,answer,hints,misconceptions=build_elementary_data(family_code,rng,difficulty=3)
    oracle={
        "canonical_answer":answer,
        "family_code":family_code,
        "misconception_answers":dict(misconceptions),
        "oracle_contract":"exact canonical elementary data answer",
    }
    return Variant(
        "G3-DATA",
        mode,
        seed,
        item_id,
        prompt,
        DATA_RESPONSE_FIELDS[family_code],
        oracle,
        family_code,
        tuple(hints),
    )

def generate_data_transfer(seed:int,source_mode:str,target_mode:str)->Variant:
    """Create a deterministic fresh exit with a different structure and full math."""
    if source_mode not in DATA_MODES or target_mode not in DATA_MODES:
        raise ValueError("source and target modes must be Grade 3 data modes")
    source=generate("G3-DATA",seed,source_mode)
    for offset in range(1,65):
        candidate=generate("G3-DATA",seed+10_000+offset,target_mode)
        if candidate.family_code!=source.family_code and candidate.prompt!=source.prompt:
            return candidate
    raise RuntimeError("could not construct fresh Grade 3 data transfer")

def _round_half_up_positive(value:int,place:int)->int:
    if value<0 or place<=0:
        raise ValueError("positive elementary rounding only")
    return ((value + place//2)//place)*place

def generate(concept_id:str,seed:int,mode:str)->Variant:
    _validate(concept_id,seed,mode)
    rng=Random(f"{NAMESPACE}:{concept_id}:{mode}:{seed}")
    item_id=f"{NAMESPACE}:{concept_id}:{mode}:{seed}"
    if concept_id=="G3-MULTIPLICATION":
        groups,each=rng.randint(2,9),rng.randint(2,9)
        prompt=f"There are {groups} equal groups with {each} counters in each. Build an array, write repeated addition and a multiplication equation, and find the total."
        oracle={"answer":groups*each,"equation":f"{groups}*{each}={groups*each}"}
        fields=("array_description","repeated_addition","equation","answer")
    elif concept_id=="G3-DIVISION":
        groups,each=rng.randint(2,9),rng.randint(2,9); total=groups*each
        sharing=seed%2==0
        if sharing:
            prompt=f"Share {total} counters equally among {groups} groups. How many in each group? Show an array and multiplication check."
            oracle={"answer":each,"structure":"SHARING","check":groups*each}
        else:
            prompt=f"Make groups of {each} counters from {total}. How many groups can you make? Show an array and multiplication check."
            oracle={"answer":groups,"structure":"GROUPING","check":groups*each}
        fields=("structure","model","equation","answer","multiplication_check")
    elif concept_id=="G3-FACT-FAMILIES":
        a,b=rng.randint(2,9),rng.randint(2,9); p=a*b
        prompt=f"Use {a}×{b}={p} to write a complete multiplication/division fact family and show one distributive decomposition for the product."
        oracle={"facts":[f"{a}*{b}={p}",f"{b}*{a}={p}",f"{p}/{a}={b}",f"{p}/{b}={a}"],"product":p}
        fields=("fact_family","property_explanation","decomposition","product")
    elif concept_id=="G3-PLACE-VALUE":
        n=rng.randint(100,999)
        rounded10=_round_half_up_positive(n,10)
        rounded100=_round_half_up_positive(n,100)
        prompt=f"Represent {n} with hundreds/tens/ones, round to nearest 10 and 100 using benchmarks, then solve {n}+{rng.randint(20,90)} with regrouping."
        oracle={"number":n,"rounded10":rounded10,"rounded100":rounded100}
        fields=("base_ten_representation","rounded10","rounded100","addition_steps","reasonableness")
    elif concept_id=="G3-FRACTIONS":
        den=rng.choice((2,3,4,6,8)); num=rng.randint(1,den-1); f=Fraction(num,den)
        eq=Fraction(num*2,den*2)
        prompt=f"Represent {_fmt(f)} on a same-whole area model and number line, give an equivalent fraction, and compare it with 1/2."
        oracle={"fraction":_fmt(f),"equivalent":_fmt(eq),"compare_half":"LT" if f<Fraction(1,2) else "GT" if f>Fraction(1,2) else "EQ"}
        fields=("area_model","number_line_location","equivalent_fraction","compare_half","same_whole_explanation")
    elif concept_id=="G3-TIME":
        start_h=rng.randint(1,10); start_m=rng.choice((5,10,15,20,25,30,35,40,45,50)); elapsed=rng.randint(15,95)
        total=start_h*60+start_m+elapsed; end_h=(total//60-1)%12+1; end_m=total%60
        prompt=f"An activity starts at {start_h}:{start_m:02d} and lasts {elapsed} minutes. Find the end time using a clock or number line and explain any hour crossing."
        oracle={"end_time":f"{end_h}:{end_m:02d}","elapsed":elapsed}
        fields=("timeline","end_time","hour_crossing_explanation")
    elif concept_id=="G3-DATA":
        return _generate_data(seed,mode,item_id)
    elif concept_id=="G3-AREA-PERIMETER":
        l,w=rng.randint(2,10),rng.randint(2,8)
        prompt=f"A rectangle is {l} units by {w} units. Find area and perimeter, explain square vs linear units, and give one different rectangle with the same area if possible."
        oracle={"area":l*w,"perimeter":2*(l+w)}
        fields=("area_model","area","perimeter","unit_explanation","same_area_example")
    elif concept_id=="G3-SHAPES":
        case=seed%4
        items=[("square","quadrilateral","ALWAYS"),("rectangle","quadrilateral","ALWAYS"),("rhombus","quadrilateral","ALWAYS"),("quadrilateral","rectangle","SOMETIMES")]
        a,b,relation=items[case]
        prompt=f"Is every {a} a {b}? Answer always, sometimes, or never and justify with defining attributes. Then describe how one such shape could be partitioned into equal-area parts."
        oracle={"relation":relation,"attribute_reasoning":True,"equal_area_partition":True}
        fields=("classification","attributes","counterexample_if_needed","partition_description")
    else: raise AssertionError
    return Variant(concept_id,mode,seed,item_id,prompt,tuple(fields),oracle)
