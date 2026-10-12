"""Deterministic DRAFT variants for the Grade 1 gap-closure wave."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

STATUS="DRAFT_UNVERIFIED"
RUNTIME_ACTIVATION=False
NAMESPACE="grade1-gap-closure-wave1"
MODES=frozenset({"guided","independent"})
CONCEPTS=("G1-COUNT-REPRESENT","G1-PLACE-VALUE","G1-ADDITION","G1-SUBTRACTION","G1-WORD-PROBLEMS","G1-EQUALITY-UNKNOWNS","G1-TIME","G1-SHAPES")

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
    if concept_id=="G1-COUNT-REPRESENT":
        n=rng.randint(0,120)
        others=[max(0,min(120,n+d)) for d in (-2,1,3)]
        prompt=f"Show a quantity of {n}, write its numeral and number name, then order {n}, {others[0]}, {others[1]}, {others[2]} from least to greatest."
        oracle={"numeral":n,"ordered":sorted([n,*others]),"within_boundary":0<=n<=120}
        fields=("quantity_description","numeral","number_name","ordered_list")
    elif concept_id=="G1-PLACE-VALUE":
        n=rng.randint(10,99); tens=n//10; ones=n%10
        prompt=f"Build {n} with tens and ones. Explain the value of each digit and show an exchange of one ten for ten ones that keeps the total the same."
        oracle={"tens":tens,"ones":ones,"value":n,"exchange_preserves_value":True}
        fields=("tens_ones_model","digit_value_explanation","exchange_explanation")
    elif concept_id=="G1-ADDITION":
        a,b=rng.randint(0,10),rng.randint(0,10)
        if a+b>20: b=20-a
        prompt=f"Solve {a}+{b}. Show a counting-on or make-ten strategy and explain why the total is reasonable."
        oracle={"answer":a+b,"within20":True}
        fields=("strategy_model","equation","answer","reasonableness")
    elif concept_id=="G1-SUBTRACTION":
        a=rng.randint(5,20); b=rng.randint(0,a)
        prompt=f"Solve {a}-{b}. Show take-away or count-up reasoning and connect the result to an addition fact."
        oracle={"answer":a-b,"addition_check":f"{a-b}+{b}={a}"}
        fields=("subtraction_model","answer","addition_check","strategy_explanation")
    elif concept_id=="G1-WORD-PROBLEMS":
        role=seed%4
        if role==0:
            start,change=rng.randint(1,10),rng.randint(1,10); result=start+change
            prompt=f"There were {start} birds. {change} more came. How many are there now?"
            oracle={"answer":result,"role":"RESULT_UNKNOWN"}
        elif role==1:
            start,result=rng.randint(1,10),rng.randint(11,20); change=result-start
            prompt=f"There were {start} birds. More came, making {result}. How many came?"
            oracle={"answer":change,"role":"CHANGE_UNKNOWN"}
        elif role==2:
            change,result=rng.randint(1,10),rng.randint(11,20); start=result-change
            prompt=f"Some birds were there. {change} more came, making {result}. How many were there at first?"
            oracle={"answer":start,"role":"START_UNKNOWN"}
        else:
            a,b=rng.randint(1,20),rng.randint(1,20)
            if a<b: a,b=b,a
            prompt=f"Mia has {a} blocks and Noah has {b}. How many more blocks does Mia have?"
            oracle={"answer":a-b,"role":"COMPARE_DIFFERENCE"}
        fields=("story_structure","model","equation","answer")
    elif concept_id=="G1-EQUALITY-UNKNOWNS":
        if seed%2==0:
            a,b=rng.randint(0,10),rng.randint(0,10); total=a+b
            prompt=f"Is {total} = {a}+{b} true? Explain what the equal sign means and write the symmetric equation."
            oracle={"truth":True,"symmetric":f"{a}+{b}={total}","equality_only":True}
            fields=("truth_value","equal_sign_meaning","symmetric_equation")
        else:
            a,b=rng.randint(0,10),rng.randint(0,10); total=a+b
            prompt=f"Find the missing number in □ + {b} = {total}. Show a model and verify both sides have the same value."
            oracle={"unknown":a,"verification":True,"unknown_solving_only":True}
            fields=("model","unknown","verification","equal_sign_explanation")
    elif concept_id=="G1-TIME":
        hour=rng.randint(1,12); half=seed%2==1; minute=30 if half else 0
        prompt=f"Read and represent {hour}:{minute:02d} on analog and digital clocks. Explain what each hand shows."
        oracle={"time":f"{hour}:{minute:02d}","hour":hour,"minute":minute}
        fields=("analog_description","digital_time","hour_hand_explanation","minute_hand_explanation")
    elif concept_id=="G1-SHAPES":
        shape=rng.choice(("triangle","square","rectangle","circle"))
        prompt=f"Describe defining attributes of a {shape}, explain one non-defining attribute, then describe how to compose or partition shapes to create a larger figure or equal shares."
        oracle={"shape":shape,"requires_defining_attributes":True,"composition_or_partition":True}
        fields=("defining_attributes","non_defining_attribute","composition_or_partition","equal_share_explanation")
    else: raise AssertionError
    return Variant(concept_id,mode,seed,item_id,prompt,tuple(fields),oracle)
