import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import torchvision.transforms as T
import numpy as np
from ReplayMemory import *

def soft_update(target, source, tau):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(target_param.data * (1.0 - tau) + param.data * tau)

def hard_update(target, source):
    for target_param, param in zip(target.parameters(), source.parameters()):
        target_param.data.copy_(param.data)

class Critic(nn.Module): 
    def __init__(self, lr, stateDim, nActions, full1Dim, full2Dim, layerNorm,name):
        super(Critic,self).__init__()
        
        self.layerNorm = layerNorm
        #Q1
        self.full1 = nn.Linear(stateDim+nActions, full1Dim)
        nn.init.kaiming_uniform_(self.full1.weight, a= 0.01, mode='fan_in', nonlinearity='leaky_relu')
        
        self.layernorm1 = nn.LayerNorm(full1Dim)
        
        self.full2 = nn.Linear(full1Dim,full2Dim)
        nn.init.kaiming_uniform_(self.full2.weight, a= 0.01, mode='fan_in', nonlinearity='leaky_relu')
        
        self.layernorm2 = nn.LayerNorm(full2Dim)
        
        self.final1 = nn.Linear(full2Dim,1)
        
        #Q2
        self.full3 = nn.Linear(stateDim+nActions, full1Dim)
        nn.init.kaiming_uniform_(self.full3.weight, a= 0.01, mode='fan_in', nonlinearity='leaky_relu')
        
        self.layernorm3 = nn.LayerNorm(full1Dim)
        
        self.full4 = nn.Linear(full1Dim,full2Dim)
        nn.init.kaiming_uniform_(self.full4.weight, a= 0.01, mode='fan_in', nonlinearity='leaky_relu')
        
        self.layernorm4 = nn.LayerNorm(full2Dim)
        
        self.final2 = nn.Linear(full2Dim,1)
        
        self.optimizer = optim.Adam(self.parameters(),lr=lr)
        self.name = name
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.to(self.device)
        
    def forward(self,state,action):
        
        stateaction = torch.cat([state,action],1)
        
        if self.layerNorm:
            
            Q1 = F.leaky_relu(self.layernorm1(self.full1(stateaction)))
            Q1 = F.leaky_relu(self.layernorm2(self.full2(Q1)))        
            Q1 = self.final1(Q1)
        
            Q2 = F.leaky_relu(self.layernorm3(self.full3(stateaction)))
            Q2 = F.leaky_relu(self.layernorm4(self.full4(Q2)))
            Q2 = self.final2(Q2)

        else:
            
            Q1 = F.leaky_relu(self.full1(stateaction))
            Q1 = F.leaky_relu(self.full2(Q1))        
            Q1 = self.final1(Q1)
        
            Q2 = F.leaky_relu(self.full3(stateaction))
            Q2 = F.leaky_relu(self.full4(Q2))        
            Q2 = self.final2(Q2)

        
        return Q1, Q2
    
    def onlyQ1(self,state,action):
        
        stateaction = torch.cat([state,action],1)
        
        if self.layerNorm:
            
            Q1 = F.leaky_relu(self.layernorm1(self.full1(stateaction)))
            Q1 = F.leaky_relu(self.layernorm2(self.full2(Q1)))        
            Q1 = self.final1(Q1)

        else:
            Q1 = F.leaky_relu(self.full1(stateaction))
            Q1 = F.leaky_relu(self.full2(Q1))        
            Q1 = self.final1(Q1)

        return Q1
    
    def saveCheckpoint(self,ajan):
        torch.save(self.state_dict(),'.\\NNs\\{}'.format(ajan) + self.name)
        
    def loadCheckpoint(self,ajan):
        self.load_state_dict(torch.load('.\\NNs\\{}'.format(ajan)  + self.name))
            
class Actor(nn.Module):
    def __init__(self, lr, stateDim, nActions, full1Dim, full2Dim, layerNorm, name):
        super(Actor,self).__init__()
        
        self.layerNorm = layerNorm
        
        self.full1 = nn.Linear(stateDim,full1Dim)
        nn.init.kaiming_uniform_(self.full1.weight, a= 0.01, mode='fan_in', nonlinearity='leaky_relu')
        
        self.layernorm1 = nn.LayerNorm(full1Dim)
        
        self.full2 = nn.Linear(full1Dim,full2Dim)
        nn.init.kaiming_uniform_(self.full2.weight, a= 0.01, mode='fan_in', nonlinearity='leaky_relu')
        
        self.layernorm2 = nn.LayerNorm(full2Dim)
        
        self.final = nn.Linear(full2Dim,nActions)
        
        self.optimizer = optim.Adam(self.parameters(),lr=lr)
        self.name = name
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.to(self.device)

    def forward(self,x):
        if self.layerNorm:
            
            x = F.leaky_relu(self.layernorm1(self.full1(x)))
            x = F.leaky_relu(self.layernorm2(self.full2(x)))

        else:
            
            x = F.leaky_relu(self.full1(x))
            x = F.leaky_relu(self.full2(x))

        
        return torch.tanh(self.final(x))
    
    def saveCheckpoint(self,ajan):
        torch.save(self.state_dict(),'.\\NNs\\{}'.format(ajan)  + self.name)
        
    def loadCheckpoint(self,ajan):
        self.load_state_dict(torch.load('.\\NNs\\{}'.format(ajan) + self.name))
    
