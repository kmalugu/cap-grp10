# Map Tool Implementation
import json

with open("data/structured/campus_map.json") as f:
    data = json.load(f)

def get_location(place_name):
    """
    Fetch campus location details
    """
    for location in data["locations"]:
        if location["name"].lower() == place_name.lower():
            return {
                "name": location["name"],
                "description": location["description"],
                "map_link": f"https://www.google.com/maps/search/?api=1&query={location['coordinates']}"
            }

    return {"message": "Location not found"}