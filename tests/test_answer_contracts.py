from app.answer_contracts import AnswerContract, AnswerKind


def test_integer_contract_rejects_decimal_string():
    contract = AnswerContract(AnswerKind.INTEGER)
    assert contract.equivalent('12', '+12')
    assert not contract.equivalent('12.0', '12')
