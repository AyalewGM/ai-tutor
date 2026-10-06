# Maryland and Ontario ingestion proof

This proof exercises the scalable curriculum pipeline against the two existing jurisdictions without changing mathematical correctness or learner mastery logic.

The test seeds the existing Maryland Algebra I and Ontario MTH1W curriculum data, reuses their existing canonical mathematical identities, ingests representative authoritative standards as DRAFT data, passes each proposed mapping through the explicit human-review publication gate, and publishes each curriculum version.

The proof asserts that Maryland and Ontario retain distinct curriculum/version identities and mapping records, while learner evidence row counts remain unchanged. A published version also fails closed if draft ingestion attempts to overwrite it.

The proof-pack standard used for Maryland is intentionally labelled as a Mihur proof identifier rather than asserting an unsupported official standard code. The authoritative MSDE source remains the provenance source. Future production ingestion should use verified official standard identifiers extracted from the authoritative source.

This establishes the architecture path for #224. The next no-fork test in #225 is Virginia + Alberta.
