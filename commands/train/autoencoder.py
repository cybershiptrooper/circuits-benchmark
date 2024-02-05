from argparse import Namespace

from argparse_dataclass import ArgumentParser

from benchmark.benchmark_case import BenchmarkCase
from commands.train.compression_training_utils import parse_compression_size
from training.compression.autencoder import AutoEncoder
from training.compression.autoencoder_trainer import AutoEncoderTrainer
from training.training_args import TrainingArgs
from utils.hooked_tracr_transformer import HookedTracrTransformer


def setup_args_parser(subparsers):
  parser = subparsers.add_parser("autoencoder")
  parser.add_argument("-i", "--indices", type=str, default=None,
                      help="A list of comma separated indices of the cases to run against. "
                           "If not specified, all cases will be run.")
  parser.add_argument("-f", "--force", action="store_true",
                      help="Force compilation of cases, even if they have already been compiled.")
  parser.add_argument("-o", "--output-dir", type=str, default="results",
                      help="The directory to save the results to.")

  parser.add_argument("--residual-stream-compression-size", type=str, required=True,
                      help="A list of comma separated sizes for the compressed residual stream.")
  parser.add_argument("--ae-layers", type=int, default=2,
                      help="The desired number of layers for the autoencoder.")


def train_autoencoder(case: BenchmarkCase, args: Namespace):
  """Trains an autoencoder to compress and decompress the residual stream space of a transformer."""
  tl_model: HookedTracrTransformer = case.load_tl_model()

  compression_size = parse_compression_size(args, tl_model)
  if compression_size == "auto":
    raise ValueError("Autoencoder training requires a fixed compression size.")

  for compression_size in compression_size:
    training_args, _ = ArgumentParser(TrainingArgs).parse_known_args(args.original_args)
    original_residual_stream_size = tl_model.cfg.d_model

    compression_layers = args.ae_layers
    autoencoder = AutoEncoder(original_residual_stream_size, compression_size, compression_layers)

    print(
      f" >>> Starting AutoEncoder training for {case} with residual stream compression size {compression_size}.")
    trainer = AutoEncoderTrainer(case, autoencoder, tl_model, training_args, output_dir=args.output_dir)
    final_metrics = trainer.train()
    print(f" >>> Final metrics for {case}'s autoencoder with residual stream compression size {compression_size}: ")
    print(final_metrics)

    autoencoder.save_weights_to_file(f"{args.output_dir}/case-{case.get_index()}-resid-{str(compression_size)}-ae.pt")
