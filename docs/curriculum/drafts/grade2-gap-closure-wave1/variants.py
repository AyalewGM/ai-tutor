"""Deterministic DRAFT variants for the Grade 2 gap-closure wave."""

from __future__ import annotations
from dataclasses import dataclass
from random import Random

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade2-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
CONCEPTS=("G2-PLACE-VALUE","G2-SKIP-PATTERNS","G2-ADDITION","G2-SUBTRACTION","G2-WORD-PROBLEMS","G2-MONEY","G2-LENGTH","G2-TIME","G2-SHAPES-SHARES")

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
    if concept_id=="G2-PLACE-VALUE":
        n=rng.randint(100,999); h,t,o=n//100,(n//10)%10,n%10
        prompt=f"Build {n} with base-ten blocks, write it in expanded and word form, and show one exchange that keeps the value the same."
        oracle={"hundreds":h,"tens":t,"ones":o,"expanded":f"{h*100}+{t*10}+{o}","value":n}
        fields=("block_inventory","expanded_form","word_form","exchange_explanation")
    elif concept_id=="G2-SKIP-PATTERNS":
        start=rng.choice((0,5,10,20,100)); step=rng.choice((5,10,100)); seq=[start+i*step for i in range(6)]
        prompt=f"Start at {start} and skip-count by {step}. Give the next five numbers, explain the pattern, then state one number immediately before the last term."
        oracle={"sequence":seq,"step":step}
        fields=("sequence","step_explanation","previous_term")
    elif concept_id=="G2-ADDITION":
        a,b=rng.randint(20,79),rng.randint(10,39)
        if a+b>=100: b=99-a
        prompt=f"Solve {a}+{b} with tens-and-ones blocks. Show any regrouping and check with subtraction or an estimate."
        oracle={"answer":a+b,"regroup":(a%10+b%10)>=10}
        fields=("tens_ones_model","regroup_explanation","answer","check")
    elif concept_id=="G2-SUBTRACTION":
        a=rng.randint(40,99); b=rng.randint(10,a-1)
        prompt=f"Solve {a}-{b} with tens-and-ones blocks. If needed, decompose one ten and explain why the total value stays the same."
        oracle={"answer":a-b,"decompose_ten":(a%10)<(b%10)}
        fields=("tens_ones_model","decomposition_explanation","answer","addition_check")
    elif concept_id=="G2-WORD-PROBLEMS":
        role=seed%4
        if role==0:
            start,change=rng.randint(20,50),rng.randint(5,25); result=start+change
            prompt=f"A jar had {start} buttons and got {change} more. How many now?"
            oracle={"answer":result,"role":"RESULT_UNKNOWN","operation":"ADD"}
        elif role==1:
            start,result=rng.randint(20,50),rng.randint(55,90); change=result-start
            prompt=f"A jar had {start} buttons. After more were added, it had {result}. How many were added?"
            oracle={"answer":change,"role":"CHANGE_UNKNOWN","operation":"SUBTRACT"}
        elif role==2:
            change,result=rng.randint(5,25),rng.randint(40,90); start=result-change
            prompt=f"Some buttons were in a jar. {change} more were added, making {result}. How many were there at first?"
            oracle={"answer":start,"role":"START_UNKNOWN","operation":"SUBTRACT"}
        else:
            a,b=rng.randint(20,50),rng.randint(10,40)
            if a<b: a,b=b,a
            prompt=f"Maya has {a} stickers and Lee has {b}. How many more does Maya have?"
            oracle={"answer":a-b,"role":"COMPARE_DIFFERENCE","operation":"SUBTRACT"}
        fields=("story_structure","equation_or_model","answer","units")
    elif concept_id=="G2-MONEY":
        quarters=rng.randint(0,4); dimes=rng.randint(0,5); nickels=rng.randint(0,4); pennies=rng.randint(0,9)
        cents=25*quarters+10*dimes+5*nickels+pennies
        prompt=f"Count {quarters} quarters, {dimes} dimes, {nickels} nickels, and {pennies} pennies. Give the total in cents and dollars/cents notation."
        oracle={"cents":cents,"notation":f"${cents/100:.2f}"}
        fields=("counting_strategy","cents","dollar_cent_notation","equivalent_collection")
    elif concept_id=="G2-LENGTH":
        length=rng.randint(10,90); unit=rng.choice(("cm","in"))
        prompt=f"An object is about {length} {unit} long. Choose an appropriate measuring tool, explain where measurement should start, and compare it with an object 7 {unit} shorter."
        oracle={"length":length,"difference":7,"other_length":length-7,"start_at_zero":True}
        fields=("tool_choice","start_point","estimate","measured_length","comparison")
    elif concept_id=="G2-TIME":
        hour=rng.randint(1,12); minute=rng.choice(tuple(range(0,60,5)))
        prompt=f"Show {hour}:{minute:02d} on an analog clock, name the hour/minute hands, and explain how many groups of five minutes the minute hand has moved from 12."
        oracle={"time":f"{hour}:{minute:02d}","five_minute_groups":minute//5}
        fields=("analog_description","hour_hand","minute_hand","five_minute_groups","digital_time")
    elif concept_id=="G2-SHAPES-SHARES":
        parts=rng.choice((2,3,4)); shape=rng.choice(("rectangle","circle")); name={2:"halves",3:"thirds",4:"fourths"}[parts]
        prompt=f"Partition a {shape} into {parts} equal shares. Explain why the shares are equal in area and name each share."
        oracle={"parts":parts,"share_name":name,"equal_area_required":True}
        fields=("partition_description","equal_area_explanation","share_name","whole_part_relationship")
    else: raise AssertionError
    return Variant(concept_id,mode,seed,item_id,prompt,tuple(fields),oracle)
