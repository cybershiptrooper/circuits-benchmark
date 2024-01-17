from typing import Set

from benchmark import vocabs
from tracr.rasp import rasp
from benchmark.common_programs import make_hist, make_length


def get_program() -> rasp.SOp:
  return make_token_frequency_classifier(rasp.tokens)

def make_token_frequency_classifier(sop: rasp.SOp) -> rasp.SOp:
    """
    Classifies each token based on its frequency as 'rare', 'common', or 'frequent'.

    Example usage:
      frequency_classifier = make_token_frequency_classifier(rasp.tokens)
      frequency_classifier(["a", "b", "a", "c", "a", "b"])
      >> ["frequent", "common", "frequent", "rare", "frequent", "common"]
    """
    frequency = make_hist()
    total_tokens = make_length()
    frequency_classification = rasp.SequenceMap(
        lambda freq, total: "frequent" if freq > total / 2 else ("common" if freq > total / 4 else "rare"),
        frequency, total_tokens)
    return frequency_classification


def get_vocab() -> Set:
  return vocabs.get_ascii_letters_vocab(count=5)