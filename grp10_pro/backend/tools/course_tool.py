# Course Tool Implementation
import pandas as pd

df = pd.read_csv("data/structured/course_catalog.csv")

def get_course(course_code):
    """
    Fetch course details by course code
    """
    result = df[df["course_code"].str.lower() == course_code.lower()]

    if result.empty:
        return {"message": "Course not found"}

    return result.to_dict(orient="records")