class Agent(nn.Module):
    def __init__(self, actorLR, criticLR, stateDim, actionDim,full1Dim,full2Dim, tau, gamma, bufferSize, batchSize,\
                 layerNorm, name):
        super(Agent,self).__init__()
        
        self.tau = tau
        self.gamma = gamma
        self.bufferSize = bufferSize
        self.batchSize = batchSize
        self.actorTrainable = True
        self.actionDim = actionDim
        self.actionNoise = 0.1
        self.TD3LearningNoise = 0.2
        self.TD3LearningNoiseClamp = 0.5
        
        self.actor = Actor(actorLR,stateDim,actionDim, full1Dim, full2Dim, layerNorm, 'Actor_'+name)
        self.targetActor = Actor(actorLR,stateDim,actionDim, full1Dim, full2Dim, layerNorm, 'TargetActor_'+name)
        hard_update(self.targetActor, self.actor)
        
        self.critic = Critic(criticLR, stateDim, actionDim, full1Dim, full2Dim, layerNorm, 'Critic_'+name)
        self.targetCritic = Critic(criticLR, stateDim, actionDim, full1Dim, full2Dim, layerNorm, 'TargetCritic_'+name)
        hard_update(self.targetCritic, self.critic)
        
        self.buffer = UniformMemory(bufferSize)
    
    def chooseAction(self, state):
        self.actor.eval()
        state = torch.tensor(state, dtype=torch.float).to(self.actor.device)
        action = (self.actor(state) + \
                  (torch.normal(mean=torch.zeros(self.actionDim),std=torch.ones(self.actionDim)*self.actionNoise)).to(self.actor.device))\
            .clamp(-1,+1)
        return action.cpu().detach().numpy()
    
    def chooseActionSmallNoise(self, state):
        self.actor.eval()
        state = torch.tensor(state, dtype=torch.float).to(self.actor.device)
        action = (self.actor(state) + \
                  (torch.normal(mean=torch.zeros(self.actionDim),std=torch.ones(self.actionDim)*self.actionNoise/10)).to(self.actor.device))\
            .clamp(-1,+1)
        return action.cpu().detach().numpy()
    
    def chooseActionNoNoise(self, state):
        self.actor.eval()
        state = torch.from_numpy(state).float().to(self.actor.device)
        action = self.actor(state)
        return action.cpu().detach().numpy()
    
    def store(self, *args):
        self.buffer.store(*args)
        
    def learn(self):

        #SAMPLING
        if isinstance(self.buffer,UniformMemory):
            batchState, batchAction, batchNextState, batchReward, batchDone = self.buffer.sample(self.batchSize)
       
        batchState = torch.tensor(np.array(batchState), dtype=torch.float).to(self.critic.device)
        batchAction = torch.tensor(np.array(batchAction), dtype=torch.float).to(self.critic.device)
        batchNextState = torch.tensor(np.array(batchNextState), dtype=torch.float).to(self.critic.device)
        batchReward = torch.tensor(np.array(batchReward), dtype=torch.float).to(self.critic.device)
        batchDone = torch.tensor(np.array(batchDone), dtype=torch.float).to(self.critic.device)
        
        self.targetActor.eval()
        self.targetCritic.eval()
        self.critic.eval()
        
        #NOISE REGULATION
        targetNextActions = self.targetActor(batchNextState)
        noise = (torch.normal(mean=torch.zeros(self.actionDim),std=torch.ones(self.actionDim)*self.TD3LearningNoise)).to(self.actor.device)
        noise = noise.clamp(-self.TD3LearningNoiseClamp,self.TD3LearningNoiseClamp)
        targetNextActions = (targetNextActions + noise).clamp(-1,+1)
        
        #TWIN TARGET CRITIC
        targetQ1, targetQ2 = self.targetCritic(batchNextState,targetNextActions)
        targetQmin = torch.min(targetQ1,targetQ2)
        
        #BELLMAN
        targetQ = batchReward.reshape(-1,1) + (self.gamma*targetQmin*((1-batchDone).reshape(-1,1))).detach()
        
        #CURRENT CRITIC
        currentQ1, currentQ2 = self.critic(batchState,batchAction)
        currentQ = torch.min(currentQ1,currentQ2)
        
    
        #CRITIC UPDATE
        self.critic.train()
        if isinstance(self.buffer,UniformMemory):
            self.critic_loss = (F.mse_loss(currentQ1,targetQ) + F.mse_loss(currentQ2,targetQ)) 
       
        self.critic.optimizer.zero_grad()
        self.critic_loss.backward()
        self.critic.optimizer.step()

        #ACTOR UPDATE
        if self.actorTrainable is True:
            self.actor.train()
            self.nextAction = self.actor(batchState)
            self.actor_loss = -self.critic.onlyQ1(batchState,self.nextAction).mean()
            self.actor.optimizer.zero_grad()
            self.actor_loss.backward()
            self.actor.optimizer.step()
        
            soft_update(self.targetCritic, self.critic, self.tau)
            soft_update(self.targetActor, self.actor, self.tau)
        
        self.actorTrainable = not self.actorTrainable
        
        return self.critic_loss.mean().cpu().detach().numpy(), self.actor_loss.cpu().detach().numpy() 
        
    def saveCheckpoints(self,ajan):
        self.critic.saveCheckpoint(ajan)
        self.actor.saveCheckpoint(ajan)
        self.targetCritic.saveCheckpoint(ajan)
        self.targetActor.saveCheckpoint(ajan)
        
    def loadCheckpoints(self,ajan):
        self.critic.loadCheckpoint(ajan)
        self.actor.loadCheckpoint(ajan)
        self.targetCritic.loadCheckpoint(ajan)
        self.targetActor.loadCheckpoint(ajan)