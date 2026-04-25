import torch.nn as nn


class LibrarianPolicy(nn.Module):
    """768-dim embedding -> 4-dim action space (NOOP/ADD/UPDATE/DELETE)."""

    def __init__(self, input_dim=768, hidden_dim=128, output_dim=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        return self.net(x)
