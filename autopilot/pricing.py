import json
import requests


def estimate_monthly_cost(hourly_cost, hours=730, discount=1):
    return hourly_cost * hours * discount


def get_vm_price(sku_name, region):
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
