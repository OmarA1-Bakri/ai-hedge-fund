import numpy as np
import pandas as pd

from src.eval.splitters import PurgedKFold

def test_purged_kfold_no_overlap_with_embargo():
    idx = pd.bdate_range("2024-01-01", periods=50)
    pkf = PurgedKFold(n_splits=5, embargo=3)

    for tr_idx, te_idx in pkf.split(idx):
        # Train and test must be disjoint
        assert set(tr_idx).isdisjoint(set(te_idx))
        # Embargo gap after test
        if len(te_idx):
            max_test = te_idx.max()
            # Any training index <= max_test+embargo must be < min(train_right)
            assert not any((tr > max_test) and (tr <= max_test + 3) for tr in tr_idx)
