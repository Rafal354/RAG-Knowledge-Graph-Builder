class PromptService:
    def get_system_prompt(self) -> str:
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


    def get_prompt_for_new_graph(self, title: str, text: str) -> str:
        return f"""
    Build a NEW knowledge graph from the provided article.

    Article:
    {title}
    
    {text}
    """.strip()

    def get_prompt_for_existing_graph(self, title: str, text: str, graph: str) -> str:
        return f"""
    Extend the existing knowledge graph using the provided article.

    Article:
    {title}
    
    {text}

    Knowledge graph:
    {graph}
    """.strip()

prompt_service = PromptService()
