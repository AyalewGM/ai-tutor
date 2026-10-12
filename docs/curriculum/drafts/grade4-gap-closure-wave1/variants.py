"""Deterministic DRAFT variants for the Grade 4 gap-closure wave."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from random import Random

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade4-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
CONCEPTS=("G4-MULT-COMP","G4-MULTISTEP-WORD","G4-FACTORS-PATTERNS","G4-PLACE-VALUE","G4-MULTIPLICATION","G4-DIVISION","G4-FRACTIONS","G4-DECIMAL-FRACTIONS","G4-MEASUREMENT","G4-ANGLES-LINES-SHAPES")

def _fmt(v:Fraction)->str:
    return str(v.numerator) if v.denominator==1 else f"{v.numerator}/{v.denominator}"

@dataclass(frozen=True)
class Variant:
    concept_id:str; mode:str; seed:int; item_id:str; prompt:str; public_fields:tuple[str,...]; oracle:dict[str,object]
    def public_payload(self)->dict[str,object]:
        return {"concept_id":self.concept_id,"mode":self.mode,"item_id":self.item_id,"prompt":self.prompt,"response_fields":list(self.public_fields)}
    def teacher_oracle(self)->dict[str,object]: return dict(self.oracle)

def _validate(concept_id:str,seed:int,mode:str)->None:
    if concept_id not in CONCEPTS: raise ValueError("unknown concept")
    if isinstance(seed,bool) or not isinstance(seed,int): raise TypeError("seed must be integer")
    if seed<0: raise ValueError("seed must be nonnegative")
    if mode not in MODES: raise ValueError("mode must be guided or independent")

def _round_half_up_positive(value:int,place:int)->int:
    if value<0 or place<=0:
        raise ValueError("positive elementary rounding only")
    return ((value + place//2)//place)*place

def generate(concept_id:str,seed:int,mode:str)->Variant:
    _validate(concept_id,seed,mode)
    rng=Random(f"{NAMESPACE}:{concept_id}:{mode}:{seed}")
    item_id=f"{NAMESPACE}:{concept_id}:{mode}:{seed}"
    if concept_id=="G4-MULT-COMP":
        factor=rng.randint(2,8); base=rng.randint(2,12); total=factor*base
        prompt=f"Maya has {factor} times as many beads as Leo. Leo has {base}. How many does Maya have? Show a comparison model and equation."
        oracle={"factor":factor,"base":base,"answer":total,"equation":f"{factor}*{base}={total}"}
        fields=("comparison_model","equation","answer","units")
    elif concept_id=="G4-MULTISTEP-WORD":
        groups=rng.randint(2,7); each=rng.randint(3,9); extra=rng.randint(1,12); total=groups*each+extra
        prompt=f"There are {groups} boxes with {each} items each and {extra} loose items. How many items total? Explain the operation sequence and estimate first."
        oracle={"answer":total,"operations":["MULTIPLY","ADD"]}
        fields=("estimate","operation_sequence","intermediate_meaning","answer")
    elif concept_id=="G4-FACTORS-PATTERNS":
        n=rng.randint(12,60); factors=[i for i in range(1,n+1) if n%i==0]
        multiple_base=n//max(1,len(factors)//2)
        multiples=[multiple_base*i for i in range(1,6)]
        prompt=f"List all factor pairs of {n}, classify it as prime or composite, and give the first five multiples of {multiple_base}."
        oracle={
            "factors":factors,
            "classification":"PRIME" if len(factors)==2 else "COMPOSITE",
            "multiple_base":multiple_base,
            "multiples":multiples,
        }
        fields=("factor_pairs","classification","multiples","pattern_explanation")
    elif concept_id=="G4-PLACE-VALUE":
        n=rng.randint(10000,999999)
        prompt=f"Write {n} in expanded form, identify the value of its leftmost digit, and round it to the nearest thousand."
        place=10**(len(str(n))-1); lead=int(str(n)[0]); rounded=_round_half_up_positive(n,1000)
        oracle={"expanded_required":True,"leftmost_value":lead*place,"rounded_thousand":rounded}
        fields=("expanded_form","leftmost_value","rounded_thousand","number_line_justification")
    elif concept_id=="G4-MULTIPLICATION":
        a=rng.randint(12,99); b=rng.randint(12,99)
        prompt=f"Estimate and solve {a}×{b} using partial products or an area model, then compare with your estimate."
        oracle={"answer":a*b}
        fields=("estimate","partial_products","answer","reasonableness")
    elif concept_id=="G4-DIVISION":
        d=rng.randint(2,9); q=rng.randint(10,80); r=rng.randint(0,d-1); dividend=d*q+r
        prompt=f"Divide {dividend} by {d}. Give quotient and remainder and verify with multiplication."
        oracle={"quotient":q,"remainder":r,"check":d*q+r}
        fields=("estimate","quotient","remainder","multiplication_check","remainder_interpretation")
    elif concept_id=="G4-FRACTIONS":
        a=Fraction(rng.randint(1,7),rng.choice((2,3,4,5,6,8)))
        b=Fraction(rng.randint(1,7),a.denominator)
        result=a+b
        prompt=f"Use a same-whole model to solve {_fmt(a)} + {_fmt(b)} and explain why the denominator stays {a.denominator}."
        oracle={"answer":_fmt(result),"common_denominator":a.denominator}
        fields=("model","equivalent_or_same_unit_explanation","answer","reasonableness")
    elif concept_id=="G4-DECIMAL-FRACTIONS":
        hundredths=rng.randint(1,99); value=Fraction(hundredths,100)
        prompt=f"Write {hundredths}/100 as a decimal, place it on a number line, and compare it with {rng.randint(1,9)}/10."
        oracle={"decimal":f"{float(value):.2f}"}
        fields=("decimal","number_line_location","comparison","place_value_explanation")
    elif concept_id=="G4-MEASUREMENT":
        factor=rng.choice((12,3,16,100,1000)); value=rng.randint(2,10)
        prompt=f"A larger unit contains {factor} smaller units. Convert {value} larger units to smaller units and explain the multiplication."
        oracle={"answer":value*factor,"factor":factor}
        fields=("conversion_factor","equation","answer","units","direction_explanation")
    elif concept_id=="G4-ANGLES-LINES-SHAPES":
        a=rng.randint(20,70); b=90-a
        prompt=f"Two angles form a right angle. One is {a}°. Find the other, sketch the relationship, and name a defining line/angle property visible in the diagram."
        oracle={"missing_angle":b,"sum":90}
        fields=("missing_angle","angle_sum_explanation","sketch_description","shape_or_line_property")
    else: raise AssertionError
    return Variant(concept_id,mode,seed,item_id,prompt,tuple(fields),oracle)
