import scripts.self_healing_smoke as smoke


def test_smoke_contracts_pass():
    assert smoke.main() == 0
