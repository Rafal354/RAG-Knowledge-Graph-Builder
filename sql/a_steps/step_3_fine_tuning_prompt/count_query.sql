SELECT g.model, COUNT(g.model)
FROM evaluations e
INNER JOIN graphs g on e.graph_id = g.id
INNER JOIN graphs rg on e.reference_graph_id = rg.id
INNER JOIN articles a on a.id = g.article_id
WHERE (
    e.prompt_key = 'default_pl/new_graph' OR
    e.prompt_key = 'typed_pl/new_graph' OR
    e.prompt_key = 'filmweb_pl/new_graph'
          )
AND (
    g.model = 'google/gemma-4-26b-a4b-it' OR
    g.model = 'google/gemma-4-31b-it' OR
    g.model = 'mistralai/mistral-small-3.2-24b-instruct' OR
    g.model = 'qwen3-30b-a3b-instruct-2507' OR
    g.model = 'qwen3-32b' OR
    g.model = 'local:bielik-11b-v3.0-instruct' OR
    g.model = 'local:qwen/qwen3-vl-8b' OR
    g.model = 'qwen3-14b'
    )

AND (
    a.title = 'Langer_serial_SkyShowtime' OR
    a.title = 'Wladcy_Pierscieni_Pierscienie_Wladzy_nowi_aktorzy' OR
    a.title = 'The_Last_of_Us_odcinek_5_tworcy_o_szokujacych_scenach'
    )

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
AND e.id != 59 -- powtórka
AND e.id != 91 -- powtórka
AND e.id > 90 -- powtórka

GROUP BY g.model
