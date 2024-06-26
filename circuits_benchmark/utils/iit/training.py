import torch as t
import numpy as np
from transformer_lens import HookedTransformer
import iit.model_pairs as mp
from circuits_benchmark.utils.iit import make_iit_hl_model, create_dataset
from circuits_benchmark.utils.iit.ll_cfg import make_ll_cfg_for_case
import circuits_benchmark.utils.iit.correspondence as correspondence
import random


def train_model(config, case, tracr_output, hl_model, use_wandb=False):
    # seed everything
    t.manual_seed(0)
    np.random.seed(0)
    # t.use_deterministic_algorithms(True)
    random.seed(0)

    # make dataset
    hl_model.to(config.device)
    iit_hl_model = make_iit_hl_model(hl_model)
    train_data, test_data = create_dataset(case, iit_hl_model)
    # make model
    ll_cfg = make_ll_cfg_for_case(hl_model, case.get_index())
    print(ll_cfg)
    model = HookedTransformer(ll_cfg)
    model.to(config.device)

    lr_scheduler_map = {
        "" : None,
        "plateau" : t.optim.lr_scheduler.ReduceLROnPlateau,
    }

    mp_map = {
        "freeze": mp.FreezedModelPair,
        "strict": mp.StrictIITModelPair,
        "stop_grad": mp.StopGradModelPair,
    }

    # make model pair
    training_args = {
        "lr": config.lr,
        "batch_size": 512,
        "atol": config.atol,
        "use_single_loss": config.use_single_loss,
        "iit_weight": config.iit_weight,
        "behavior_weight": config.behavior_weight,
        "strict_weight": config.strict_weight,
        "clip_grad_norm": config.clip_grad_norm,
        "lr_scheduler": lr_scheduler_map[config.lr_scheduler],
    }
    hl_ll_corr = correspondence.TracrCorrespondence.from_output(
        case, tracr_output
    )
    model_pair = mp_map[config.model_pair](
        hl_model=iit_hl_model,
        ll_model=model,
        corr=hl_ll_corr,
        training_args=training_args,
    )

    # train model
    model_pair.train(
        train_data,
        test_data,
        epochs=config.epochs,
        use_wandb=use_wandb,
        wandb_name_suffix=config.wandb_suffix,
    )
    return model_pair
