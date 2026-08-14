SELECT g.model, COUNT(g.model)
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
INNER JOIN graphs rg on e.reference_graph_id = rg.id
INNER JOIN articles a on a.id = g.article_id
WHERE e.prompt_key = 'default_pl/new_graph'

AND e.id != 101 -- powtórka
AND e.id != 102 -- powtórka
AND e.id != 104 -- powtórka
AND e.id != 105 -- powtórka
AND e.id != 106 -- powtórka
AND e.id != 107 -- powtórka
AND e.id != 109 -- powtórka
AND e.id != 120 -- powtórka
AND e.id != 96 -- powtórka
AND e.id != 97 -- powtórka
AND e.id != 98 -- powtórka
AND e.id != 99 -- powtórka
AND e.id != 100 -- powtórka
AND g.model != 'openai/gpt-oss-20b' -- nieobsługiwany model

GROUP BY g.model
