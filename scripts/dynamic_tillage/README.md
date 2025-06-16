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

## SQL

    with scen as (
        select huc_12, extract(week from valid) as datum, sum(avg_loss) from results_by_huc12 where scenario = 171 and valid < '2025-01-01'
        group by huc_12, datum),
    prod as (
        select huc_12, extract(week from valid) as datum, sum(avg_loss) from results_by_huc12 where scenario = 0 and valid < '2025-01-01'
        group by huc_12, datum),
    agg as (
        select s.huc_12, s.datum, s.sum as scen_sum, p.sum as p_sum from scen s
        JOIN prod p on (s.huc_12 = p.huc_12 and s.datum = p.datum)),
    agg2 as (
        select datum, sum(scen_sum) as ss, sum(p_sum) as ps from agg
        GROUP by datum order by datum)
    select '2020-01-01'::date + (datum - 1) * '7 days'::interval, ss, ps,
    (ps - ss) / ss * 100. as ratio from agg2 order by datum;

Mud it in report

    with myfields as (
        select f.scenario, f.isag, field_id, acres from fields f JOIN huc12 h
        on (f.huc12 = h.huc_12) WHERE f.scenario = 0 and h.scenario = 0 and
        (h.states = 'IA' or h.states = 'MN'))
    select year, sum(case when to_char(plant, 'mmdd') >= '0611'
    then acres else 0 end) / 1e7, sum(acres) / 1e7 from
    myfields f JOIN field_operations o on (f.field_id = o.field_id)
    WHERE f.scenario = 0 and f.isag > 0 group by year order by year;
