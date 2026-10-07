"""Authoritative California Grade-9 pathway leaf-standard inventories.

California higher mathematics is course/pathway organized. These identifiers are
transcribed from the 2013 CA CCSSM Algebra I and Mathematics I model-course
sections. Inventory alone is not a mapping or completion claim.
"""

CA_ALGEBRA_I_STANDARD_CODES = (
    "N-RN.1", "N-RN.2", "N-RN.3",
    "N-Q.1", "N-Q.2", "N-Q.3",
    "A-SSE.1.a", "A-SSE.1.b", "A-SSE.2", "A-SSE.3.a", "A-SSE.3.b", "A-SSE.3.c",
    "A-APR.1",
    "A-CED.1", "A-CED.2", "A-CED.3", "A-CED.4",
    "A-REI.1", "A-REI.3", "A-REI.3.1", "A-REI.4.a", "A-REI.4.b",
    "A-REI.5", "A-REI.6", "A-REI.7", "A-REI.10", "A-REI.11", "A-REI.12",
    "F-IF.1", "F-IF.2", "F-IF.3", "F-IF.4", "F-IF.5", "F-IF.6",
    "F-IF.7.a", "F-IF.7.b", "F-IF.7.e", "F-IF.8.a", "F-IF.8.b", "F-IF.9",
    "F-BF.1.a", "F-BF.1.b", "F-BF.2", "F-BF.3", "F-BF.4.a",
    "F-LE.1.a", "F-LE.1.b", "F-LE.1.c", "F-LE.2", "F-LE.3", "F-LE.5", "F-LE.6",
    "S-ID.1", "S-ID.2", "S-ID.3", "S-ID.5",
    "S-ID.6.a", "S-ID.6.b", "S-ID.6.c", "S-ID.7", "S-ID.8", "S-ID.9",
)

CA_MATHEMATICS_I_STANDARD_CODES = (
    "N-Q.1", "N-Q.2", "N-Q.3",
    "A-SSE.1.a", "A-SSE.1.b",
    "A-CED.1", "A-CED.2", "A-CED.3", "A-CED.4",
    "A-REI.1", "A-REI.3", "A-REI.3.1", "A-REI.5", "A-REI.6",
    "A-REI.10", "A-REI.11", "A-REI.12",
    "F-IF.1", "F-IF.2", "F-IF.3", "F-IF.4", "F-IF.5", "F-IF.6",
    "F-IF.7.a", "F-IF.7.e", "F-IF.9",
    "F-BF.1.a", "F-BF.1.b", "F-BF.2", "F-BF.3",
    "F-LE.1.a", "F-LE.1.b", "F-LE.1.c", "F-LE.2", "F-LE.3", "F-LE.5",
    "G-CO.1", "G-CO.2", "G-CO.3", "G-CO.4", "G-CO.5",
    "G-CO.6", "G-CO.7", "G-CO.8", "G-CO.12", "G-CO.13",
    "G-GPE.4", "G-GPE.5", "G-GPE.7",
    "S-ID.1", "S-ID.2", "S-ID.3", "S-ID.5",
    "S-ID.6.a", "S-ID.6.b", "S-ID.6.c", "S-ID.7", "S-ID.8", "S-ID.9",
)


def validate_grade9_pathway_inventories() -> None:
    for name, codes in (
        ("ALGEBRA_I", CA_ALGEBRA_I_STANDARD_CODES),
        ("MATHEMATICS_I", CA_MATHEMATICS_I_STANDARD_CODES),
    ):
        if any(not code.strip() for code in codes):
            raise ValueError(f"{name} contains an empty standard code")
        if len(codes) != len(set(codes)):
            raise ValueError(f"{name} contains duplicate standard codes")


validate_grade9_pathway_inventories()
