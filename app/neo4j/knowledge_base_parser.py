from dataclasses import dataclass
from typing import List


@dataclass
class Relation:
    source: str
    relation: str
    target: str


@dataclass
class KBParsed:
    entities: List[str]
    relations: List[Relation]


def parse(entities_text: str, relations_text: str) -> KBParsed:

    lines = [line.strip() for line in entities_text.splitlines()]
    entities: List[str] = []

    for line in lines:
        print(line)
        entities.append(line)

    lines = [line.strip() for line in relations_text.splitlines()]
    relations: List[Relation] = []

    for line in lines:
        print(line)
        parts = [p.strip() for p in line.split("->")]
        if len(parts) != 3:
            continue

        source, relation, target = parts
        relations.append(Relation(source=source, relation=relation, target=target))

    return KBParsed(entities=entities, relations=relations)
