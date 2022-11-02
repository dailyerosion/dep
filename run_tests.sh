# Run Tests!

coverage run --source=scripts -m pytest \
    scripts/cligen/daily_clifile_editor.py \
    scripts/cligen/arb_precip_delta.py \
    scripts/RT/env2database.py \
    scripts/import/flowpath_importer.py
