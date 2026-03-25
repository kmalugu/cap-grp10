# Calendar Tool Implementation

import pandas as pd

df = pd.read_csv("data/structured/academic_calendar.csv")

def get_calendar(program):
    """
    Fetch academic calendar for a program
    """
    result = df[df["program"].str.lower() == program.lower()]

    if result.empty:
        return {"message": "No calendar data found"}

    return result.to_dict(orient="records")