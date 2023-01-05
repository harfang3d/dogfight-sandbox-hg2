import numpy as np
import dogfight_client as df
from Constants import *
import gym

class HarfangEnv():
    def __init__(self):      
        self.done = False
        self.loc_diff = 0
        self.action_space = gym.spaces.Box(low=np.array([-1.0,-1.0,-1.0]), high=np.array([1.0,1.0,1.0]), dtype=np.float64)
        self.Plane_ID_oppo = "ennemy_2" # Opponent aircrafts name
        self.Plane_ID_ally   = "ally_1" # our aircrafts name
        self.Aircraft_Loc = None
        self.Ally_target_locked = None
        self.reward = 0     
        self.Plane_Irtifa = 0
        self.plane_heading = 0
        self.plane_heading_2 = 0

    def reset(self): # reset simulation beginning of episode
        self.done = False
        state_ally = self._get_observation() # get observations
        self._reset_machine()
        df.set_target_id(self.Plane_ID_ally, self.Plane_ID_oppo) # set target, for firing missile

        return state_ally

    def step(self, action_ally):
        self._apply_action(action_ally) # apply neural networks output
        state_ally = self._get_observation() # in each step, get observation
        self._get_reward() # get reward value
        self._get_termination() # check termination conditions

        return state_ally,self.reward,self.done, {}

            
    def _get_reward(self): 
        self.reward =0
        self._get_loc_diff() # get location difference information for reward
        self.reward -= (0.0001* (self.loc_diff))

        if self.loc_diff<500:
            self.reward += 1000

        if self.plane_heading>180:
            deger_1 = (self.plane_heading-360)
        else:
            deger_1 = self.plane_heading


        if self.plane_heading_2>180:
            deger_2 = (self.plane_heading_2-360)
        else:
            deger_2 = self.plane_heading_2
        self.reward -= abs(deger_1-deger_2)/90

        if self.Plane_Irtifa < 2000:
            self.reward -= 4

        if self.Plane_Irtifa > 7000:
            self.reward -= 4



    def _apply_action(self,action_ally):
        df.set_plane_pitch(self.Plane_ID_ally, float(action_ally[0]))
        df.set_plane_roll(self.Plane_ID_ally, float(action_ally[1]))
        df.set_plane_yaw(self.Plane_ID_ally, float(action_ally[2]))

        df.set_plane_pitch(self.Plane_ID_oppo, float(0))
        df.set_plane_roll(self.Plane_ID_oppo, float(0))
        df.set_plane_yaw(self.Plane_ID_oppo, float(0))
        df.update_scene()
        if self.Ally_target_locked:
            df.fire_missile(self.Plane_ID_ally,0)

        


    def _get_termination(self):
        if self.loc_diff <300 :
            self.done = True
        if self.Plane_Irtifa < 500 or self.Plane_Irtifa > 10000 :
            self.done=True


    def _reset_machine(self):
        df.set_health("ennemy_2",1)
        df.reset_machine_matrix(self.Plane_ID_oppo, 0, 4200, 0, 0, 0, 0)
        df.reset_machine_matrix(self.Plane_ID_ally, 0, 3500, -4000, 0, 0, 0)

        df.set_plane_thrust(self.Plane_ID_ally,1)
        df.set_plane_thrust(self.Plane_ID_oppo, 0.6)
        df.set_plane_linear_speed(self.Plane_ID_ally,300)
        df.set_plane_linear_speed(self.Plane_ID_oppo, 200)
        df.retract_gear(self.Plane_ID_ally)
        df.retract_gear(self.Plane_ID_oppo)

    def _get_loc_diff(self):
        self.loc_diff = (((self.Aircraft_Loc[0] - self.Oppo_Loc[0]) ** 2) + ((self.Aircraft_Loc[1] - self.Oppo_Loc[1]) ** 2) + ((self.Aircraft_Loc[2] - self.Oppo_Loc[2]) ** 2)) ** (1 / 2)
    
    def  _get_observation(self):
        # Plane States
        plane_state = df.get_plane_state(self.Plane_ID_ally)
        Plane_Pos = [plane_state["position"][0] / NormStates["Plane_position"],
                     plane_state["position"][1] / NormStates["Plane_position"],
                     plane_state["position"][2] / NormStates["Plane_position"]]
        Plane_Euler = [plane_state["Euler_angles"][0] / NormStates["Plane_Euler_angles"],
                       plane_state["Euler_angles"][1] / NormStates["Plane_Euler_angles"],
                       plane_state["Euler_angles"][2] / NormStates["Plane_Euler_angles"]]
        Plane_Heading = plane_state["heading"] / NormStates["Plane_heading"]
        
        # Opponent States
        Oppo_state = df.get_plane_state(self.Plane_ID_oppo)

        Oppo_Pos = [Oppo_state["position"][0] / NormStates["Plane_position"],
                       Oppo_state["position"][1] / NormStates["Plane_position"],
                       Oppo_state["position"][2] / NormStates["Plane_position"]]
        Oppo_Heading = Oppo_state["heading"] / NormStates["Plane_heading"]
        Oppo_Pitch_Att = Oppo_state["pitch_attitude"] / NormStates["Plane_pitch_attitude"]
        Oppo_Roll_Att = Oppo_state["roll_attitude"] / NormStates["Plane_roll_attitude"]
        
        self.plane_heading_2 = Oppo_state["heading"]        
        self.plane_heading = plane_state["heading"]-Oppo_state["heading"]
        self.Plane_Irtifa = plane_state["position"][1]
        self.Aircraft_Loc = plane_state["position"]
        self.Oppo_Loc  = Oppo_state["position"]
        self.Ally_target_locked = plane_state["target_locked"]

        target_angle = plane_state['target_angle']/360
        Pos_Diff = [Plane_Pos[0]-Oppo_Pos[0],Plane_Pos[1]-Oppo_Pos[1],Plane_Pos[2]-Oppo_Pos[2]]

        States = np.concatenate((Pos_Diff, Plane_Euler, Plane_Heading,
                                 Oppo_Heading,Oppo_Pitch_Att,Oppo_Roll_Att ,target_angle), axis=None)

        return States


