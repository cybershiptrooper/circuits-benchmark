from tracr.compiler.compiling import TracrOutput
import iit.model_pairs as mp
from iit.utils import index
from circuits_benchmark.benchmark.benchmark_case import BenchmarkCase
from iit_utils.tracr_ll_corrs import get_tracr_ll_corr
from iit_utils._corr_utils import TracrHLCorr
from collections import namedtuple
import pickle

class TracrHLNode(mp.HLNode):
    def __init__(self, name, label, num_classes, idx=None):
        # type checks
        assert isinstance(name, str), ValueError(f"name is not a string, but {type(name)}")
        assert isinstance(label, str), ValueError(f"label is not a string, but {type(label)}")
        assert isinstance(num_classes, int), ValueError(f"num_classes is not an int, but {type(num_classes)}")
        assert idx is None or isinstance(idx, index.TorchIndex), ValueError(
            f"index is not a TorchIndex, but {type(index)}"
        )
        super().__init__(name, num_classes, idx)
        self.label = label

    def get_label(self) -> str:
        return self.label

    def get_name(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return super().__hash__() + hash(self.label)

    def __str__(self) -> str:
        return super().__str__()

    def __eq__(self, other) -> bool:
        if isinstance(other, TracrHLNode):
            return (
                self.name == other.name
                and self.label == other.label
                and self.num_classes == other.num_classes
                and self.index == other.index
            )
        return super().__eq__(other)

    def __repr__(self) -> str:
        return f"TracrHLNode(name: {self.name},\n label: {self.label},\n classes: {self.num_classes},\n index: {self.index}\n)"


class TracrCorrespondence(dict[TracrHLNode, set[mp.LLNode]]):
    def __setattr__(self, __name: TracrHLNode, __value: set[mp.LLNode]) -> None:
        assert isinstance(__name, TracrHLNode), ValueError(f"__name is not a TracrHLNode, but {type(__name)}")
        assert isinstance(__value, set), ValueError(f"__value is not a set, but {type(__value)}")
        assert all(isinstance(v, mp.LLNode) for v in __value), ValueError(f"__value contains non-LLNode elements")
        super().__setattr__(__name, __value)

    @classmethod
    def make_hl_ll_corr(
        cls, tracr_hl_corr: TracrHLCorr, tracr_ll_corr: dict[str, set[mp.LLNode]], hook_name_style: str = "tl"
    ):
        def hook_name(loc, style) -> str:
            layer, attn_or_mlp, unit = loc
            assert attn_or_mlp in ["attn", "mlp"], ValueError(f"Unknown attn_or_mlp {attn_or_mlp}")
            if style == "tl":
                return f"blocks.{layer}.{attn_or_mlp}.{'hook_result' if attn_or_mlp == 'attn' else 'hook_post'}"
            elif style == "wrapper":
                return f"mod.blocks.{loc}.mod.{attn_or_mlp}.hook_point"
            else:
                raise ValueError(f"Unknown style {style}")

        def idx(loc):
            _, attn_or_mlp, unit = loc
            if isinstance(unit, index.TorchIndex):
                return unit
            assert attn_or_mlp in ["attn", "mlp"], ValueError(f"Unknown attn_or_mlp {attn_or_mlp}")
            if attn_or_mlp == "attn":
                return index.Ix[:, :, unit, :]
            assert unit is None
            return index.Ix[[None]]

        if tracr_ll_corr is None:
            print("WARNING: tracr_ll_corr is None, returning an Identity correspondence using HL Model")
            return cls(
                {
                    TracrHLNode(
                        hook_name(hl_loc, hook_name_style),
                        label=basis_dir.name,
                        num_classes=0,  # TODO: get num_classes
                        idx=idx(hl_loc),
                    ): {mp.LLNode(hook_name(hl_loc, hook_name_style), idx(hl_loc), None)}
                    for basis_dir, hl_loc in tracr_hl_corr.items()
                }
            )

        return cls(
            {
                TracrHLNode(
                    hook_name(hl_loc, hook_name_style),
                    label=basis_dir.name,
                    num_classes=0,  # TODO: get num_classes
                    idx=idx(hl_loc),
                ): {
                    mp.LLNode(hook_name(ll_loc, "tl"), idx(ll_loc))
                    for ll_loc in tracr_ll_corr[basis_dir.name, basis_dir.value]
                }
                for basis_dir, hl_loc in tracr_hl_corr.items()
            }
        )

    @classmethod
    def from_output(cls, case: BenchmarkCase, tracr_output: TracrOutput):
        tracr_hl_corr = TracrHLCorr.from_output(tracr_output)
        tracr_ll_corr = get_tracr_ll_corr(case)
        return cls.make_hl_ll_corr(tracr_hl_corr, tracr_ll_corr)
    
    def save(self, filename: str):
        pickle.dump(self, open(filename, "wb"))
    
    @classmethod
    def load(cls, filename: str):
        return cls(pickle.load(open(filename, "rb")))


EdgeCorr = namedtuple("EdgeCorr", ["hookpoint_from", "index_from", "hookpoint_to", "index_to"])


def make_edge_corr(tracr_edges, hl_ll_corr) -> list[EdgeCorr]:
    ll_edges = []
    for tracr_edge in tracr_edges:
        tracr_n_from, tracr_n_to = tracr_edge
        hl_node_from = None
        hl_node_to = None
        # find hl nodes using labels
        for hl_node in hl_ll_corr.keys():
            if tracr_n_from == hl_node.label:
                hl_node_from = hl_node
            elif tracr_n_to == hl_node.label:
                hl_node_to = hl_node
        if hl_node_from is None or hl_node_to is None:
            continue

        ll_froms = hl_ll_corr[hl_node_from]
        ll_tos = hl_ll_corr[hl_node_to]

        for ll_from in ll_froms:
            for ll_to in ll_tos:
                hookpoint_from = ll_from.name
                index_from = ll_from.index
                hookpoint_to = ll_to.name
                index_to = ll_to.index
                ll_edge = EdgeCorr(hookpoint_from, index_from, hookpoint_to, index_to)
                ll_edges.append(ll_edge)
    return ll_edges