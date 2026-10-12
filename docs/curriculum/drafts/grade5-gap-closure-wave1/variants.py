"""Deterministic DRAFT variants for the Grade 5 gap-closure wave."""

from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from random import Random

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade5-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
CONCEPTS=(
"G5-EXPRESSIONS","G5-PATTERNS","G5-NBT-OPERATIONS","G5-FRAC-ADD-SUB",
"G5-FRAC-MUL-DIV","G5-MEAS-CONVERSION","G5-VOLUME","G5-COORDINATES","G5-SHAPE-HIERARCHY"
)

def _fmt(v: Fraction)->str:
    return str(v.numerator) if v.denominator==1 else f"{v.numerator}/{v.denominator}"

@dataclass(frozen=True)
class Variant:
    concept_id:str
    mode:str
    seed:int
    item_id:str
    prompt:str
    public_fields:tuple[str,...]
    oracle:dict[str,object]
    def public_payload(self)->dict[str,object]:
        return {"concept_id":self.concept_id,"mode":self.mode,"item_id":self.item_id,"prompt":self.prompt,"response_fields":list(self.public_fields)}
    def teacher_oracle(self)->dict[str,object]:
        return dict(self.oracle)

def _validate(concept_id:str,seed:int,mode:str)->None:
    if concept_id not in CONCEPTS: raise ValueError("unknown concept")
    if isinstance(seed,bool) or not isinstance(seed,int): raise TypeError("seed must be integer")
    if seed<0: raise ValueError("seed must be nonnegative")
    if mode not in MODES: raise ValueError("mode must be guided or independent")

