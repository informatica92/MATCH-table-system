from typing import List

def f_score(a: List, b: List, beta: float = 1.0) -> float:
    intersection = len(set(a) & set(b))
    if intersection == 0:
        return 0.0
    precision = intersection / len(b)   # game coverage
    recall    = intersection / len(a)   # user coverage
    b2 = beta ** 2
    return (1 + b2) * precision * recall / (b2 * precision + recall)

def recommend_score(
    user_categories: List[str],
    user_mechanics:  List[str],
    game_categories: List[str],
    game_mechanics:  List[str],
    cat_weight: float = 0.35,
    mech_weight: float = 0.65,
    beta: float = 1.2,          # privilegia recall (trovare giochi che coprono i gusti)
) -> float:

    has_cats  = bool(user_categories and game_categories)
    has_mechs = bool(user_mechanics  and game_mechanics)

    if not has_cats and not has_mechs:
        return 0.5  # no information

    scores, weights = [], []

    if has_cats:
        scores.append(f_score(user_categories, game_categories, beta))
        weights.append(cat_weight)

    if has_mechs:
        scores.append(f_score(user_mechanics, game_mechanics, beta))
        weights.append(mech_weight)

    total_w = sum(weights)
    return sum(s * w for s, w in zip(scores, weights)) / total_w
