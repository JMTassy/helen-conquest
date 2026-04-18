import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple, Any

class GatedDeltaRule(nn.Module):
    """
    Simplified implementation of the Gated Delta Rule from Qwen 3.5.
    This acts as the mathematical engine for HELEN's Serpent Coil.
    
    Solve (Linear) = Recurrent update with gated decay.
    Coagula (Full) = Global synchronization (Transformer).
    """
    def __init__(self, hidden_size: int, head_dim: int = 64):
        super().__init__()
        self.hidden_size = hidden_size
        self.head_dim = head_dim
        self.num_heads = hidden_size // head_dim
        
        # Projection layers for Delta Rule
        self.q_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.k_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.v_proj = nn.Linear(hidden_size, hidden_size, bias=False)
        self.g_proj = nn.Linear(hidden_size, self.num_heads, bias=False)  # Decay gate
        self.beta_proj = nn.Linear(hidden_size, self.num_heads, bias=False) # Learning rate

    def forward(
        self, 
        hidden_states: torch.Tensor, 
        initial_state: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for the Gated Delta Rule.
        Implements: Solve (Recurrence) logic.
        """
        b, s, h = hidden_states.shape
        
        q = self.q_proj(hidden_states).view(b, s, self.num_heads, self.head_dim)
        k = self.k_proj(hidden_states).view(b, s, self.num_heads, self.head_dim)
        v = self.v_proj(hidden_states).view(b, s, self.num_heads, self.head_dim)
        
        g = self.g_proj(hidden_states).sigmoid() # Gate [solve transition]
        beta = self.beta_proj(hidden_states).sigmoid() # Impetus [learning rate]
        
        # Recurrent state: batch x heads x k_dim x v_dim
        state = initial_state if initial_state is not None else torch.zeros(
            b, self.num_heads, self.head_dim, self.head_dim, 
            device=hidden_states.device, dtype=hidden_states.dtype
        )
        
        outputs = []
        for t in range(s):
            q_t = q[:, t]
            k_t = k[:, t]
            v_t = v[:, t]
            g_t = g[:, t].unsqueeze(-1).unsqueeze(-1)
            beta_t = beta[:, t].unsqueeze(-1).unsqueeze(-1)
            
            # Solve: Decay the old state
            state = state * g_t
            
            # Coagula: Compute error (delta) and update
            # current_v = keys * state
            v_pred = (k_t.unsqueeze(-2) @ state).squeeze(-2)
            delta = (v_t - v_pred) * beta_t.squeeze(-1)
            
            # Update state with key/delta pair
            state = state + (k_t.unsqueeze(-1) @ delta.unsqueeze(-2))
            
            # Output: query * state
            out_t = (q_t.unsqueeze(-2) @ state).squeeze(-2)
            outputs.append(out_t)
            
        final_output = torch.stack(outputs, dim=1).view(b, s, h)
        return final_output, state

class HybridSerpentEngine:
    """
    High-level engine that manages the transition between Linear (Solve) 
    and Full (Coagula) attention layers.
    """
    def __init__(self, config: dict):
        self.hidden_size = config.get("hidden_size", 4096)
        self.linear_layers = nn.ModuleList([
            GatedDeltaRule(self.hidden_size) for _ in range(config.get("num_linear_layers", 4))
        ])

    def step(self, x: torch.Tensor, state_cache: list) -> Tuple[torch.Tensor, list]:
        """Apply one block of Solve-step (Linear Attention)"""
        new_cache = []
        for i, layer in enumerate(self.linear_layers):
            prev_state = state_cache[i] if state_cache else None
            x, next_state = layer(x, prev_state)
            new_cache.append(next_state)
        return x, new_cache
