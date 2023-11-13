from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resource.subscriptions import SubscriptionClient
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
import json
import pricing

CONFIG_FILE = "autopilot.json"


def list():
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


def list_costs():
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
    resource_client = ResourceManagementClient(credential, active_sub)

    print(f"Listing resources for subscription: {active_sub}")

    total_monthly_cost = 0
    total_minimum_cost = 0
    total_maximum_cost = 0
    total_monthly_cost_with_savings = 0
    total_minimum_cost_with_savings = 0
    total_maximum_cost_with_savings = 0

    print(f"Compute resources:")

    for vm in compute_client.virtual_machines.list_all():
        vm_size = vm.hardware_profile.vm_size
        region = vm.location
        hourly_cost = pricing.get_vm_price(vm_size, region)
        if "AVD" in vm.name:
            monthly_cost = pricing.estimate_monthly_cost(hourly_cost, hours=200)
            minimum_cost = pricing.estimate_monthly_cost(hourly_cost, hours=100)
            maximum_cost = pricing.estimate_monthly_cost(hourly_cost, hours=730)
            monthly_cost_with_savings = pricing.estimate_monthly_cost(
                hourly_cost, hours=200, discount=0.87
            )
            minimum_cost_with_savings = pricing.estimate_monthly_cost(
                hourly_cost, hours=100, discount=0.87
            )
            maximum_cost_with_savings = pricing.estimate_monthly_cost(
                hourly_cost, hours=730, discount=0.87
            )
        else:
            monthly_cost = pricing.estimate_monthly_cost(hourly_cost)
            minimum_cost = pricing.estimate_monthly_cost(hourly_cost)
            maximum_cost = pricing.estimate_monthly_cost(hourly_cost)
            monthly_cost_with_savings = pricing.estimate_monthly_cost(
                hourly_cost, discount=0.60
            )
            minimum_cost_with_savings = pricing.estimate_monthly_cost(
                hourly_cost, discount=0.60
            )
            maximum_cost_with_savings = pricing.estimate_monthly_cost(
                hourly_cost, discount=0.60
            )
        total_minimum_cost += minimum_cost
        total_maximum_cost += maximum_cost
        total_monthly_cost += monthly_cost
        total_minimum_cost_with_savings += minimum_cost_with_savings
        total_maximum_cost_with_savings += maximum_cost_with_savings
        total_monthly_cost_with_savings += monthly_cost_with_savings
        print(f"- Name: {vm.name} ({vm_size})")
        print(f"  - Hourly Cost: \u00A3{hourly_cost:.2f}")
        print(f"  - Monthly Cost: \u00A3{monthly_cost:.2f}")
        if "AVD" in vm.name:
            print(f"  - Minimum Cost: \u00A3{minimum_cost:.2f}")
            print(f"  - Maximum Cost: \u00A3{maximum_cost:.2f}")

    print(
        f"Minimum Monthly Cost for all VMs: \u00A3{total_minimum_cost:.2f} | \u00A3{total_minimum_cost_with_savings:.2f} with savings"
    )
    print(
        f"Maximum Monthly Cost for all VMs: \u00A3{total_maximum_cost:.2f} | \u00A3{total_maximum_cost_with_savings:.2f} with savings"
    )
    print(
        f"Total Estimated Cost per Month for all VMs (AVDs: 200hrs): \u00A3{total_monthly_cost:.2f} | \u00A3{total_monthly_cost_with_savings:.2f} with savings"
    )
