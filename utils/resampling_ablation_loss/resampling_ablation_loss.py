import random
from typing import List, Generator

import numpy as np
import torch as t
from jaxtyping import Float
from torch import Tensor
from transformer_lens import HookedTransformer

from benchmark.case_dataset import CaseDataset
from training.compression.autencoder import AutoEncoder
from utils.resampling_ablation_loss.intervention import Intervention
from utils.resampling_ablation_loss.intervention_type import InterventionType


def get_resampling_ablation_loss(
    clean_inputs: CaseDataset,
    corrupted_inputs: CaseDataset,
    base_model: HookedTransformer,
    hypothesis_model: HookedTransformer,
    autoencoder: AutoEncoder | None = None,
    hook_filters : List[str] | None = None,
    batch_size: int = 2048,
    max_interventions: int = 100
) -> Float[Tensor, ""]:
  if hook_filters is None:
    # by default, we use the following hooks for the intervention points.
    # This will give 2 + n_layers * 2 intervention points.
    hook_filters = ["hook_embed", "hook_pos_embed", "hook_attn_out", "hook_mlp_out"]

  # we assume that both models have the same architecture. Otherwise, the comparison is flawed since they have different
  # intervention points.
  assert base_model.cfg.n_layers == hypothesis_model.cfg.n_layers
  assert base_model.cfg.n_heads == hypothesis_model.cfg.n_heads
  assert base_model.cfg.n_ctx == hypothesis_model.cfg.n_ctx
  assert base_model.cfg.d_vocab == hypothesis_model.cfg.d_vocab

  # assert that clean_input and corrupted_input have the same length
  assert len(clean_inputs) == len(corrupted_inputs), "clean and corrupted inputs should have same length."
  # assert that clean and corrupted inputs are not exactly the same, otherwise the comparison is flawed.
  assert clean_inputs != corrupted_inputs, "clean and corrupted inputs should have different data."
  assert max_interventions > 0, "max_interventions should be greater than 0."

  # for each intervention, run both models, calculate MSE and add it to the losses.
  losses = []
  for intervention in get_interventions(base_model, hypothesis_model, hook_filters, autoencoder, max_interventions):

    # We may have more than one batch of inputs, so we need to iterate over them, and average at the end.
    intervention_losses = []
    for clean_inputs_batch, corrupted_inputs_batch in zip(clean_inputs.get_inputs_loader(batch_size),
                                                          corrupted_inputs.get_inputs_loader(batch_size)):
      clean_inputs_batch = clean_inputs_batch[CaseDataset.INPUT_FIELD]
      corrupted_inputs_batch = corrupted_inputs_batch[CaseDataset.INPUT_FIELD]

      with intervention.hooks(base_model, hypothesis_model, clean_inputs_batch, corrupted_inputs_batch):
          base_model_logits = base_model(clean_inputs_batch)
          hypothesis_model_logits = hypothesis_model(clean_inputs_batch)

          loss = t.nn.functional.mse_loss(base_model_logits, hypothesis_model_logits).item()
          intervention_losses.append(loss)

    losses.append(np.mean(intervention_losses))

  return np.mean(losses)


def get_interventions(
    base_model: HookedTransformer,
    hypothesis_model: HookedTransformer,
    hook_filters : List[str],
    autoencoder: AutoEncoder | None = None,
    max_interventions: int = 100) -> Generator[Intervention, None, None]:
  """Builds the different combinations for possible interventions on the base and hypothesis models."""
  hook_names: List[str | None] = list(base_model.hook_dict.keys())
  hook_names_for_patching = [name for name in hook_names
                             if not should_hook_name_be_skipped_due_to_filters(name, hook_filters)]

  # assert all hook names for patching are also present in the hypothesis model
  assert all([hook_name in hypothesis_model.hook_dict for hook_name in hook_names_for_patching]), \
    "All hook names for patching should be present in the hypothesis model."

  # For each hook name we need to decide what type of intervention we want to apply.
  options = InterventionType.get_available_interventions(autoencoder)

  # If max_interventions is greater than the total number of possible combinations, we will use all of them.
  # Otherwise, we will use a random sample of max_interventions.
  total_number_combinations = len(options) ** len(hook_names_for_patching)

  if max_interventions < total_number_combinations:
    indices = random.sample(range(total_number_combinations), max_interventions)
  else:
    indices = range(total_number_combinations)

  for index in indices:
    # build intervention for index
    intervention_types = np.base_repr(index, base=len(options)).zfill(len(hook_names_for_patching))
    intervention_types = [options[int(digit)] for digit in intervention_types]
    intervention = Intervention(hook_names_for_patching, intervention_types, autoencoder)
    yield intervention


def should_hook_name_be_skipped_due_to_filters(hook_name: str | None, hook_filters: List[str]) -> bool:
  if hook_filters is None:
    # No filters to apply
    return False

  if hook_name is None:
    # No hook name to apply the filters to
    return False

  return not any([filter in hook_name for filter in hook_filters])

