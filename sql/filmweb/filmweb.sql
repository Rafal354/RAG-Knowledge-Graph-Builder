SELECT
    rg.position,
    e.id,
    a.title,
    g.model,
    e.prompt_key,
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
WHERE e.prompt_key = 'filmweb_pl/new_graph'

AND (
    a.title = 'Langer_serial_SkyShowtime' OR
    a.title = 'Wladcy_Pierscieni_Pierscienie_Wladzy_nowi_aktorzy' OR
    a.title = 'The_Last_of_Us_odcinek_5_tworcy_o_szokujacych_scenach'
    )

AND e.id != 59 -- powtórka
AND e.id != 91 -- powtórka
AND e.id > 90 -- powtórka

ORDER BY g.model, a.title
