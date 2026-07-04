SELECT g.model, COUNT(g.model)
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

GROUP BY g.model
