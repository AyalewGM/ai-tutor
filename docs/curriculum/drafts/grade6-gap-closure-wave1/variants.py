"""Deterministic DRAFT variants for the Grade 6 gap-closure wave."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from random import Random

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade6-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
CONCEPTS=(
"G6-FRACTION-DIVISION","G6-EXPRESSIONS","G6-EQUATIONS",
"G6-POLYGON-COORDINATE","G6-NETS-SURFACE","G6-STAT-DISTRIBUTIONS","G6-RATIO-RATE"
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
    band=(2,9) if mode=="guided" else (11,19)
    n=rng.randint(*band)
    item_id=f"{NAMESPACE}:{concept_id}:{mode}:{seed}"
    if concept_id=="G6-FRACTION-DIVISION":
        a=Fraction(rng.randint(1,5),rng.choice((2,3,4,5)))
        b=Fraction(rng.randint(1,4),rng.choice((2,3,4)))
        q=a/b
        prompt=f"Estimate, model, and solve {_fmt(a)} ÷ {_fmt(b)}. Explain the context meaning and why reciprocal multiplication matches the model."
        oracle={"quotient":_fmt(q),"reciprocal_product":_fmt(a*Fraction(b.denominator,b.numerator)),"estimate_relation":"GT1" if q>1 else "LT1"}
        fields=("estimate","visual_model_explanation","equation","exact_quotient","context_interpretation")
    elif concept_id=="G6-EXPRESSIONS":
        x=n
        a=rng.randint(2,5); b=rng.randint(1,6)
        value=a*(x+b)
        prompt=f"Evaluate {a}(x+{b}) when x={x}, expand to an equivalent expression, and name the property used."
        oracle={"value":value,"expanded":f"{a}x+{a*b}","property":"DISTRIBUTIVE_PROPERTY"}
        fields=("substitution","order_of_operations","expanded_expression","property_justification")
    elif concept_id=="G6-EQUATIONS":
        a=Fraction(rng.randint(1,5),rng.choice((1,1,2)))
        x=Fraction(n,1)
        b=a*x
        prompt=f"A quantity x multiplied by {_fmt(a)} equals {_fmt(b)}. Write and solve the equation, verify by substitution, and interpret x on a number line."
        oracle={"equation":f"{_fmt(a)}x={_fmt(b)}","solution":_fmt(x),"substitution":True}
        fields=("equation","inverse_operation","solution","substitution_check","number_line_interpretation")
    elif concept_id=="G6-POLYGON-COORDINATE":
        w=rng.randint(3,8); h=rng.randint(2,7)
        # Guided practice may use the origin; independent transfer is translated
        # so a same-seed item cannot repeat the learner-visible coordinate task.
        x0,y0=(0,0) if mode=="guided" else (rng.randint(2,6),rng.randint(2,6))
        prompt=f"A rectangle has vertices ({x0},{y0}),({x0+w},{y0}),({x0+w},{y0+h}),({x0},{y0+h}). Find side lengths, perimeter, and area, then explain how coordinate differences produced the lengths."
        oracle={"width":w,"height":h,"perimeter":2*(w+h),"area":w*h}
        fields=("side_lengths","perimeter","area","coordinate_reasoning")
    elif concept_id=="G6-NETS-SURFACE":
        shape="RECTANGULAR_PRISM" if seed%2==0 else "SQUARE_PYRAMID"
        if shape=="RECTANGULAR_PRISM":
            l,w,h=rng.randint(2,6),rng.randint(2,5),rng.randint(2,4)
            sa=2*(l*w+l*h+w*h)
            prompt=f"A rectangular prism has dimensions {l} by {w} by {h}. Describe a valid net and compute exact surface area."
            oracle={"shape":shape,"faces":6,"surface_area":sa}
        else:
            b=rng.randint(2,6); slant=rng.randint(2,6)
            sa=b*b+4*Fraction(b*slant,2)
            prompt=f"A square pyramid has base side {b} and triangular face height {slant}. Describe a valid net and compute surface area."
            oracle={"shape":shape,"faces":5,"surface_area":_fmt(sa)}
        fields=("net_description","face_count","face_areas","surface_area","volume_vs_surface_explanation")
    elif concept_id=="G6-STAT-DISTRIBUTIONS":
        data=[rng.randint(1,20) for _ in range(9)]
        s=sorted(data)
        med=s[4]
        q1=Fraction(s[1]+s[2],2)
        q3=Fraction(s[6]+s[7],2)
        iqr=q3-q1
        prompt=(
            f"For data {data}, compute the five-number summary and IQR using the "
            "exclusive-median convention: omit the overall median, then average the "
            "middle two values of each four-value half. Describe spread and choose "
            "mean or median as a more useful center with justification."
        )
        oracle={
            "min":s[0],
            "q1":q1,
            "median":med,
            "q3":q3,
            "max":s[-1],
            "iqr":iqr,
            "sorted_data":s,
            "quartile_convention":"EXCLUDE_MEDIAN_AVERAGE_HALVES",
        }
        fields=("five_number_summary","iqr","shape_or_outlier_comment","center_choice","context_justification")
    elif concept_id=="G6-RATIO-RATE":
        a=rng.randint(2,6); b=rng.randint(3,9); scale=rng.randint(2,5)
        prompt=f"A ratio is {a}:{b}. Complete an equivalent-ratio table for scale factor {scale}, show it on a double number line, and state both unit rates."
        oracle={"scaled":[a*scale,b*scale],"unit_rate_b_per_a":_fmt(Fraction(b,a)),"unit_rate_a_per_b":_fmt(Fraction(a,b))}
        fields=("ratio_table","double_number_line","scale_factor","unit_rate","interpretation")
    else:
        raise AssertionError
    return Variant(concept_id,mode,seed,item_id,prompt,tuple(fields),oracle)
