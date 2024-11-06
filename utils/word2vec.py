import numpy as np
from collections import Counter
from utils.bgg_manager import get_bgg_game_info

def cosine(a, b):
    return np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b))

class Word2Vec(object):
    def __init__(self):
        pass

    # Tokenize and pad items
    @staticmethod
    def tokenize_and_pad(items, pad_token="<PAD>"):
        max_len = max(len(i) for i in items)
        padded_items = [item + [pad_token] * (max_len - len(item)) for item in items]
        return padded_items

    # Build word frequency vectors
    @staticmethod
    def build_frequency_vectors(items):
        all_words = set(word for item in items for word in item)
        vectors = []
        for item in items:
            counter = Counter(item)
            vector = [counter[word] for word in all_words]
            vectors.append(vector)
        return np.array(vectors), list(all_words)

    # Compute similarity
    @staticmethod
    def get_similarities(vector, vectors):
        similarities = []
        for i, v in enumerate(vectors):
            sim = cosine(vector, v)
            similarities.append((i, sim))
        return similarities

class BGGWord2Vec(object):

    def __init__(self, username: str, propositions: list[tuple]):
        """

        """

        self.nlp = Word2Vec()
        self.categories = []
        self.mechanics = []
        self.liked_ids = []
        self.bgg_info = []

        for i, p in enumerate(propositions):
            print(f"Processing {i} ({p[7]})")
            _, description, category, mechanics = get_bgg_game_info(p[7])  # p[7] = bgg_game_id
            bgg_info = {
                "name": p[1],
                "description": description,
                "category": category,
                "mechanics": mechanics
            }
            self.bgg_info.append(bgg_info)
            if username in p[10]:  # p[10]: joined players
                self.liked_ids.append(i)
            self.categories.append(bgg_info["category"])  # bgg_info[2] = category
            self.mechanics.append(bgg_info["mechanics"])  # bgg_info[3] = mechanics

        # Create frequency vectors for categories and mechanics
        self.category_vectors, self.category_words = self.nlp.build_frequency_vectors(self.categories)
        self.mechanics_vectors, self.mechanics_words = self.nlp.build_frequency_vectors(self.mechanics)

    
    def _create_item_array_from_liked(self, item_words, item_name, verbose=False):
        item_vector = np.zeros(len(item_words))
        for liked_id in self.liked_ids:
            if verbose:
                print(f"Processing {liked_id} ({self.bgg_info[liked_id]['name']})")
                print(f"\t{self.bgg_info[liked_id][item_name]}")
            for c in self.bgg_info[liked_id][item_name]:
                item_vector[item_words.index(c)] = 1
        return item_vector

    def _remove_liked_ids_from_similarity(self, sims):
        sims = [s for s in sims if s[0] not in self.liked_ids]
        return sims

    # CREATE CATEGORY/MECHANICS ARRAY FROM LIKED
    def create_category_array_from_liked(self, verbose=False):
        return self._create_item_array_from_liked(self.category_words, "category", verbose)

    def create_mechanics_array_from_liked(self, verbose=False):
        return self._create_item_array_from_liked(self.mechanics_words, "mechanics", verbose)

    # USE CATEGORY/MECHANICS ARRAYS FOR SIMILARITY CALCULATION
    # # CATEGORY
    def get_category_similarities(self, categories_to_test, remove_liked_ids: bool = False):
        sims = self.nlp.get_similarities(categories_to_test, self.category_vectors)
        if remove_liked_ids:
            sims = self._remove_liked_ids_from_similarity(sims)
        return sims

    # # MECHANICS
    def get_mechanics_similarities(self, mechanics_to_test, remove_liked_ids: bool = False):
        sims = self.nlp.get_similarities(mechanics_to_test, self.mechanics_vectors)
        if remove_liked_ids:
            sims = self._remove_liked_ids_from_similarity(sims)
        return sims

    # # MIXED
    def get_merged_similarities(self, categories_to_test=None, mechanics_to_test=None, category_score=0.5, mechanics_score=None, remove_liked_ids: bool = False):
        if not mechanics_score:
            mechanics_score = 1.0 - category_score

        if category_score + mechanics_score != 1.0:
            raise AttributeError("Sum of category_score and mechanics_score must be 1")

        if not categories_to_test:
            categories_to_test = self.create_category_array_from_liked()
        if not mechanics_to_test:
            mechanics_to_test = self.create_mechanics_array_from_liked()

        category_sims = self.get_category_similarities(categories_to_test)
        mechanics_sims = self.get_mechanics_similarities(mechanics_to_test)
        if len(category_sims) != len(mechanics_sims):
            raise AttributeError("Len of category_sims and mechanics_sims must match")

        print(f"category sims:  {category_sims}")
        print(f"mechanics sims: {mechanics_sims}")
        mixed_sims = []
        for i in range(len(category_sims)):
            mixed_sims.append((i, category_sims[i][1]*category_score + mechanics_sims[i][1]*mechanics_score))

        print(f"mixed sims: {mixed_sims}")

        if remove_liked_ids:
            mixed_sims = self._remove_liked_ids_from_similarity(mixed_sims)
        
        return mixed_sims
            