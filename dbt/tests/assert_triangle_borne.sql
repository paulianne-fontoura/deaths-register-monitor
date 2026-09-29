-- The completeness share is a ratio of cumulative arrivals over the
-- current total of the same month, both on the canonical grain, so it
-- must live in ]0, 1] by construction. This test proves the construction
-- on the published table: a row outside the bound means the grain or the
-- knowledge axis broke.

select
    triangle_id,
    part_connue
from {{ ref('fct_completeness_triangle') }}
where part_connue <= 0 or part_connue > 1 or n_connus <= 0
