# Architecture — ai-hedge-fund

## Flow (high level)
Data Ingestion → Feature Generation → Agents (scores ∈ [-1,1], confidence) → Meta-Blend (μ, σ) → Risk Model (Σ̂ LW) → Optimizer (constraints) → Orders → Execution Adapter (paper/live) → Portfolio P&L → Eval/Tearsheet

## Modules
- `src/features/`: microstructure, regime, sentiment, fundamentals, labels
- `src/agents/`: valuation, technicals, sentiment, fundamentals (all return (score, confidence))
- `src/meta_ensemble/blender.py`: blends agent scores → (μ, σ)
- `src/risk/risk_model.py`: Ledoit–Wolf shrinkage covariance
- `src/portfolio/optimizer.py`: mean–variance w/ constraints (gross/net, single-name, turnover)
- `src/execution/adapter.py`: paper broker + stubs (IBKR/CCXT)
- `src/eval/`: walk-forward + tearsheet
- `config/config.yaml`: single source of truth for params
- `.env`: keys only

## Evaluation hygiene
- Purged K-Fold + embargo for all model CV
- Walk-forward train/test splits
- Costs & slippage modeled in backtests
- Reproducible seeds