def generate(concept_id:str,seed:int,mode:str)->Variant:
    _validate(concept_id,seed,mode)
    rng=Random(f"{NAMESPACE}:{concept_id}:{mode}:{seed}")
    item_id=f"{NAMESPACE}:{concept_id}:{mode}:{seed}"
    band=(2,9) if mode=="guided" else (11,19)
    n=rng.randint(*band)

    if concept_id=="G5-EXPRESSIONS":
        a,b,c=rng.randint(2,6),rng.randint(1,8),rng.randint(2,5)
        value=(a+b)*c
        prompt=f"Translate 'the sum of {a} and {b}, multiplied by {c}' into an expression and evaluate it. Explain why grouping matters."
        oracle={"expression":f"({a}+{b})*{c}","value":value,"grouping_required":True}
        fields=("expression","grouping_explanation","value","reasonableness_check")

    elif concept_id=="G5-PATTERNS":
        s1,s2=rng.randint(1,5),rng.randint(2,8)
        d1,d2=rng.randint(2,5),rng.randint(3,7)
        pairs=[(s1+i*d1,s2+i*d2) for i in range(5)]
        prompt=f"Generate five terms for rules A: start {s1}, add {d1}; B: start {s2}, add {d2}. Compare corresponding terms and describe a relationship you can justify."
        oracle={"pairs":[list(p) for p in pairs],"differences":[b-a for a,b in pairs]}
        fields=("pattern_a","pattern_b","paired_table","relationship","evidence")

    elif concept_id=="G5-NBT-OPERATIONS":
        case=seed%4
        if case==0:
            value=Fraction(rng.randint(1,9999),100)
            prompt=f"Write {_fmt(value)} in expanded decimal place-value form and explain each digit's value."
            oracle={"value":_fmt(value),"place_value":True}
            fields=("expanded_form","place_value_explanation")
        elif case==1:
            a,b=rng.randint(100,999),rng.randint(10,99)
            prompt=f"Multiply {a} × {b}. Estimate first, then solve and explain place-value partial products."
            oracle={"answer":a*b,"estimate_reasonable":True}
            fields=("estimate","partial_products","answer","reasonableness")
        elif case==2:
            divisor=rng.randint(2,12); q=n; dividend=divisor*q+rng.randint(0,divisor-1)
            prompt=f"Divide {dividend} ÷ {divisor}. Give quotient and remainder, then interpret the remainder."
            oracle={"quotient":dividend//divisor,"remainder":dividend%divisor}
            fields=("estimate","quotient","remainder","remainder_interpretation")
        else:
            a=Fraction(rng.randint(10,999),100); b=Fraction(rng.randint(10,999),100)
            prompt=f"Compute {_fmt(a)} + {_fmt(b)} by aligning place values. Estimate first and justify the result."
            oracle={"answer":_fmt(a+b),"estimate_reasonable":True}
            fields=("estimate","place_value_alignment","answer","reasonableness")

    elif concept_id=="G5-FRAC-ADD-SUB":
        a=Fraction(rng.randint(1,5),rng.choice((2,3,4,5,6)))
        b=Fraction(rng.randint(1,5),rng.choice((2,3,4,5,6)))
        op="+" if seed%2==0 else "-"
        if op=="-" and a<b: a,b=b,a
        result=a+b if op=="+" else a-b
        prompt=f"Estimate and solve {_fmt(a)} {op} {_fmt(b)} using equivalent fractions. Explain the common unit."
        oracle={"answer":_fmt(result),"operation":op}
        fields=("estimate","equivalent_fractions","common_unit_explanation","answer")

    elif concept_id=="G5-FRAC-MUL-DIV":
        if seed%2==0:
            a=Fraction(rng.randint(1,5),rng.choice((2,3,4,5)))
            b=Fraction(rng.randint(1,5),rng.choice((2,3,4,5)))
            result=a*b
            prompt=f"Predict whether {_fmt(a)} × {_fmt(b)} is larger or smaller than {_fmt(a)}, then model and solve."
            oracle={"answer":_fmt(result),"scaling_relation":"SMALLER" if 0<b<1 else "LARGER_OR_EQUAL"}
        else:
            whole=rng.randint(2,8); unit=Fraction(1,rng.choice((2,3,4,5,6)))
            result=Fraction(whole,1)/unit
            prompt=f"How many groups of {_fmt(unit)} are in {whole}? Model the division and explain the quotient."
            oracle={"answer":_fmt(result),"measurement_division":True}
        fields=("prediction","model_explanation","equation","answer","context_interpretation")

    elif concept_id=="G5-MEAS-CONVERSION":
        factor=rng.choice((10,100,1000,12,3))
        value=rng.randint(2,9)
        prompt=f"A larger unit contains {factor} smaller units. Convert {value} larger units to smaller units and explain why multiplication is appropriate."
        oracle={"answer":value*factor,"factor":factor,"direction":"LARGER_TO_SMALLER"}
        fields=("conversion_factor","direction_explanation","equation","answer","units")

    elif concept_id=="G5-VOLUME":
        l,w,h=rng.randint(2,6),rng.randint(2,5),rng.randint(2,4)
        volume=l*w*h
        if seed%2==0:
            prompt=f"Build a {l}×{w}×{h} rectangular prism from unit-cube layers. Explain why l×w×h equals the cube count."
            oracle={"volume":volume,"base_area":l*w,"layers":h}
        else:
            l2=rng.randint(1,4)
            volume2=l2*w*h
            prompt=f"A composite solid is two non-overlapping rectangular prisms with volumes {l}×{w}×{h} and {l2}×{w}×{h}. Find total volume and justify addition."
            oracle={"volume":volume+volume2,"additive_volume":True}
        fields=("layer_model","equation","volume","cubic_units","surface_vs_volume_explanation")

    elif concept_id=="G5-COORDINATES":
        x,y=rng.randint(0,9),rng.randint(0,9)
        prompt=f"Plot point ({x},{y}) in the first quadrant, explain the role of each coordinate, and describe a context that could use this ordered pair."
        oracle={"point":[x,y],"x_first":True,"origin":[0,0]}
        fields=("point","x_axis_meaning","y_axis_meaning","context_interpretation")

    elif concept_id=="G5-SHAPE-HIERARCHY":
        case=seed%4
        cases=[
            ("square","rectangle","ALWAYS"),
            ("rectangle","parallelogram","ALWAYS"),
            ("rhombus","parallelogram","ALWAYS"),
            ("parallelogram","rectangle","SOMETIMES"),
        ]
        a,b,relation=cases[case]
        prompt=f"Is every {a} a {b}? Answer always, sometimes, or never, and justify using defining attributes rather than appearance."
        oracle={"relation":relation,"use_defining_attributes":True}
        fields=("classification","defining_attributes","hierarchy_justification","counterexample_if_needed")

    else:
        raise AssertionError
    return Variant(concept_id,mode,seed,item_id,prompt,tuple(fields),oracle)
