from src.utils.config import load_config

def test_config_loads_and_has_core_keys():
    cfg = load_config()
    assert isinstance(cfg.get("data.tickers"), list) and len(cfg.get("data.tickers")) >= 1
    assert cfg.get("risk.single_name_max_weight") <= 1.0
    assert cfg.get("costs.bps_per_trade") >= 0
