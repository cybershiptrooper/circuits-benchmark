from typing import Set

from benchmark import vocabs
from tracr.rasp import rasp
from benchmark.common_programs import shift_by


def get_program() -> rasp.SOp:
  return make_token_symmetry_checker(rasp.tokens)

def make_token_symmetry_checker(sop: rasp.SOp) -> rasp.SOp:
    """
    Checks if each token is symmetric around its center.

    Example usage:
      symmetry_checker = make_token_symmetry_checker(rasp.tokens)
      symmetry_checker(["radar", "apple", "rotor", "data"])
      >> [True, False, True, False]
    """
    half_length = rasp.Map(lambda x: len(x) // 2, sop)
    first_half = shift_by(half_length, sop)
    second_half = rasp.SequenceMap(lambda x, y: x[:y] == x[:-y-1:-1], sop, half_length)
    symmetry_checker = rasp.SequenceMap(lambda x, y: x if y else None, sop, second_half)
    return symmetry_checker


def get_vocab() -> Set:
  return vocabs.get_words_vocab().union({"radar", "rotor"})