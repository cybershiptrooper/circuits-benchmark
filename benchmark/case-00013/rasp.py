from typing import Set

from benchmark import vocabs
from tracr.rasp import rasp
from benchmark.program_evaluation_type import causal_and_regular
from benchmark.common_programs import make_hist

@causal_and_regular
def get_program() -> rasp.SOp:
  return make_count_less_freq(2)

@causal_and_regular
def make_count_less_freq(n: int) -> rasp.SOp:
  """Returns how many tokens appear fewer than n times in the input.

  The output sequence contains this count in each position.

  Example usage:
    count_less_freq = make_count_less_freq(2)
    count_less_freq(["a", "a", "a", "b", "b", "c"])
    >> [3, 3, 3, 3, 3, 3]
    count_less_freq(["a", "a", "c", "b", "b", "c"])
    >> [6, 6, 6, 6, 6, 6]

  Args:
    n: Integer to compare token frequences to.
  """
  hist = make_hist().named("hist")
  select_less = rasp.Select(hist, hist,
                            lambda x, y: x <= n).named("select_less")
  return rasp.SelectorWidth(select_less).named("count_less_freq")


def get_vocab() -> Set:
  return vocabs.get_ascii_letters_vocab(count=3)