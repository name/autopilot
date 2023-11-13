import argparse
import subscriptions
import resources
import pricing


def main():
    parser = argparse.ArgumentParser(description="Azure CLI tool")
    subparsers = parser.add_subparsers(dest="command")

    # Login parser
    login_parser = subparsers.add_parser(
        "login", help="Log in to Azure and list subscriptions"
    )

    # Subscription parser
    subscription_parser = subparsers.add_parser(
        "subscription", help="Manage Azure subscriptions"
    )
    subscription_parser.add_argument(
        "--set",
        metavar="SUBSCRIPTION_ID",
        type=str,
        help="Set an active Azure subscription",
    )

    # Resources parser
    resources_parser = subparsers.add_parser(
        "resources", help="List all resources in the current subscription"
    )
    resources_parser.add_argument(
        "--cost",
        help="Estimate monthly cost of all resources in the current subscription",
        type=bool,
        metavar="COST",
    )

    args = parser.parse_args()

    if args.command == "login":
        subscriptions.login()
    elif args.command == "subscription":
        if args.set:
            subscriptions.set_subscription(args.set)
    elif args.command == "resources":
        if args.cost:
            resources.list_costs()
        else:
            resources.list()


if __name__ == "__main__":
    main()
