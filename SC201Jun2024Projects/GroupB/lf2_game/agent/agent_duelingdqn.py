import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class DuelingLSTMDQN(nn.Module):
    def __init__(self, state_size_x, state_size_y, action_size):
        super().__init__()
        self.state_size_x = state_size_x
        self.state_size_y = state_size_y
        self.action_size = action_size

        self.seq_model = nn.Sequential(
            nn.Conv2d(4, 32, 8, stride=4, padding=1),
            nn.ReLU(),
            nn.AvgPool2d(2),
            torch.nn.Conv2d(32, 64, 4, stride=2),
            nn.ReLU(),
            nn.AvgPool2d(2),
            torch.nn.Conv2d(64, 64, 3),
            nn.ReLU(),
            nn.AvgPool2d(2)
        )

        self.fc = nn.Linear(64 * 1 * 4 + 16 + 1, 657)
        self.lstm = nn.LSTM(657, 64, batch_first=True)
        self.fc_z_v = nn.Linear(64, 1)
        self.fc_z_a = nn.Linear(64, self.action_size)

    def forward(self, state, agent_info, action):
        # N x 4 x 160 x 380
        out = self.seq_model(state)
        # N x 64 x 1 x 4
        out = torch.flatten(out, 1)
        # N x 256
        
        # Concatenate the agent_info and action with the processed image input
        # agent_info shape: N x 16
        # action shape: N x 1
        if len(action.shape) == 1:
            action = action.unsqueeze(1)

        merge = torch.cat([out, agent_info, action], dim=1) # (64, 273) 
        # N x 273 ( 4 * 160 * 380 + 64 * 1 * 4 + 16 + 1
        merge = self.fc(merge)
        # N x 657
        merge = merge.unsqueeze(1)
        # N x 1 x 657
        
        lstm_out, _ = self.lstm(merge)
        # N x 1 x 64
        s_value = self.fc_z_v(lstm_out[:,-1])
        actions_out = torch.softmax(self.fc_z_a(lstm_out[:,-1]), dim=1) 
        advantage = self.fc_z_a(lstm_out[:,-1])
        
        # advantage need to remove mean of advantage to decide the fianl ouput with action 
        q = s_value + advantage - advantage.mean()
        return q, actions_out, s_value

