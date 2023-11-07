import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Autopilot CLI for Azure cost optimization."
    )
    parser.add_argument("config", help="Path to the configuration file")

    args = parser.parse_args()
    config_path = args.config

    print(f"Hello! You've provided the following config path: {config_path}")


if __name__ == "__main__":
    main()
