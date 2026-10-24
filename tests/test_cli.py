from seo_warehouse_demo.cli import build_parser


def test_cli_requires_a_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["validate", "data/demo_search_performance.csv"])
    assert args.command == "validate"
