SELECT g.model, COUNT(g.model)
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
INNER JOIN graphs rg on e.reference_graph_id = rg.id
INNER JOIN articles a on a.id = g.article_id
WHERE e.prompt_key = 'filmweb_pl/new_graph'

AND e.id != 59 -- powtórka
AND e.id != 91 -- powtórka
GROUP BY g.model