"""CLI entry point — argparse with subcommands."""

import argparse
import sys

from mental_gym import __version__


HELP_TEXT = """
Mental Gym — AI-driven deliberate practice for domain expertise

COMMANDS
  init                 Set up a new domain (topic graph + knowledge base)
  train [--focus T]    Run a training session (warm-up -> main -> cool-down)
  warmup               Quick spaced-repetition review (~10 min)
  review <file>        Challenge yourself on claims in your own writing
  status               View topic mastery, upcoming reviews, session history
  sync                 Sync topic graph with knowledge base changes
  add-topic "NAME"     Add a new topic to your graph
  suggest              Context-aware training suggestion (auto-triggered by hooks)
  help                 Show this help page

EXERCISE TYPES
  Explain It Cold      Explain a concept from scratch, no references
  Predict Before Read  Predict study findings before seeing results
  Connect the Dots     Articulate relationships between concepts
  Defend or Attack     Steelman or critique a position (AI plays opponent)

CONFIGURATION
  Config file: mental_gym.yaml (created by `init`)
  Database:    data/mental_gym.db (SQLite, portable)
  LLM backend: anthropic-api | claude-cli | codex-cli

EXAMPLES
  mental-gym init --domain "social simulation" --knowledge-base ../wiki
  mental-gym train --focus "validation"
  mental-gym review papers/paper_draft.md
  mental-gym status
"""


def cmd_init(args):
    """Initialize Mental Gym for a domain."""
    from mental_gym.commands.init import run_init
    run_init(args)


def cmd_train(args):
    """Run a training session."""
    from mental_gym.commands.train import run_train
    run_train(args)


def cmd_warmup(args):
    """Quick spaced-repetition warm-up."""
    from mental_gym.commands.train import run_warmup
    run_warmup(args)


def cmd_status(args):
    """Show progress dashboard."""
    from mental_gym.commands.status import run_status
    run_status(args)


def cmd_review(args):
    """Review an article/writing piece."""
    from mental_gym.commands.review import run_review
    run_review(args)


def cmd_sync(args):
    """Sync knowledge base changes."""
    from mental_gym.commands.sync import run_sync
    run_sync(args)


def cmd_add_topic(args):
    """Add a new topic."""
    from mental_gym.commands.add_topic import run_add_topic
    run_add_topic(args)


def cmd_suggest(args):
    """Context-aware training suggestion."""
    from mental_gym.commands.suggest import run_suggest
    run_suggest(args)


def cmd_help(args):
    """Show detailed help."""
    print(HELP_TEXT)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mental-gym",
        description="AI-driven deliberate practice for domain expertise",
    )
    parser.add_argument(
        "--version", action="version", version=f"mental-gym {__version__}"
    )
    parser.add_argument(
        "--config", default="mental_gym.yaml",
        help="Path to config file (default: mental_gym.yaml)",
    )

    subs = parser.add_subparsers(dest="command")

    # init
    p_init = subs.add_parser("init", help="Set up a new domain")
    p_init.add_argument("--domain", required=True, help="Domain name")
    p_init.add_argument("--knowledge-base", help="Path to knowledge base directory")
    p_init.add_argument(
        "--backend", default="claude-cli",
        choices=["anthropic-api", "claude-cli", "codex-cli"],
        help="LLM backend (default: claude-cli)",
    )
    p_init.set_defaults(func=cmd_init)

    # train
    p_train = subs.add_parser("train", help="Run a training session")
    p_train.add_argument("--focus", help="Focus on a specific topic")
    p_train.set_defaults(func=cmd_train)

    # warmup
    p_warmup = subs.add_parser("warmup", help="Quick spaced-repetition review")
    p_warmup.set_defaults(func=cmd_warmup)

    # status
    p_status = subs.add_parser("status", help="View progress dashboard")
    p_status.set_defaults(func=cmd_status)

    # review
    p_review = subs.add_parser("review", help="Challenge yourself on your own writing")
    p_review.add_argument("file", help="Path to markdown/text file to review")
    p_review.set_defaults(func=cmd_review)

    # sync
    p_sync = subs.add_parser("sync", help="Sync knowledge base changes")
    p_sync.set_defaults(func=cmd_sync)

    # add-topic
    p_add = subs.add_parser("add-topic", help="Add a new topic")
    p_add.add_argument("name", help="Topic name")
    p_add.set_defaults(func=cmd_add_topic)

    # suggest
    p_suggest = subs.add_parser("suggest", help="Context-aware training suggestion")
    p_suggest.add_argument("--changed-file", help="File that triggered the suggestion")
    p_suggest.set_defaults(func=cmd_suggest)

    # help
    p_help = subs.add_parser("help", help="Show detailed help")
    p_help.set_defaults(func=cmd_help)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        # No command: show help
        print(HELP_TEXT)
        sys.exit(0)

    args.func(args)
