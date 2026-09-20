"""Execute Project Aether evaluation as a package."""

import argparse

from .evaluator import main


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="print the evaluation report as a Markdown table",
    )
    args = parser.parse_args()
    main(markdown=args.markdown)
