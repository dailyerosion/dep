"""pydep static reference data."""

# Classification of slope % into classes (right inclusive)
SLOPE_CLASSES = [-99, 2, 4, 6, 12]

# Classification of soil kwfact into classes (right inclusive)
KWFACT_CLASSES = [-99, 0.28, 0.32]

# Spacing of our precip grid
GRID_SPACING = 0.01

# Conversion of kg/m2 to ton/acre, verbatim from what pint reports
KG_M2_TO_TON_ACRE = 4.46091345
