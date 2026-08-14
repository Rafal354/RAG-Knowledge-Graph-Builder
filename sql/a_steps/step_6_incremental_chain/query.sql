SELECT e.prompt_key,
       rg.position                                                                                         as ref_position,
       g.position,
       e.id,
       g.title,
       g.model,
       e.precision,
       e.recall,
       (unsupported_count::text || ' | ' || (supported_count + unsupported_count)::text)::text             as hall,
       (missing_count::text || ' | ' || (supported_count + missing_count)::text)::text                     as miss,
       e.t_precision,
       e.t_recall,
       ((supported_count + unsupported_count - matched_count)::text || ' | ' ||
        (supported_count + unsupported_count)::text)::text                                                 as t_hall,
       ((reference_relation_count - matched_count)::text || ' | ' || reference_relation_count::text)::text as t_miss,
       e.connectivity_score                                                                                as connectivity,
       e.unique_entities,
       e.reference_unique_entities,
       (e.unique_entities - e.reference_unique_entities)                                                   as ref_ent_diff,
       e.self_duplicate_relations,
       e.self_duplicate_rate,
       e.merge_new_candidate_count,
       e.merge_dropped_count,
       e.merge_drop_rate
FROM evaluations e
         INNER JOIN graphs g on e.graph_id = g.id
         LEFT JOIN graphs rg on e.reference_graph_id = rg.id
WHERE e.prompt_key IN (
                       'technology/new_graph',
                       'konferencja_pl/new_graph',
                       'sport_pl/new_graph'
    )
  AND (
    g.model = 'claude-opus-4-6' OR
    g.model = 'qwen3-32b' OR
    g.model = 'google/gemma-4-26b-a4b-it' OR
    g.model = 'google/gemma-4-31b-it' OR
    g.model = 'mistralai/mistral-small-3.2-24b-instruct'
    )
  AND e.unique_entities IS NOT NULL -- tylko ewaluacje scenariusza przyrostowego (use_article_chain=True), nie pojedyncze artykuły z tym samym prompt_key

  AND e.id != 301                   -- powtórka (duplikat id 302, ten sam graph_id 1088)
  AND e.id != 291                   -- Opus, druga (niewykorzystana dalej) referencja - graph 974 oceniany względem 988, a nie odwrotnie jak w reszcie porównania

ORDER BY e.prompt_key, g.model;

