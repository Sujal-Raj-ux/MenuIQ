-- MenuIQ - verify the data survived the trip into Postgres (Phase 1, Step 2)
-- Run:  psql -d menuiq -f verify.sql
--
-- This recomputes the SAME planted pattern your generator printed as its answer
-- key (Lobster Roll -> Onion Rings). If the numbers match, your load worked and
-- the database is ready for Phase 2.
--
-- item_id 3 = Lobster Roll, item_id 4 = Onion Rings.

WITH
total AS (SELECT COUNT(DISTINCT order_id)::numeric AS n FROM order_lines),
lob   AS (SELECT COUNT(DISTINCT order_id)::numeric AS n FROM order_lines WHERE item_id = 3),
onion AS (SELECT COUNT(DISTINCT order_id)::numeric AS n FROM order_lines WHERE item_id = 4),
paired AS (
    SELECT COUNT(*)::numeric AS n FROM (
        SELECT order_id FROM order_lines WHERE item_id = 3
        INTERSECT
        SELECT order_id FROM order_lines WHERE item_id = 4
    ) shared
)
SELECT
    round((SELECT n FROM onion)  / (SELECT n FROM total), 3)       AS p_onion,
    round((SELECT n FROM paired) / (SELECT n FROM lob),   3)       AS p_onion_given_lobster,
    round(((SELECT n FROM paired) / (SELECT n FROM lob))
          / ((SELECT n FROM onion) / (SELECT n FROM total)), 1)    AS lift;

-- Bonus: a peek at every item's margin (the database computed this column for you).
SELECT name, price, food_cost, margin, category
FROM menu_items
ORDER BY margin DESC;