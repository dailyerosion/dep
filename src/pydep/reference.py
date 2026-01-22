"""pydep static reference data."""

# Classification of slope % into classes (right inclusive)
SLOPE_CLASSES = [-99, 2, 4, 6, 12]

# Classification of soil kwfact into classes (right inclusive)
KWFACT_CLASSES = [-99, 0.28, 0.32]

# Spacing of our precip grid
GRID_SPACING = 0.01

# Conversion of kg/m2 to ton/acre, verbatim from what pint reports
KG_M2_TO_TON_ACRE = 4.46091345

# 9 values for 8 colors on the website
# NB: Keep the lowest value just above zero so that plots always show data
RAMPS = {
    "english": [
        [0.01, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 3.0, 5.0],
        [0.01, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0],
        [0.01, 1.0, 2.0, 5.0, 7.0, 10.0, 20.0, 30.0, 40.0],
    ],
    "metric": [
        [0.25, 1.0, 10.0, 15.0, 25.0, 35.0, 50.0, 100.0, 200.0],
        [0.25, 2.0, 20.0, 30.0, 50.0, 70.0, 100.0, 200.0, 400.0],
        [0.25, 25.0, 50.0, 125.0, 200.0, 300.0, 500.0, 750.0, 1000.0],
    ],
}
