import json
import logging

import numpy as np
from pydantic import BaseModel, field_validator
from scipy.optimize import linear_sum_assignment

logger = logging.getLogger(__name__)

# Bumped whenever the judge prompt's evaluation criteria (point 1, "supported" rubric) change,
# so saved evaluations can be traced back to the rubric version that produced them.
# v1: "semantically supported, paraphrases count as supported"
# v2: added entity/relation-type/direction fidelity checks
JUDGE_PROMPT_VERSION = 2


class TripleVerdict(BaseModel):
    triple: str
    supported: bool
    comment: str | None = None


class JudgeOutput(BaseModel):
    triple_verdicts: list[TripleVerdict]
    missing_important_relations: list[str] = []
    analysis: str = ""

    @field_validator("triple_verdicts", mode="before")
    @classmethod
    def _parse_triple_verdicts(cls, v):
        if isinstance(v, str):
            from json_repair import repair_json
            v = json.loads(repair_json(v))
        if isinstance(v, list):
            flat = []
            for item in v:
                if isinstance(item, list):
                    flat.extend(item)
                elif isinstance(item, str):
                    pass  # misplaced missing-relation string — discard
                else:
                    flat.append(item)
            return flat
        return v

    @field_validator("missing_important_relations", mode="before")
    @classmethod
    def _parse_missing_relations(cls, v):
        if isinstance(v, str):
            from json_repair import repair_json
            v = json.loads(repair_json(v))
        if isinstance(v, list):
            flat = []
            for item in v:
                if isinstance(item, list):
                    flat.extend(item)
                else:
                    flat.append(item)
            return flat
        return v


class EvaluationResult(BaseModel):
    graph_id: int
    graph_relations: int
    eval_model: str
    precision: float
    recall: float
    f1: float
    supported_count: int
    unsupported_count: int
    missing_count: int
    triple_verdicts: list[dict]
    missing_relations: list[str]
    analysis: str
    connectivity_score: float | None = None
    reference_graph_id: int | None = None
    t_precision: float | None = None
    t_recall: float | None = None
    t_f1: float | None = None
    hallucination_rate: float | None = None
    omission_rate: float | None = None
    ged: int | None = None
    matched_count: int | None = None
    reference_relation_count: int | None = None
    judge_prompt_version: int | None = None
    judge_prompt_text: str | None = None


def _compute_connectivity_score(graph) -> float:
    import networkx as nx
    G = nx.Graph()
    for r in graph.relations:
        G.add_edge(r.entity_1, r.entity_2)
    if len(G.nodes) == 0:
        return 0.0
    largest = max(nx.connected_components(G), key=len)
    score = len(largest) / len(G.nodes)
    logger.info("Connectivity score for graph_id=%d: %.3f (%d/%d nodes in largest component)",
                graph.id, score, len(largest), len(G.nodes))
    return round(score, 3)


def _graph_to_text(graph) -> str:
    return "\n".join(
        f"{r.entity_1} -> {r.relation} -> {r.entity_2}"
        for r in graph.relations
    )


import re as _re

_QUOTE_CHARS = frozenset([0x201c, 0x201d, 0x201e, 0x2018, 0x2019, 0x00ab, 0x00bb, 0x22, 0x27])
_WS_RE = _re.compile(r"\s+")


def _normalize_str(s: str) -> str:
    s = s.lower().strip()
    s = "".join(c for c in s if ord(c) not in _QUOTE_CHARS)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _normalize_triple(r) -> tuple:
    return (_normalize_str(r.entity_1), _normalize_str(r.relation), _normalize_str(r.entity_2))


_EMBED_MODEL = None


def _get_embed_model():
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
        logger.info("Sentence embedding model loaded")
    return _EMBED_MODEL


def _triple_str(t: tuple) -> str:
    return t[0] + " -> " + t[1] + " -> " + t[2]


def _semantic_match(predicted: list, reference: list, threshold: float = 0.75):
    if not predicted or not reference:
        return 0, set(), set(range(len(reference)))

    model = _get_embed_model()
    pred_texts = [_triple_str(t) for t in predicted]
    ref_texts = [_triple_str(t) for t in reference]
    pred_emb = model.encode(pred_texts, convert_to_numpy=True, show_progress_bar=False)
    ref_emb = model.encode(ref_texts, convert_to_numpy=True, show_progress_bar=False)
    pred_norm = pred_emb / (np.linalg.norm(pred_emb, axis=1, keepdims=True) + 1e-9)
    ref_norm = ref_emb / (np.linalg.norm(ref_emb, axis=1, keepdims=True) + 1e-9)
    sim_matrix = pred_norm @ ref_norm.T
    row_ind, col_ind = linear_sum_assignment(-sim_matrix)
    matched_pred = set()
    matched_ref = set()
    for r, c in zip(row_ind, col_ind):
        score = float(sim_matrix[r, c])
        if score >= threshold:
            matched_pred.add(r)
            matched_ref.add(c)
    unmatched_pred = set(range(len(predicted))) - matched_pred
    unmatched_ref = set(range(len(reference))) - matched_ref
    return len(matched_pred), unmatched_pred, unmatched_ref


