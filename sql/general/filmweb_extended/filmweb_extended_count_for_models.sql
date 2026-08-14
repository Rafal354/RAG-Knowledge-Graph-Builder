SELECT g.model, COUNT(g.model)
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
INNER JOIN graphs rg on e.reference_graph_id = rg.id
INNER JOIN articles a on a.id = g.article_id
WHERE e.prompt_key = 'filmweb_pl/new_graph'

AND (
    g.model = 'qwen3-32b' OR
    g.model = 'google/gemma-4-26b-a4b-it' OR
    g.model = 'google/gemma-4-31b-it' OR
    g.model = 'mistralai/mistral-small-3.2-24b-instruct'
    )

AND e.id != 59 -- powtórka
AND e.id != 91 -- powtórka
AND e.id != 170 -- powtórka
AND e.id != 179 -- powtórka
AND e.id != 187 -- powtórka
AND e.id != 167 -- powtórka
AND e.id != 176 -- powtórka
AND e.id != 184 -- powtórka
AND e.id != 168 -- powtórka
AND e.id != 177 -- powtórka
AND e.id != 185 -- powtórka
AND e.id != 169 -- powtórka
AND e.id != 178 -- powtórka
AND e.id != 186 -- powtórka

GROUP BY g.model
