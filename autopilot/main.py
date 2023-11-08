#!/usr/bin/env python3
import argparse
import os
import json
import requests
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient


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


def list_resources():
    # Load active subscription from config file
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            active_sub = config.get("active_subscription")
            if not active_sub:
                print(
                    "No active subscription set. Set one using the 'subscription --set' command."
                )
                return
    except FileNotFoundError:
        print(
            "Config file not found. Set an active subscription using the 'subscription --set' command."
        )
        return

    credential = InteractiveBrowserCredential()
    resource_client = ResourceManagementClient(credential, active_sub)

    print(f"Listing resources for subscription: {active_sub}")

    resource_dict = {}

    for resource_group in resource_client.resource_groups.list():
        resource_dict[resource_group.name] = []
        for resource in resource_client.resources.list_by_resource_group(
            resource_group.name
        ):
            resource_dict[resource_group.name].append((resource.type, resource.name))

    # Sort the resource groups
    sorted_resource_groups = sorted(resource_dict.keys(), key=lambda x: x.lower())

    for rg_name in sorted_resource_groups:
        print(f"- Resource Group: {rg_name}")
        sorted_resources = sorted(
            resource_dict[rg_name], key=lambda x: (x[0].lower(), x[1].lower())
        )
        for r_type, r_name in sorted_resources:
            print(f"  - {r_type}: {r_name}")


def get_vm_pricing_details(sku_name, region):
    api_url = "https://prices.azure.com/api/retail/prices"
    params = {
        "currencyCode": "GBP",
        "api-version": "2023-01-01-preview",
        "$filter": f"serviceFamily eq 'Compute' and armSkuName eq '{sku_name}' and armRegionName eq 'uksouth' and priceType eq 'Consumption'",
    }
    # print(f"Fetching pricing for SKU: {sku_name} in Region: {region}")
    response = requests.get(api_url, params=params)
    json_data = json.loads(response.text)

    # Debugging the fetched pricing data:
    if json_data["Items"]:
        for item in json_data["Items"]:
            # print(f"Found price item: SKU: {item['armSkuName']}, Price: {item['retailPrice']}")
            if (
                item["armSkuName"].lower() == sku_name.lower()
                and item["armRegionName"].lower() == region.lower()
            ):
                return float(item["retailPrice"])
    else:
        print("No pricing data found for the specified SKU and Region.")

    # Handle the case where no matching price was found
    return None


def get_resource_pricing(resource_type, sku_name, region):
    # This needs to be adapted based on the resource type because the filters
    # you might need to use could be different for different types of resources
    api_url = "https://prices.azure.com/api/retail/prices"
    params = {
        "currencyCode": "GBP",
        "api-version": "2023-01-01-preview",
        "$filter": f"serviceFamily eq '{resource_type}' and armSkuName eq '{sku_name}' and armRegionName eq '{region}' and priceType eq 'Consumption'",
    }
    response = requests.get(api_url, params=params)
    json_data = json.loads(response.text)

    # Here we return the first matched item, but in real scenario you might want to handle multiple matches
    if json_data["Items"]:
        return json_data["Items"][0]["retailPrice"]

    # Handle the case where no pricing data was found
    return None


def estimate_monthly_cost(hourly_cost):
    return hourly_cost * 720


def list_vms():
    # Load active subscription
    try:
        with open(CONFIG_FILE, "r") as config_file:
            config = json.load(config_file)
            active_sub = config.get("active_subscription")
    except FileNotFoundError as e:
        print(f"Required file not found: {e}")
        return

    if not active_sub:
        print("No active subscription set. Use the 'subscription --set' command first.")
        return

    credential = InteractiveBrowserCredential()
    compute_client = ComputeManagementClient(credential, active_sub)

    total_monthly_cost = 0
    for vm in compute_client.virtual_machines.list_all():
        vm_size = vm.hardware_profile.vm_size
        region = "uksouth"
        hourly_cost = get_vm_pricing_details(vm_size, region)
        monthly_cost = estimate_monthly_cost(hourly_cost)
        total_monthly_cost += monthly_cost

        print(f"- VM Name: {vm.name}")
        print(f"  Size: {vm_size}")
        print(f"  Estimated Cost per Hour: ${hourly_cost:.2f}")
        print(f"  Estimated Cost per Month (720 hours): ${monthly_cost:.2f}")

    print(f"\nTotal Estimated Cost per Month for all VMs: ${total_monthly_cost:.2f}")


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

    # VM parser
    vm_parser = subparsers.add_parser("vm", help="Manage Azure virtual machines")

    args = parser.parse_args()

    if args.command == "login":
        login()
    elif args.command == "subscription":
        if args.set:
            set_subscription(args.set)
    elif args.command == "resources":
        list_resources()
    elif args.command == "vm":
        list_vms()


if __name__ == "__main__":
    main()
