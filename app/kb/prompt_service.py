def get_prompt_for_existing_graph(title: str, text: str, graph: str) -> str:
    return f"""
Update the existing knowledge graph using the new article below.

The result should represent a merged and consistent knowledge graph based on:
- the existing graph
- the new article

The output should not be based only on the new article.
It should reflect the combined knowledge from both sources.

Return the result exactly in this format:

[ENTITIES]
entity_1
entity_2

[RELATIONS]
entity_1 -> relation -> entity_2

Existing knowledge graph:
{graph}

Article title:
{title}

Article text:
{text}
""".strip()


def get_prompt_for_new_graph(title: str, text: str) -> str:
    return f"""
Build a knowledge graph from the article below.

Extract entities and relations mentioned in the text.

Return the result exactly in this format:

[ENTITIES]
entity_1
entity_2

[RELATIONS]
entity_1 -> relation -> entity_2

Article title:
{title}

Article text:
{text}
""".strip()


def get_system_prompt() -> str:
    return """
You are a knowledge extraction system.

Your job is to extract entities and relationships from text and represent them in a structured format.

Output format must strictly follow:

[ENTITIES]
entity_1
entity_2

[RELATIONS]
entity_1 -> relation -> entity_2
""".strip()
