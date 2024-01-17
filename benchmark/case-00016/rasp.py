from typing import Set

from benchmark import vocabs
from tracr.rasp import rasp
from benchmark.common_programs import make_length


def get_program() -> rasp.SOp:
  return make_token_position_encoding()

def make_token_position_encoding() -> rasp.SOp:
    """
    Encodes each token's position relative to the start and end of the sequence.

    Example usage:
      position_encoding = make_token_position_encoding()
      position_encoding(["a", "b", "c", "d"])
      >> [(0, 3), (1, 2), (2, 1), (3, 0)]

    Returns:
      A SOp that maps each token in the input sequence to a tuple representing 
      its position index from the start and its reverse index from the end.
    """
    position_encoding = rasp.SequenceMap(
        lambda start_idx, end_idx: (start_idx, end_idx),
        rasp.indices, make_length() - rasp.indices - 1).named("position_encoding")
    return position_encoding


def get_vocab() -> Set:
  return vocabs.get_ascii_letters_vocab(count=3)