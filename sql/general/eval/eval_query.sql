SELECT
    e.id,
    e.precision,
    e.recall,
    unsupported_count::text || '/' || (supported_count + unsupported_count)::text as hall,
    missing_count::text || '/' || (supported_count + missing_count)::text as miss,
    e.t_precision,
    e.t_recall,
    (supported_count + unsupported_count - matched_count)::text || '/' || (supported_count + unsupported_count)::text as t_hall,
    (reference_relation_count - matched_count)::text || '/' || reference_relation_count::text as t_miss,
    e.connectivity_score as connectivity
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
INNER JOIN graphs rg on e.reference_graph_id = rg.id
INNER JOIN articles a on a.id = g.article_id

-- supported_count = 40
-- unsupported_count = 1
-- missing_count = 10
-- jallucination_rate = 0.049
-- ommision_rate = 0.114
-- matched_count = 39
-- reference_relation_count = 44

-- hall. = unsupported_count "/" (supported_count + unsupported_count)
-- miss. = missing_count "/" (supported_count + missing_count)
--
-- t-hall. = (supported_count + unsupported_count - matched_count) "/" (supported_count + unsupported_count)
-- t-miss. = (reference_relation_count - matched_count) "/" reference_relation_count
