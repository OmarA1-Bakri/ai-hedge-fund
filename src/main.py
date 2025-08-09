# src/main.py
import sys
import json
import argparse
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any

from dotenv import load_dotenv
from colorama import Fore, Style, init
import questionary

from src.utils.display import print_trading_output
from src.utils.analysts import ANALYST_ORDER
from src.llm.models import LLM_ORDER, OLLAMA_LLM_ORDER, get_model_info, ModelProvider
from src.utils.ollama import ensure_ollama_and_model
from src.utils.config import load_config
from src.utils.visualize import save_graph_as_png

# Import the engine (no circular imports)
from src.engine.runner import create_workflow, run_hedge_fund

# Load environment variables from .env file
load_dotenv()
init(autoreset=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the hedge fund trading system")
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration file")
    parser.add_argument("--initial-cash", type=float, default=None, help="Override starting cash")
    parser.add_argument("--margin-requirement", type=float, default=None, help="Override margin requirement")
    parser.add_argument("--tickers", type=str, default=None, help="Comma-separated tickers (override config)")
    parser.add_argument("--start-date", type=str, help="YYYY-MM-DD (override config)")
    parser.add_argument("--end-date", type=str, help="YYYY-MM-DD (override config)")
    parser.add_argument("--show-reasoning", action="store_true", help="Show reasoning from each agent")
    parser.add_argument("--show-agent-graph", action="store_true", help="Export agent graph PNG")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama for local LLM inference")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # Resolve tickers: CLI > config
    if args.tickers:
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    else:
        tickers = cfg.get("data.tickers", [])
    if not tickers:
        print("Error: No tickers provided (CLI or config).")
        sys.exit(2)

    # Resolve dates: CLI > config > sensible defaults
    if args.start_date:
        datetime.strptime(args.start_date, "%Y-%m-%d")
    if args.end_date:
        datetime.strptime(args.end_date, "%Y-%m-%d")

    end_date = args.end_date or cfg.get("data.end_date") or datetime.now().strftime("%Y-%m-%d")
    start_date = args.start_date or cfg.get("data.start_date")
    if not start_date:
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_date_obj - relativedelta(months=3)).strftime("%Y-%m-%d")

    # Interactive analyst selection
    analyst_choices = questionary.checkbox(
        "Select your AI analysts.",
        choices=[questionary.Choice(display, value=value) for display, value in ANALYST_ORDER],
        instruction=(
            "\n\nInstructions: \n"
            "1. Press Space to select/unselect analysts.\n"
            "2. Press 'a' to select/unselect all.\n"
            "3. Press Enter when done to run the hedge fund.\n"
        ),
        validate=lambda x: len(x) > 0 or "You must select at least one analyst.",
        style=questionary.Style(
            [
                ("checkbox-selected", "fg:green"),
                ("selected", "fg:green noinherit"),
                ("highlighted", "noinherit"),
                ("pointer", "noinherit"),
            ]
        ),
    ).ask()

    if not analyst_choices:
        print("\n\nInterrupt received. Exiting...")
        sys.exit(0)
    selected_analysts = analyst_choices
    print(
        f"\nSelected analysts: "
        f"{', '.join(Fore.GREEN + choice.title().replace('_', ' ') + Style.RESET_ALL for choice in selected_analysts)}\n"
    )

    # LLM model selection
    if args.ollama:
        print(f"{Fore.CYAN}Using Ollama for local LLM inference.{Style.RESET_ALL}")
        model_name = questionary.select(
            "Select your Ollama model:",
            choices=[questionary.Choice(display, value=value) for display, value, _ in OLLAMA_LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()
        if not model_name:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)
        if model_name == "-":
            model_name = questionary.text("Enter the custom model name:").ask()
            if not model_name:
                print("\n\nInterrupt received. Exiting...")
                sys.exit(0)
        if not ensure_ollama_and_model(model_name):
            print(f"{Fore.RED}Cannot proceed without Ollama and the selected model.{Style.RESET_ALL}")
            sys.exit(1)
        model_provider = ModelProvider.OLLAMA.value
        print(f"\nSelected {Fore.CYAN}Ollama{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n")
    else:
        choice = questionary.select(
            "Select your LLM model:",
            choices=[questionary.Choice(display, value=(name, provider)) for display, name, provider in LLM_ORDER],
            style=questionary.Style(
                [
                    ("selected", "fg:green bold"),
                    ("pointer", "fg:green bold"),
                    ("highlighted", "fg:green"),
                    ("answer", "fg:green bold"),
                ]
            ),
        ).ask()
        if not choice:
            print("\n\nInterrupt received. Exiting...")
            sys.exit(0)
        model_name, model_provider = choice
        model_info = get_model_info(model_name, model_provider)
        if model_info and model_info.is_custom():
            model_name = questionary.text("Enter the custom model name:").ask()
            if not model_name:
                print("\n\nInterrupt received. Exiting...")
                sys.exit(0)
        print(f"\nSelected {Fore.CYAN}{model_provider}{Style.RESET_ALL} model: {Fore.GREEN + Style.BRIGHT}{model_name}{Style.RESET_ALL}\n")

    # Initialize portfolio
    initial_cash = args.initial_cash if args.initial_cash is not None else cfg.get("execution.paper.starting_cash", 100000.0)
    margin_requirement = args.margin_requirement if args.margin_requirement is not None else 0.0

    portfolio: Dict[str, Any] = {
        "cash": initial_cash,
        "margin_requirement": margin_requirement,
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {
                "long": 0.0,
                "short": 0.0,
            }
            for ticker in tickers
        },
    }

    # Build and optionally export the agent graph
    workflow = create_workflow(selected_analysts)
    app = workflow.compile()
    if args.show_agent_graph:
        fp = "_".join(selected_analysts) + "_graph.png"
        save_graph_as_png(app, fp)

    # Run
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=args.show_reasoning,
        selected_analysts=selected_analysts,
        model_name=model_name,
        model_provider=model_provider,
    )
    print_trading_output(result)


if __name__ == "__main__":
    # Recommended: poetry run python -m src.main --config config/config.yaml
    main()