def _compute_reference_metrics(graph, reference_graph) -> dict:
    predicted = [_normalize_triple(r) for r in graph.relations]
    reference = [_normalize_triple(r) for r in reference_graph.relations]

    matched, unmatched_pred_idx, unmatched_ref_idx = _semantic_match(predicted, reference)

    t_precision = matched / len(predicted) if predicted else 0.0
    t_recall = matched / len(reference) if reference else 0.0
    t_f1 = (
        2 * t_precision * t_recall / (t_precision + t_recall)
        if (t_precision + t_recall) > 0 else 0.0
    )
    hallucination_rate = 1.0 - t_precision
    omission_rate = 1.0 - t_recall

    predicted_set = set(predicted)
    reference_set = set(reference)
    predicted_nodes = {t[0] for t in predicted_set} | {t[2] for t in predicted_set}
    reference_nodes = {t[0] for t in reference_set} | {t[2] for t in reference_set}
    ged = len(predicted_set.symmetric_difference(reference_set)) + len(
        predicted_nodes.symmetric_difference(reference_nodes)
    )

    logger.info(
        "Reference graph comparison: graph_id=%d vs reference_id=%d | "
        "predicted=%d, reference=%d, matched=%d | "
        "T-P=%.3f T-R=%.3f T-F1=%.3f | Unmatched=%.3f Missing=%.3f GED=%d",
        graph.id, reference_graph.id,
        len(predicted), len(reference), matched,
        t_precision, t_recall, t_f1,
        hallucination_rate, omission_rate, ged,
    )
    if unmatched_pred_idx:
        logger.info("Unmatched in predicted (not in reference):")
        for i in sorted(unmatched_pred_idx):
            logger.info("  + %s", _triple_str(predicted[i]))
    if unmatched_ref_idx:
        logger.info("Missing from predicted (in reference, not matched):")
        for i in sorted(unmatched_ref_idx):
            logger.info("  - %s", _triple_str(reference[i]))

    return dict(
        reference_graph_id=reference_graph.id,
        t_precision=round(t_precision, 3),
        t_recall=round(t_recall, 3),
        t_f1=round(t_f1, 3),
        hallucination_rate=round(hallucination_rate, 3),
        omission_rate=round(omission_rate, 3),
        ged=ged,
        matched_count=matched,
        reference_relation_count=len(reference),
    )


def build_judge_prompt(graph, text: str, prompt_template: str) -> str:
    graph_text = _graph_to_text(graph)
    return (
        f"You are evaluating a knowledge graph extracted from a source text.\n\n"
        f"The extraction prompt used to create this graph was:\n{prompt_template}\n\n"
        f"Source text:\n{text}\n\n"
        f"Knowledge graph triples ({len(graph.relations)} total):\n{graph_text}\n\n"
        f"Your tasks:\n"
        f"1. For each triple in the graph, decide whether it is supported by the source text "
        f"(supported=true) or not (supported=false). A triple is supported only if ALL of the "
        f"following hold: (a) both entities refer to things actually mentioned in the text "
        f"(paraphrased names/wording are fine); (b) the relation type accurately reflects what "
        f"the text states about them, not just a loosely related or overly generic relation; "
        f"(c) the DIRECTION of the relation matches the text — the subject and object are not "
        f"swapped. Mark supported=false for hallucinated facts, incorrect or overly generic "
        f"relation types, and reversed-direction relations.\n"
        f"2. List important relations present in the source text that are NOT captured by any triple in the graph.\n"
        f"3. Write a brief analysis of the overall quality.\n\n"
        f"Evaluate all {len(graph.relations)} triples."
    )


class EvaluationService:

    def evaluate(self, graph, text: str, prompt_template: str, model: str = "claude-sonnet-4-6",
                 reference_graph=None) -> EvaluationResult:
        from langchain.chat_models import init_chat_model

        prompt = build_judge_prompt(graph, text, prompt_template)

        logger.info("Judge prompt:\n%s", prompt)

        llm = init_chat_model(model, timeout=120)
        judge: JudgeOutput = llm.with_structured_output(JudgeOutput).invoke(prompt)

        supported = sum(1 for v in judge.triple_verdicts if v.supported)
        unsupported = len(judge.triple_verdicts) - supported
        missing = len(judge.missing_important_relations)

        precision = supported / len(judge.triple_verdicts) if judge.triple_verdicts else 0.0
        recall = supported / (supported + missing) if (supported + missing) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        ref_metrics = _compute_reference_metrics(graph, reference_graph) if reference_graph is not None else {}
        connectivity_score = _compute_connectivity_score(graph)

        return EvaluationResult(
            graph_id=graph.id,
            graph_relations=len(graph.relations),
            eval_model=model,
            precision=round(precision, 3),
            recall=round(recall, 3),
            f1=round(f1, 3),
            supported_count=supported,
            unsupported_count=unsupported,
            missing_count=missing,
            triple_verdicts=[v.model_dump() for v in judge.triple_verdicts],
            missing_relations=judge.missing_important_relations,
            analysis=judge.analysis,
            connectivity_score=connectivity_score,
            judge_prompt_version=JUDGE_PROMPT_VERSION,
            judge_prompt_text=prompt,
            **ref_metrics,
        )
