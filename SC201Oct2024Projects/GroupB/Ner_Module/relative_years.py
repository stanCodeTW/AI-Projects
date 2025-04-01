# relative_years.py

# Mapping of expressions indicating past years to the number of years before the current year
past_years_map = {
    "last year": 1, "the previous year": 1,
    "two years ago": 2, "three years ago": 3,
    "four years ago": 4, "five years ago": 5,
}

# Mapping of expressions indicating future years to negative values
# (relative to the current year; e.g., -1 means 1 year after now)
future_years_map = {
    "next year": -1, "one year later": -1, "in a year": -1,
    "two years later": -2, "in two years": -2,
    "three years later": -3, "in three years": -3,
    "four years later": -4, "in four years": -4,
    "in the future": -1, "future": -1,
    "the year after next": -2, "year after next": -2,
}

# Expose only the relevant variables for external use
__all__ = ["past_years_map", "future_years_map"]