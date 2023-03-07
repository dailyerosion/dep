# DEP Dynamic Tillage

Presently, tillage and planting operations are hard coded within the DEP input
database.  The intention is to make these data-driven and thus dynamic with the
hope of being 'operational' for the 2023 planting season.

## Daily closure

Life choices are necessary to make the logic work out.  The chicken/egg issue
is that precipitation on a given date impacts the 'next day' DEP output. So
we need to "look ahead" and guess what could have happened for tomorrow. The
timing looks like then:

    - April 15th is the arbitrary start date?
    - At 9 PM, we produce a simple rainfall analyses and pick an arbitrary
threshold of `10mm`(?) that will exclude any OFEs from receiving an operation.
    - We then need to consider a soil moisture state, but maybe we just use a
bucket model and figure out cells/fields without substancial rain over 4 days?
    - From previous processing, we have a list of OFEs that are needing to have
a given operation (tillage or planting) done.  By total `isAG` acreage, we
randomly pick ~10% of OFEs/fields to receive a tillage operation and ~10% of
different fields to receive a planting operation.
    - On 1 June, we panic and mud everything in on sequential days?
    - `prj2wepp` is run and is completed by midnight.

## Database / data needs

For each field with a given `acres` size and `isAG`, we construct a list of
tillage and planting operations needed that year.  These entries are ordered
with some key that makes them implemented sequentially.  Only one operation
can happen per day.

If the field is picked for an operation, the database is updated with a date
for that operation.  Since WEPP needs a full year to run, we just manually hack
in the remaining operations for dates in the future.
