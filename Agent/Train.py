#IMPORTS
from NeuralNetwork import Agent
from ReplayMemory  import *
import numpy as np
import time
import sys
import math
from torch.utils.tensorboard import SummaryWriter
from statistics import mean
from HarfangEnv_GYM import *
import dogfight_client as df

df.connect("192.168.1.28", 50888) #TODO:Change IP and PORT values

start = time.time() #STARTING TIME
df.disable_log() 

# PARAMETERS
trainingEpisodes = 1000000
validationEpisodes =30
explorationEpisodes = 200

Test = True
if Test:
    render = False
else:
    render = True
    
df.set_renderless_mode(render)
df.set_client_update_mode(True)

bufferSize = (10**6)
gamma = 0.99
criticLR = 1e-3
actorLR = 1e-3
tau = 0.005
checkpointRate = 100
highScore = -math.inf
batchSize = 128
maxStep = 11000
hiddenLayer1 = 128
hiddenLayer2 = 256
stateDim = 11
actionDim = 3
useLayerNorm = True

name = "Harfang_GYM"


#INITIALIZATION
env = HarfangEnv()
agent = Agent(actorLR, criticLR, stateDim, actionDim, hiddenLayer1, hiddenLayer2, tau, gamma, bufferSize, batchSize, useLayerNorm, name)

writer = SummaryWriter(log_dir = "runs/" )
arttir = 0
agent.loadCheckpoints("Agent_")

if not Test:
    # RANDOM EXPLORATION
    print("Exploration Started")
    for episode in range(explorationEpisodes):
        state = env.reset()
        done = False
        for step in range(maxStep):
            if not done:
                action = env.action_space.sample()                

                n_state,reward,done, info = env.step(action)
                if step is maxStep-1:
                    done = True
                agent.store(state,action,n_state,reward,done)
                state=n_state

                if done:
                    break
        sys.stdout.write("\rExploration Completed: %.2f%%" % ((episode+1)/explorationEpisodes*100))
    sys.stdout.write("\n")

    print("Training Started")
    scores = []
    for episode in range(trainingEpisodes):
        state = env.reset()
        totalReward = 0
        done = False
        for step in range(maxStep):
            if not done:
                action = agent.chooseAction(state)
                n_state,reward,done, info = env.step(action)

                if step is maxStep - 1:
                    done = True

                agent.store(state, action, n_state, reward, done)
                state = n_state
                totalReward += reward

                if agent.buffer.fullEnough(agent.batchSize):
                    critic_loss, actor_loss = agent.learn()
                    writer.add_scalar('Loss/Critic_Loss', critic_loss, step + episode * maxStep)
                    writer.add_scalar('Loss/Actor_Loss', actor_loss, step + episode * maxStep)
                    
                if done:
                    break
               
        scores.append(totalReward)
        writer.add_scalar('Training/Episode Reward', totalReward, episode)
        writer.add_scalar('Training/Last 100 Average Reward', np.mean(scores[-100:]), episode)
        
        
        now = time.time()
        seconds = int((now - start) % 60)
        minutes = int(((now - start) // 60) % 60)
        hours = int((now - start) // 3600)
        print('Episode: ', episode+1, ' Completed: %r' % done,\
            ' FinalReward: %.2f' % totalReward, \
            ' Last100AverageReward: %.2f' % np.mean(scores[-100:]), \
            'RunTime: ', hours, ':',minutes,':', seconds)
            
        #VALIDATION
        if (((episode+1) % checkpointRate) == 0):
            valScores = []
            for e in range(validationEpisodes):
                state = env.reset()
                totalReward = 0
                done = False
                for step in range(maxStep):
                    if not done:
                        action = agent.chooseActionNoNoise(state)
                        n_state,reward,done, info = env.step(action)
                        if step is maxStep - 1:
                            done = True

                        state = n_state
                        totalReward += reward
                    if done:
                        break

                valScores.append(totalReward)

            if mean(valScores) > highScore:
                agent.saveCheckpoints("Agent{}_".format(arttir))
                highScore = mean(valScores)
        
            arttir +=1
            print('Validation Episode: ', (episode//checkpointRate)+1, ' Average Reward:', mean(valScores))
            writer.add_scalar('Validation Reward', mean(valScores), episode)
else:
    for e in range(validationEpisodes):
        state = env.reset()
        totalReward = 0
        done = False
        for step in range(maxStep):
            if not done:
                action = agent.chooseActionNoNoise(state)
                n_state,reward,done, info  = env.step(action)
                if step is maxStep - 1:
                    done = True

                state = n_state
                totalReward += reward
            if done:
                break

        print('Test  Reward:', totalReward)
