from utils.retrieval import search_rules


def is_low_confidence(results):
    """
    Chroma returns distance.
    Lower is better.
    """
    if not results:
        return True

    best_distance = results[0].get("distance", 999.0)
    return best_distance > 1.50


def format_source(result):
    return (
        f"Rule {result['rule_number']} | "
        f"{result['section']} | "
        f"Page {result['page']}"
    )


def build_answer_from_result(result):
    return (
        f"According to Rule {result['rule_number']} under "
        f"{result['section']}, {result['text']}"
    )


def answer_question(user_query: str):
    search_output = search_rules(user_query, top_k=3)
    mode = search_output["mode"]
    results = search_output["results"]

    if not results:
        return {
            "answer": "I could not find a relevant answer in the hostel rules.",
            "sources": []
        }

    if mode == "exact_rule":
        top = results[0]
        return {
            "answer": build_answer_from_result(top),
            "sources": [format_source(top)]
        }

    if is_low_confidence(results):
        top = results[0]
        return {
            "answer": (
                "I could not find a highly reliable answer in the hostel rules. "
                "The closest match I found is:\n\n"
                f"{build_answer_from_result(top)}"
            ),
            "sources": [format_source(top)]
        }

    top = results[0]
    answer = build_answer_from_result(top)
    sources = [format_source(top)]

    if len(results) > 1:
        second = results[1]
        if second.get("distance", 999.0) <= 1.30:
            sources.append(format_source(second))

    return {
        "answer": answer,
        "sources": sources
    }