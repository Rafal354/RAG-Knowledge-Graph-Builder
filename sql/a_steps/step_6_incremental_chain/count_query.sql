SELECT e.prompt_key, g.model, COUNT(*)
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
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
AND e.unique_entities IS NOT NULL

AND e.id != 301 -- powtórka (duplikat id 302, ten sam graph_id 1088)
AND e.id != 291 -- Opus, druga (niewykorzystana dalej) referencja

GROUP BY e.prompt_key, g.model
ORDER BY e.prompt_key, g.model
