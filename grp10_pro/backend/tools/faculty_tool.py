# Faculty Tool Implementation

import pandas as pd

df = pd.read_csv("data/structured/faculty.csv")

def get_faculty(department):
    """
    Fetch faculty details by department
    """
    result = df[df["department"].str.lower() == department.lower()]

    if result.empty:
        return {"message": "No faculty found"}

    return result.to_dict(orient="records")
