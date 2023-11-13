import json
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resource.subscriptions import SubscriptionClient


CONFIG_FILE = "autopilot.json"


def login():
    credential = InteractiveBrowserCredential()
    subscription_client = SubscriptionClient(credential)

    print("Available subscriptions:")
    subscriptions = subscription_client.subscriptions.list()
    for sub in subscriptions:
        print(f"- {sub.subscription_id} ({sub.display_name})")

    # Attempt to read the active subscription from config file
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            active_sub = config.get("active_subscription", None)
            if active_sub:
                print(f"Active subscription: {active_sub}")
    except FileNotFoundError:
        print(
            "No active subscription set. Use the 'subscription --set' command to set one."
        )


def set_subscription(subscription_id):
    credential = InteractiveBrowserCredential()
    subscription_client = SubscriptionClient(credential)

    # Check if subscription exists
    subscriptions = subscription_client.subscriptions.list()
    if any(sub.subscription_id == subscription_id for sub in subscriptions):
        # Save the subscription ID to the config file
        with open(CONFIG_FILE, "w") as f:
            json.dump({"active_subscription": subscription_id}, f)
        print(f"Subscription set to {subscription_id}")
    else:
        print(f"No subscription found with ID: {subscription_id}")
