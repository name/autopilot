import json
import requests
from functools import lru_cache


def estimate_monthly_cost(hourly_cost, hours=730, discount=1):
    return hourly_cost * hours * discount


def estimate_monthly_storage_cost(size_in_gb, disk_tier):
    # Calculate the actual cost per GB for StandardSSD_LRS
    actual_cost_per_gb_standardssd_lrs = 8.70 / 127
    actual_cost_per_gb_standard_lrs = 1.40 / 32

    # Define cost per GB for each tier
    tier_costs = {
        "StandardSSD_LRS": actual_cost_per_gb_standardssd_lrs,  # Updated cost per GB
        "Standard_LRS": actual_cost_per_gb_standard_lrs,  # £1.40 per month for 32 GiB
        "Premium_LRS": 0.077,  # £0.077 per GiB
    }

    # Get the cost per GB for the specified disk tier
    cost_per_gb = tier_costs.get(disk_tier)

    # If the disk tier is not recognized, return None or raise an error
    if cost_per_gb is None:
        print(f"Unknown disk tier: {disk_tier}")
        return None

    # Calculate and return the monthly cost
    return size_in_gb * cost_per_gb


@lru_cache(maxsize=128)  # Cache up to 128 different (sku_name, region) combinations
def get_resource_price(sku_name, region):
    api_url = "https://prices.azure.com/api/retail/prices"
    params = {
        "currencyCode": "GBP",
        "api-version": "2023-01-01-preview",
        "$filter": f"serviceFamily eq 'Compute' and armSkuName eq '{sku_name}' and armRegionName eq '{region}' and priceType eq 'Consumption'",
    }

    response = requests.get(api_url, params=params)

    # Check for rate limit headers
    if "X-Ratelimit-Limit" in response.headers:
        limit = response.headers["X-Ratelimit-Limit"]
        remaining = response.headers["X-Ratelimit-Remaining"]
        reset_time = response.headers["X-Ratelimit-Reset"]

        print(f"Rate Limit: {limit}")
        print(f"Remaining Requests: {remaining}")
        print(f"Reset Time (UTC): {reset_time}")

    try:
        json_data = json.loads(response.text)
    except json.JSONDecodeError:
        print("Error decoding JSON response.")
        return None

    if "Items" in json_data and json_data["Items"]:
        for item in json_data["Items"]:
            if (
                item["armSkuName"].lower() == sku_name.lower()
                and item["armRegionName"].lower() == region.lower()
            ):
                return float(item["retailPrice"])
    elif "Error" in json_data:
        # Rate limit exceeded
        print(json_data.get("Error").get("Message"))
        exit(1)
    else:
        print("No pricing data found for the specified SKU and Region.")

    return None
