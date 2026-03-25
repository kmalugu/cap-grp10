# Fees Tool Implementation

import json

with open("data/structured/fees_scholarships.json") as f:
    data = json.load(f)

def get_fees(program, nationality="domestic"):
    """
    Fetch fee structure and scholarship info
    """
    program_data = data.get(program)

    if not program_data:
        return {"message": "Program not found"}

    result = program_data.get(nationality)

    if not result:
        return {"message": "Nationality data not found"}

    return result
