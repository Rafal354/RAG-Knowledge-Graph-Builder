SELECT
    e.id,
    e.precision,
    e.recall,
    (unsupported_count::text || ' | ' || (supported_count + unsupported_count)::text)::text as hall,
    (missing_count::text || ' | ' || (supported_count + missing_count)::text)::text as miss,
    e.t_precision,
    e.t_recall,
    ((supported_count + unsupported_count - matched_count)::text || ' | ' || (supported_count + unsupported_count)::text)::text as t_hall,
    ((reference_relation_count - matched_count)::text || ' | ' || reference_relation_count::text)::text as t_miss,
    e.connectivity_score as connectivity
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
INNER JOIN graphs rg on e.reference_graph_id = rg.id
INNER JOIN articles a on a.id = g.article_id
