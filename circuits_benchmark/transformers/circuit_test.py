import unittest

from circuits_benchmark.benchmark.cases.case_3 import Case3


class CircuitTest(unittest.TestCase):
  def test_build_circuit_for_case_3_with_component_granularity(self):
    case = Case3()
    hl_circuit, ll_circuit, alignment = case.get_tracr_circuit(granularity="component")

    expected_nodes = ["embed", "pos_embed", "blocks.0.mlp", "blocks.1.attn"]
    expected_edges = [("embed", "blocks.0.mlp"),
                      ("pos_embed", "blocks.1.attn"),
                      ("blocks.0.mlp", "blocks.1.attn")]
    self.assertEqual(sorted(ll_circuit.nodes), sorted(expected_nodes))
    self.assertEqual(sorted(ll_circuit.edges), sorted(expected_edges))

  def test_build_circuit_for_case_3_with_matrix_granularity(self):
    case = Case3()
    hl_circuit, ll_circuit, alignment = case.get_tracr_circuit(granularity="matrix")

    expected_nodes = ["embed.W_E", "pos_embed.W_pos",
                      "blocks.0.mlp.W_in", "blocks.0.mlp.W_out",
                      "blocks.1.attn.W_Q", "blocks.1.attn.W_K",
                      "blocks.1.attn.W_V", "blocks.1.attn.W_O"]
    expected_edges = [("embed.W_E", "blocks.0.mlp.W_in"),
                      ("pos_embed.W_pos", "blocks.1.attn.W_K"),
                      ("pos_embed.W_pos", "blocks.1.attn.W_Q"),
                      ("blocks.0.mlp.W_in", "blocks.0.mlp.W_out"),
                      ("blocks.0.mlp.W_out", "blocks.1.attn.W_V"),
                      ("blocks.1.attn.W_K", "blocks.1.attn.W_O"),
                      ("blocks.1.attn.W_Q", "blocks.1.attn.W_O"),
                      ("blocks.1.attn.W_V", "blocks.1.attn.W_O")]
    self.assertEqual(sorted(ll_circuit.nodes), sorted(expected_nodes))
    self.assertEqual(sorted(ll_circuit.edges), sorted(expected_edges))

  def test_build_circuit_for_case_3_with_acdc_hooks_granularity(self):
    case = Case3()
    hl_circuit, ll_circuit, alignment = case.get_tracr_circuit(granularity="acdc_hooks")

    expected_nodes = ["hook_embed", "hook_pos_embed",
                      "blocks.0.hook_mlp_in", "blocks.0.hook_mlp_out",
                      "blocks.1.hook_q_input", "blocks.1.hook_k_input", "blocks.1.hook_v_input",
                      "blocks.1.attn.hook_q", "blocks.1.attn.hook_k", "blocks.1.attn.hook_v",
                      "blocks.1.attn.hook_result", "blocks.1.hook_resid_post"]
    expected_edges = [("hook_embed", "blocks.0.hook_mlp_in"),
                      ("hook_pos_embed", "blocks.1.hook_q_input"),
                      ("hook_pos_embed", "blocks.1.hook_k_input"),
                      ("blocks.0.hook_mlp_in", "blocks.0.hook_mlp_out"),
                      ("blocks.0.hook_mlp_out", "blocks.1.hook_v_input"),
                      ("blocks.1.hook_q_input", "blocks.1.attn.hook_q"),
                      ("blocks.1.hook_k_input", "blocks.1.attn.hook_k"),
                      ("blocks.1.hook_v_input", "blocks.1.attn.hook_v"),
                      ("blocks.1.attn.hook_q", "blocks.1.attn.hook_result"),
                      ("blocks.1.attn.hook_k", "blocks.1.attn.hook_result"),
                      ("blocks.1.attn.hook_v", "blocks.1.attn.hook_result"),
                      ("blocks.1.attn.hook_result", "blocks.1.hook_resid_post")]
    self.assertEqual(sorted(ll_circuit.nodes), sorted(expected_nodes))
    self.assertEqual(sorted(ll_circuit.edges), sorted(expected_edges))

  def test_build_circuit_for_case_3_with_sp_hooks_granularity(self):
    case = Case3()
    hl_circuit, ll_circuit, alignment = case.get_tracr_circuit(granularity="sp_hooks")

    expected_nodes = ["hook_embed", "hook_pos_embed",
                      "blocks.0.hook_mlp_in", "blocks.0.hook_mlp_out",
                      "blocks.1.hook_q_input", "blocks.1.hook_k_input", "blocks.1.hook_v_input",
                      "blocks.1.attn.hook_result", "blocks.1.hook_resid_post"]
    expected_edges = [("hook_embed", "blocks.0.hook_mlp_in"),
                      ("hook_pos_embed", "blocks.1.hook_q_input"),
                      ("hook_pos_embed", "blocks.1.hook_k_input"),
                      ("blocks.0.hook_mlp_in", "blocks.0.hook_mlp_out"),
                      ("blocks.0.hook_mlp_out", "blocks.1.hook_v_input"),
                      ("blocks.1.hook_q_input", "blocks.1.attn.hook_result"),
                      ("blocks.1.hook_k_input", "blocks.1.attn.hook_result"),
                      ("blocks.1.hook_v_input", "blocks.1.attn.hook_result"),
                      ("blocks.1.attn.hook_result", "blocks.1.hook_resid_post")]
    self.assertEqual(sorted(ll_circuit.nodes), sorted(expected_nodes))
    self.assertEqual(sorted(ll_circuit.edges), sorted(expected_edges))