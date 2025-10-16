from typing import Optional, Tuple

import torch
try:
    import torch_npu
except:
    print('Using N* GPU...')
import math


def repeat_kv(hidden_states: torch.Tensor, n_rep: int) -> torch.Tensor:
    """
    This is the equivalent of torch.repeat_interleave(x, dim=1, repeats=n_rep). The hidden states go from (batch,
    num_key_value_heads, seqlen, head_dim) to (batch, num_attention_heads, seqlen, head_dim)
    """
    batch, num_key_value_heads, slen, head_dim = hidden_states.shape
    if n_rep == 1:
        return hidden_states
    hidden_states = hidden_states[:, :, None, :, :].expand(batch, num_key_value_heads, n_rep, slen, head_dim)
    return hidden_states.reshape(batch, num_key_value_heads * n_rep, slen, head_dim)


def spec_sdpa_attention_forward(
    module: torch.nn.Module,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attention_mask: Optional[torch.Tensor],
    dropout: float = 0.0,
    scaling: Optional[float] = None,
    is_causal: Optional[bool] = None,
    **kwargs,
) -> Tuple[torch.Tensor, None]:
    if hasattr(module, "num_key_value_groups"):
        key = repeat_kv(key, module.num_key_value_groups)
        value = repeat_kv(value, module.num_key_value_groups)

    causal_mask = attention_mask
    if attention_mask is not None and causal_mask.ndim == 4:
        causal_mask = causal_mask[:, :, :, : key.shape[-2]]

    # SDPA with memory-efficient backend is bugged with non-contiguous inputs and custom attn_mask for some torch versions
    # Reference: https://github.com/pytorch/pytorch/issues/112577.
    query = query.contiguous()
    key = key.contiguous()
    value = value.contiguous()

    # We dispatch to SDPA's Flash Attention or Efficient kernels via this `is_causal` if statement instead of an inline conditional assignment
    # in SDPA to support both torch.compile's dynamic shapes and full graph options. An inline conditional prevents dynamic shapes from compiling.
    # Note that it is important to check first for the shape, otherwise compile will fail with `argument 'is_causal' must be bool, not SymBool`
    if is_causal is None:
        is_causal = query.shape[2] > 1 and causal_mask is None

    # Shapes (e.g. query.shape[2]) are tensors during jit tracing, resulting in `is_causal` being a tensor.
    # We convert it to a bool for the SDPA kernel that only accepts bools.

    if attention_mask is None:
        atten_mask_npu = torch.triu(torch.ones([query.size(-2), 
                                                query.size(-2)]), diagonal=1).bool().to(query.device)
    elif attention_mask.dtype == torch.bool:
        atten_mask_npu = torch.logical_not(attention_mask.bool()).to(attention_mask.device) # atten_mask需要取反
    else:
        atten_mask_npu = attention_mask.bool().to(attention_mask.device)

    if torch.jit.is_tracing() and isinstance(is_causal, torch.Tensor):
        is_causal = is_causal.item()

    # attn_output = torch.nn.functional.scaled_dot_product_attention(
    #     query,
    #     key,
    #     value,
    #     attn_mask=causal_mask,
    #     dropout_p=dropout,
    #     scale=scaling,
    #     is_causal=is_causal,
    # )

    head_num = query.shape[1]
    attn_output = torch_npu.npu_fusion_attention(
                    query, key, value, head_num, input_layout="BNSD", 
                    pse=None,
                    atten_mask=atten_mask_npu,
                    scale=1.0 / math.sqrt(query.shape[-1]),
                    pre_tockens=2147483647,
                    next_tockens=2147483647,
                    keep_prob=1
                )[0]

    attn_output = attn_output.transpose(1, 2).contiguous()

    return attn_output, None
