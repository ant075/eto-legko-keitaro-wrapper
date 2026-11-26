def offer_map(response) -> dict[int, dict]:
    return {item["offer_id"]: item for item in response.json()["offers"]}
