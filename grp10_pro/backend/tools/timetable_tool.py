# Timetable Tool Implementation

import pandas as pd

df = pd.read_csv("data/structured/timetable.csv")

def get_timetable(year, department):
    """
    Fetch timetable based on year and department
    """
    result = df[
        (df["year"] == year) &
        (df["department"].str.lower() == department.lower())
    ]

    if result.empty:
        return {"message": "No timetable found"}

    return result.to_dict(orient="records")