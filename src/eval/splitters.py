import numpy as np
import pandas as pd
from typing import Iterator, Tuple

class PurgedKFold:
    """
    Purged K-Fold CV for time series.
    - Splits are contiguous by time order.
    - Training folds are 'purged' around test indices.
    - Optional embargo removes a post-test buffer from training.

    Usage:
      pkf = PurgedKFold(n_splits=5, embargo=5)
      for tr_idx, te_idx in pkf.split(times):
          ...
    """
    def __init__(self, n_splits: int = 5, embargo: int = 0):
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        self.n_splits = n_splits
        self.embargo = max(0, int(embargo))

    def split(self, times: pd.Index | pd.Series) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        if isinstance(times, pd.Series):
            times = times.index

        n = len(times)
        if n < self.n_splits:
            raise ValueError("Not enough samples for the requested number of splits")

        fold_sizes = np.full(self.n_splits, n // self.n_splits, dtype=int)
        fold_sizes[: n % self.n_splits] += 1

        indices = np.arange(n)
        current = 0
        for fold_size in fold_sizes:
            start, stop = current, current + fold_size
            test_indices = indices[start:stop]

            # Purge + embargo around test region
            left_purge_end = start  # train can use [0 : start)
            right_purge_start = stop + self.embargo  # train can use [right_purge_start : n)

            train_left = indices[:left_purge_end]
            train_right = indices[right_purge_start:]

            train_indices = np.concatenate([train_left, train_right])
            yield train_indices, test_indices

            current = stop
