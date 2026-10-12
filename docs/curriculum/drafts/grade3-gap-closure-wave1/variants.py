"""Deterministic DRAFT variants for the Grade 3 gap-closure wave."""

from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from random import Random

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade3-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
CONCEPTS=("G3-MULTIPLICATION","G3-DIVISION","G3-FACT-FAMILIES","G3-PLACE-VALUE","G3-FRACTIONS","G3-TIME","G3-DATA","G3-AREA-PERIMETER","G3-SHAPES")

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
        n=rng.randint(100,999); rounded10=round(n/10)*10; rounded100=round(n/100)*100
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
        scale=rng.choice((2,5,10)); cats=["A","B","C"]; counts=[rng.randint(1,5)*scale for _ in cats]
        prompt=f"A scaled bar graph uses 1 grid unit = {scale}. Categories A,B,C have counts {counts}. Give the bar heights in grid units and answer which category is greatest."
        heights=[c//scale for c in counts]; idx=max(range(3),key=lambda i:counts[i])
        oracle={"heights":heights,"greatest":cats[idx],"scale":scale}
        fields=("scale","bar_heights","greatest_category","comparison_explanation")
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
