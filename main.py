#!/usr/bin/env python3
"""CLI entry point for Soccer Practice Excel Generator."""

import argparse
import sys

from dotenv import load_dotenv

from src.agent import PracticeMenuAgent


def main():
    """Main entry point."""
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="サッカー練習メニューをExcelファイルで生成します",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py "4人でのパス練習"
  python main.py "シュート練習" -o shooting_practice.xlsx
  echo "守備練習" | python main.py

環境変数:
  OPENROUTER_API_KEY  OpenRouter APIキー（必須）
        """,
    )
    parser.add_argument(
        "challenge",
        nargs="?",
        help="練習課題（例: 「4人でのパス練習」）。省略時は標準入力から読み込み",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="practice_menu.xlsx",
        help="出力ファイル名（デフォルト: practice_menu.xlsx）",
    )

    args = parser.parse_args()

    # Get challenge from argument or stdin
    if args.challenge:
        challenge = args.challenge
    elif not sys.stdin.isatty():
        challenge = sys.stdin.read().strip()
    else:
        parser.print_help()
        print("\nエラー: 練習課題を指定してください", file=sys.stderr)
        sys.exit(1)

    if not challenge:
        print("エラー: 練習課題が空です", file=sys.stderr)
        sys.exit(1)

    try:
        # Create agent and generate practice menu
        agent = PracticeMenuAgent()
        output_path = agent.generate_practice_menu(challenge, args.output)
        print(f"\n🎉 練習メニューを生成しました: {output_path}")

    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        print("OPENROUTER_API_KEY環境変数を設定してください", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
