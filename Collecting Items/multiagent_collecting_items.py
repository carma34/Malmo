import MalmoPython
import json
import logging
import math
import os
import random
import sys
import time
import re
import uuid
from collections import namedtuple
from operator import add
import thread


save_images = False
if save_images:
    from PIL import Image
class StrategicAgent:
    """Estrategic Agent for discrete state/action spaces."""

    def __init__(self, actions=[]):
        self.actions = actions
        

    def act(self, world_state, agent_host, current_r,agent_index):
        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text) # most recent observation
        xPos=obs[u'XPos']
        zPos=obs[u'ZPos']
        num_items=0
        if obs.has_key('entities'):
            for item in obs[u'entities']:
                if 'Robot' not in item[u'name']:
                    num_items+=1
                    break
        if num_items==0 and obs.has_key('entities'):
            num_agent=int(obs[u'Name'][-1])-1
            if num_agent==0:
                command = str(dimension+0.5)+" 227.0 1.5"
            if num_agent==1:
                command = "1.5 227.0 "+str(dimension+0.5)
            if num_agent==2:
                command = "1.5 227.0 1.5"
            if num_agent==3:
                command = str(dimension+0.5)+" 227.0 "+str(dimension+0.5)
                

            agent_host.sendCommand("tp "+command)
            agent_host.sendCommand("quit")

        if agent_index == 1:
            close_item=[10,10]
            if obs.has_key('entities'):
                for item in obs[u'entities']:
                    #Items
                    if 'Robot' not in item[u'name']:
                        if (abs(close_item[0]) + abs(close_item[1])) > (abs(item[u'x'] - xPos) + abs(item[u'z'] - zPos)):
                            close_item = [item[u'x'] - xPos, item[u'z'] - zPos]
            # actionSet = ["movenorth 1", "movesouth 1", "movewest 1", "moveeast 1"]
            if abs(close_item[0]) > abs(close_item[1]):
                if close_item[0] < 0:
                    a = 2
                else:
                    a = 3
            else:
                if close_item[1] < 0:
                    a = 0
                else:
                    a = 1
        else:
            close_item=[10,10]
            if obs.has_key('entities'):
                for item in obs[u'entities']:
                    #Items
                    if 'Robot' not in item[u'name']:
                        if (abs(close_item[0]) + abs(close_item[1])) > (abs(item[u'x'] - xPos) + abs(item[u'z'] - zPos)):
                            close_item = [item[u'x'] - xPos, item[u'z'] - zPos]
            # actionSet = ["movenorth 1", "movesouth 1", "movewest 1", "moveeast 1"]
            if abs(close_item[0]) > abs(close_item[1]):
                if close_item[0] <= 0:
                    a = 2
                else:
                    a = 3
            else:
                if close_item[1] <= 0:
                    a = 0
                else:
                    a = 1
        agent_host.sendCommand(self.actions[a])
        time.sleep(0.2)
        return current_r

class TabQAgent:
    """Tabular Q-learning agent for discrete state/action spaces."""



    def __init__(self, actions=[],current_s_list=[0,0,0,0,0,0,0,0, 0,0,0,0, 0,0,0,0],
        epsilon=0.1, alpha=0.8, gamma=0.5, debug=False, num_items=8):

        self.epsilon = epsilon
        self.alpha = alpha
        self.gamma = gamma
        self.training = True
        self.current_s_list = current_s_list
        self.num_items = num_items

        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)
        self.logger.handlers = []
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        self.actions = actions
        self.q_table = {}


        self.rep = 0


    def loadModel(self, model_file):
        """load q table from model_file"""
        with open(model_file) as f:
            self.q_table = json.load(f)

    def training(self):
        """switch to training mode"""
        self.training = True


    def evaluate(self):
        """switch to evaluation mode (no training)"""
        self.training = False

    def act(self, world_state, agent_host, current_r,agent_index ):
        """take 1 action in response to the current world state"""

        obs_text = world_state.observations[-1].text
        obs = json.loads(obs_text) # most recent observation
        self.logger.debug(obs)
        num_items=0
        if obs.has_key('entities'):
            # print obs[u'entities']
            for item in obs[u'entities']:
                if 'Robot' not in item[u'name']:
                    num_items+=1
                    break

        if num_items==0 and obs.has_key('entities'):
            num_agent=int(obs[u'Name'][-1])-1
            if num_agent==0:
                command = str(dimension+0.5)+" 227.0 1.5"
            if num_agent==1:
                command = "1.5 227.0 "+str(dimension+0.5)
            if num_agent==2:
                command = "1.5 227.0 1.5"
            if num_agent==3:
                command = str(dimension+0.5)+" 227.0 "+str(dimension+0.5)
                

            agent_host.sendCommand("tp "+command)
            agent_host.sendCommand("quit")


        #states
        #   lava    close_items  far_items  agents
        #[N,S,W,E,   N,S,W,E,     N,S,W,E,  N,S,W,E]
        self.current_s_list=[0,0,0,0 ,0,0,0,0, 0,0,0,0, 0,0,0,0]
        xPos=obs[u'XPos']
        zPos=obs[u'ZPos']
        if obs.has_key('floor3x3'):
            if u'lava' in obs[u'floor3x3'][1]:
                self.current_s_list[0] = 1
            if u'lava' in obs[u'floor3x3'][7]:
                self.current_s_list[1] = 1
            if u'lava' in obs[u'floor3x3'][3]:
                self.current_s_list[2] = 1
            if u'lava' in obs[u'floor3x3'][5]:
                self.current_s_list[3] = 1

        if obs.has_key('entities'):
            for item in obs[u'entities']:
                #Items
                if 'Robot' not in item[u'name']:
                    if max([abs(item[u'x'] - xPos), abs(item[u'z'] - zPos)]) <= 2 and\
                        min([abs(item[u'x'] - xPos), abs(item[u'z'] - zPos)]) < 2:
                        if abs(item[u'x'] - xPos) >  abs(item[u'z'] - zPos):

                            if item[u'x'] > xPos:
                                self.current_s_list[7]+=1
                            else:
                                self.current_s_list[6]+=1

                        else:
                            if item[u'z'] > zPos:
                                self.current_s_list[5]+=1
                            else:
                                self.current_s_list[4]+=1
                    else:
                        if abs(item[u'x'] - xPos) >  abs(item[u'z'] - zPos):

                            if item[u'x'] > xPos:
                                self.current_s_list[11]+=1
                            else:
                                self.current_s_list[10]+=1

                        else:
                            if item[u'z'] > zPos:
                                self.current_s_list[9]+=1
                            else:
                                self.current_s_list[8]+=1

                else:
                    #Agents
                    if item[u'name'] != obs[u'Name']:
                        if item[u'x'] > xPos:
                            self.current_s_list[14]+=1
                        if item[u'x'] < xPos:
                            self.current_s_list[15]+=1
                        if item[u'z'] < zPos:
                            self.current_s_list[13]+=1
                        if item[u'z'] > zPos:
                            self.current_s_list[12]+=1


        current_s=str(self.current_s_list)
        self.logger.debug("State: %s" % current_s)
        if not self.q_table.has_key(current_s):
            self.q_table[current_s] = ([0] * len(self.actions))

        # update Q values
        if self.training and self.prev_s is not None and self.prev_a is not None:
            old_q = self.q_table[self.prev_s][self.prev_a]
            self.q_table[self.prev_s][self.prev_a] = old_q + self.alpha * (current_r
                + self.gamma * max(self.q_table[current_s]) - old_q)


        
        rnd = random.random()
        all_actions = [0,1,2,3]
        allowedActions=[]
        for action in all_actions:
            if not self.current_s_list[action]:
                allowedActions.append(action)

        if rnd < self.epsilon:
            a = random.choice(allowedActions)
        else:
            m = max([self.q_table[current_s][action] for action in allowedActions ])
            l = list()
            for x in allowedActions:
                if self.q_table[current_s][x] == m:
                    l.append(x)
            y = random.randint(0, len(l)-1)
            a = l[y]
               
        # send the selected action
        agent_host.sendCommand(self.actions[a])
        time.sleep(0.2)
        self.prev_s = current_s
        self.prev_a = a
        return current_r



EntityInfo = namedtuple('EntityInfo', 'x, y, z, yaw, pitch, name, colour, variation, quantity')
EntityInfo.__new__.__defaults__ = (0, 0, 0, 0, 0, "", "", "", 1)

# Create one agent host for parsing:
agent_hosts = [MalmoPython.AgentHost()]

# Parse the command-line options:
agent_hosts[0].addOptionalFlag( "debug,d", "Display debug information.")
agent_hosts[0].addOptionalFlag( "slow", "Slowly move")
agent_hosts[0].addOptionalFlag( "qs", "Q-Learning vs Strategic")
agent_hosts[0].addOptionalFlag( "ss", "Strategic vs Strategic")
agent_hosts[0].addOptionalFlag( "qq", "Q-Learning vs Q-Learning")
agent_hosts[0].addOptionalFlag( "evaluation", "Evaluation mode")
agent_hosts[0].addOptionalIntArgument("agents,n", "Number of agents to use, including observer.", 3)

agent_hosts[0].addOptionalFloatArgument('alpha',
    'Learning rate of the Q-learning agent.', 0.1)
agent_hosts[0].addOptionalFloatArgument('epsilon',
    'Exploration rate of the Q-learning agent.', 0.1)
agent_hosts[0].addOptionalFloatArgument('gamma', 'Discount factor.', 1.0)
agent_hosts[0].addOptionalFloatArgument('ep-dec', 'Epsilon decrementation.', 0.9)
agent_hosts[0].addOptionalIntArgument('dim', 'Odd dimension of terrain.', 9)
agent_hosts[0].addOptionalIntArgument('items', 'Number of items in the scene.', 8)
agent_hosts[0].addOptionalStringArgument('model_file', 'Path to the initial model file', '')

try:
    agent_hosts[0].parse( sys.argv )
except RuntimeError as e:
    print 'ERROR:',e
    print agent_hosts[0].getUsage()
    exit(1)
if agent_hosts[0].receivedArgument("help"):
    print agent_hosts[0].getUsage()
    exit(0)

DEBUG = agent_hosts[0].receivedArgument("debug")
INTEGRATION_TEST_MODE = agent_hosts[0].receivedArgument("test")
agents_requested = agent_hosts[0].getIntArgument("agents")
dimension = agent_hosts[0].getIntArgument("dim")
if dimension%2==0:
    print "Please use odd dimension"
    exit(0)

NUM_AGENTS = max(1, agents_requested-1) # Will be NUM_AGENTS robots running around, plus one static observer.
NUM_ITEMS = agent_hosts[0].getIntArgument("items")

# Create the rest of the agent hosts - one for each robot:
agent_hosts += [MalmoPython.AgentHost() for x in xrange(1, NUM_AGENTS+1) ]

# Set up debug output:
for ah in agent_hosts:
    ah.setDebugOutput(DEBUG)    # Turn client-pool connection messages on/off.

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)  # flush print output immediately

def agentName(i):
    return "Robot#" + str(i + 1)

def agentPos(i):
    xml=''
    if i==0:
        xml+='''<Placement x="'''+str(dimension+0.5)+'''" y="227.0" z="1.5" pitch="30" yaw="0"/>'''
    if i==1:
        xml+='''<Placement x="1.5" y="227.0" z="'''+str(dimension+0.5)+'''" pitch="30" yaw="0"/>'''
    if i==2:
        xml+='''<Placement x="1.5" y="227.0" z="1.5" pitch="30" yaw="0"/>'''
    if i==3:
        xml+='''<Placement x="'''+str(dimension+0.5)+'''" y="227.0" z="'''+str(dimension+0.5)+'''" pitch="30" yaw="0"/>'''


    return xml

def startMission(agent_host, my_mission, my_client_pool, my_mission_record, role, expId):
    max_retries = 3
    for retry in range(max_retries):
        try:
            # Attempt to start the mission:
            agent_host.startMission( my_mission, my_client_pool, my_mission_record, role, expId )
            break
        except RuntimeError as e:
            if retry == max_retries - 1:
                print "Error starting mission",e
                print "Is the game running?"
                exit(1)
            else:
                # In a multi-agent mission, startMission will fail if the integrated server
                # hasn't yet started - so if none of our clients were available, that may be the
                # reason. To catch this specifically we could check the results for "MALMONOSERVERYET",
                # but it should be sufficient to simply wait a bit and try again.
                time.sleep(5)




def GetMissionXML(summary,reset, itemDrawingXML,mission_no):
    ''' Build an XML mission string that uses the RewardForCollectingItemQLearning mission handler.'''

    xml= '''<?xml version="1.0" encoding="UTF-8"  standalone="no" ?>
    <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <About>
            <Summary>''' + summary + '''</Summary>
        </About>

        <ServerSection>
            <ServerInitialConditions>
                <Time>
                    <StartTime>6000</StartTime>
                    <AllowPassageOfTime>false</AllowPassageOfTime>
                </Time>
                <Weather>clear</Weather>
                <AllowSpawning>false</AllowSpawning>
            </ServerInitialConditions>
            <ServerHandlers>
                <FlatWorldGenerator forceReset="'''+reset+'''" generatorString="3;7,220*1,5*3,2;3;,biome_1" />
                <DrawingDecorator>
                    ''' + floor(dimension,dimension) + '''
                    ''' + itemDrawingXML + '''
                    <DrawBlock x="'''+str(dimension/2+1)+'''" y="'''+str(dimension+224) +'''" z="'''+str(dimension/2+1)+'''" type="fence"/>
                </DrawingDecorator>
                <ServerQuitFromTimeUp timeLimitMs="60000"/>
            </ServerHandlers>
        </ServerSection>
        '''

    for i in range(NUM_AGENTS):
        xml += '''
          <AgentSection mode="Survival">
            <Name>''' + agentName(i) + '''</Name>
            <AgentStart>
                '''+agentPos(i)+'''
                <Inventory>
                </Inventory>
            </AgentStart>
            <AgentHandlers>
                <DiscreteMovementCommands/>
                <AbsoluteMovementCommands/>
                <MissionQuitCommands/>
                <ObservationFromNearbyEntities>
                    <Range name="entities" xrange="'''+str(dimension)+'''" yrange="2" zrange="'''+str(dimension)+'''"/>
                </ObservationFromNearbyEntities>
                <ObservationFromGrid>
                    <Grid name="floor3x3">
                        <min x="-1" y="-1" z="-1"/>
                        <max x="1" y="-1" z="1"/>
                    </Grid>
                </ObservationFromGrid>
                <ObservationFromFullStats/>
                <VideoProducer>
                    <Width>480</Width>
                    <Height>320</Height>
                </VideoProducer>
                <RewardForCollectingItem>
                    <Item reward="10" type="potato"/>
                </RewardForCollectingItem>
                  <RewardForTouchingBlockType>
                    <Block reward="-100.0" type="lava" behaviour="onceOnly"/>
                  </RewardForTouchingBlockType>
                  <RewardForSendingCommand reward="-1"/>
                    <AgentQuitFromTouchingBlockType>
                    <Block type="lava" />
                </AgentQuitFromTouchingBlockType>
            </AgentHandlers>
        </AgentSection>
        '''
    xml += '''<AgentSection mode="Creative">
        <Name>TheWatcher</Name>
        <AgentStart>
          <Placement x="'''+str(dimension/2+1.5)+'''" y="'''+str(dimension+226) +'''" z="'''+str(dimension/2+1.5)+'''" pitch="90"/>
        </AgentStart>
        <AgentHandlers>
          <ContinuousMovementCommands turnSpeedDegs="360"/>
          <MissionQuitCommands/>
          <VideoProducer>
            <Width>640</Width>
            <Height>640</Height>
          </VideoProducer>
        </AgentHandlers>
      </AgentSection>'''

    xml += '</Mission>'
    # print xml
    return xml

def floor(x,z):
    xml=""
    xml+='<DrawCuboid x1="-1" y1="226" z1="-1" x2="'+str(x+2)+'" y2="228" z2="'+str(z+2)+'" type="air" />\n'
    xml+='<DrawCuboid x1="-1" y1="226" z1="-1" x2="'+str(x+2)+'" y2="225" z2="'+str(z+2)+'" type="lava" />\n'
    for i in range(1,x+1):
        for j in range(1,z+1):
            if i%2==0:
                if j%2==0:
                    xml+='''<DrawBlock x="'''+ str(i) +'''" y="226" z="'''+ str(j) +'''" type="end_stone" />\n'''
                else:
                    xml+='''<DrawBlock x="'''+ str(i) +'''" y="226" z="'''+ str(j) +'''" type="sandstone" />\n'''
            else:
                if j%2==0:
                    xml+='''<DrawBlock x="'''+ str(i) +'''" y="226" z="'''+ str(j) +'''" type="sandstone" />\n'''
                else:
                    xml+='''<DrawBlock x="'''+ str(i) +'''" y="226" z="'''+ str(j) +'''" type="end_stone" />\n'''

    return xml

def GetItemDrawingXMLRandom():
    ''' Build an XML string that contains 400 randomly positioned bits of food'''
    xml=""
    itemPos=[]
    dist=[0,0]
    avoidedPositions = [(dimension,dimension), (dimension-1,dimension),
                (dimension,dimension-1), (dimension-1,dimension-1),
                (dimension,1), (dimension-1,1),
                (dimension,2), (dimension-1,2),
                (1,1), (1,2), (2,1), (2,2),
                (1,dimension),(1,dimension-1),
                (2,dimension),(2,dimension-1)
                ]
    type = "potato"
    
   
    if NUM_AGENTS<3:
        while len(itemPos)<(NUM_ITEMS):
            z = random.randint(1,dimension)
            x = random.randint(1,dimension)
            if (x,z) not in itemPos and (int(x),int(z)) not in avoidedPositions and x!=z:
                itemPos.insert(0,(x,z))
                itemPos.insert(0,(dimension+1-x, dimension+1-z))
                xml += '''<DrawItem x="''' + str(x) + '''" y="227" z="''' + str(z) + '''" type="''' + type + '''"/>'''
                xml += '''<DrawItem x="''' + str(dimension+1-x) + '''" y="227" z="''' + str(dimension+1-z) + '''" type="''' + type + '''"/>'''
    else:
        while len(itemPos)<(NUM_ITEMS):
            z = random.randint(1,dimension/2)
            x = random.randint(1,dimension/2)
            if (x,z) not in itemPos and (int(x),int(z)) not in avoidedPositions:
                itemPos.insert(0,(x,z))
                itemPos.insert(0,(dimension+1-x, dimension+1-z))
                itemPos.insert(0,(z, dimension+1-x))
                itemPos.insert(0,(dimension+1-z, x))
                xml += '''<DrawItem x="''' + str(x) + '''" y="227" z="''' + str(z) + '''" type="''' + type + '''"/>'''
                xml += '''<DrawItem x="''' + str(dimension+1-x) + '''" y="227" z="''' + str(dimension+1-z) + '''" type="''' + type + '''"/>'''
                xml += '''<DrawItem x="''' + str(z) + '''" y="227" z="''' + str(dimension+1-x) + '''" type="''' + type + '''"/>'''
                xml += '''<DrawItem x="''' + str(dimension+1-z) + '''" y="227" z="''' + str(x) + '''" type="''' + type + '''"/>'''
    return xml



# Set up a client pool.
# IMPORTANT: If ANY of the clients will be on a different machine, then you MUST
# make sure that any client which can be the server has an IP address that is
# reachable from other machines - ie DO NOT SIMPLY USE 127.0.0.1!!!!
# The IP address used in the client pool will be broadcast to other agents who
# are attempting to find the server - so this will fail for any agents on a
# different machine.
client_pool = MalmoPython.ClientPool()
for x in xrange(10000, 10000 + NUM_AGENTS+1):
    client_pool.add( MalmoPython.ClientInfo('127.0.0.1', x) )


# -- set up the agent -- #
actionSet = ["movenorth 1", "movesouth 1", "movewest 1", "moveeast 1"]
agents = []
cumulative_rewards = []
for a in range(NUM_AGENTS):
    cumulative_rewards.insert(0,[])

cumulative_reward = []
for a in range(NUM_AGENTS):
    cumulative_reward.insert(0,0)


num_missions = 1

for mission_no in range(num_missions):
    print "Running mission #" + str(mission_no)
    for a in range(NUM_AGENTS):
        cumulative_rewards[a].insert(mission_no,[])
    for a in range(NUM_AGENTS):
        agents.insert(0,[])
    if agent_hosts[0].receivedArgument("ss"):
        agents[0] = StrategicAgent(actions=actionSet)
        agents[1] = StrategicAgent(actions=actionSet)

    elif agent_hosts[0].receivedArgument("qs"):
        agents[0] = TabQAgent(
            actions=actionSet,
            epsilon=agent_hosts[0].getFloatArgument('epsilon'),
            alpha=agent_hosts[0].getFloatArgument('alpha'),
            gamma=agent_hosts[0].getFloatArgument('gamma'),
            debug = agent_hosts[0].receivedArgument("debug")
            )
        if agent_hosts[0].receivedArgument("evaluation"):
                agents[0].evaluate()
                agents[0].loadModel("qtable_collecting_items_agent_"+str(0)+".txt")
        agents[1] = StrategicAgent(actions=actionSet)
    
    elif agent_hosts[0].receivedArgument("qq"):
        for a in range(NUM_AGENTS):
            agents[a] = TabQAgent(
            actions=actionSet,
            epsilon=agent_hosts[0].getFloatArgument('epsilon'),
            alpha=agent_hosts[0].getFloatArgument('alpha'),
            gamma=agent_hosts[0].getFloatArgument('gamma'),
            debug = agent_hosts[0].receivedArgument("debug")
            )
            if agent_hosts[0].receivedArgument("evaluation"):
                agents[a].evaluate()
                agents[a].loadModel("qtable_collecting_items_agent_"+str(a)+".txt")
    
    # Generate an experiment ID for this mission.
    # This is used to make sure the right clients join the right servers -
    # if the experiment IDs don't match, the startMission request will be rejected.
    # In practice, if the client pool is only being used by one researcher, there
    # should be little danger of clients joining the wrong experiments, so a static
    # ID would probably suffice, though changing the ID on each mission also catches
    # potential problems with clients and servers getting out of step.

    # Note that, in this sample, the same process is responsible for all calls to startMission,
    # so passing the experiment ID like this is a simple matter. If the agentHosts are distributed
    # across different threads, processes, or machines, a different approach will be required.
    # (Eg generate the IDs procedurally, in a way that is guaranteed to produce the same results
    # for each agentHost independently.)
    # experimentID = str(uuid.uuid4())
    # expID = str(uuid.uuid4())
    expID = "multiagent_collecting_items"


    itemdrawingxml = GetItemDrawingXMLRandom()
    num_repeats = 5
    for i in range(num_repeats):
        print "\nMap %d - Mission %d of %d:" % ( mission_no, i+1, num_repeats )
        # Create mission xml - use forcereset if this is the first mission.
        my_mission = MalmoPython.MissionSpec(GetMissionXML("Collecting items run #" + str(mission_no), "true" if i == 0 else "false", itemdrawingxml,mission_no),True)

        for p in range(len(agent_hosts)):
            my_mission_record = MalmoPython.MissionRecordSpec( "./Records/save_%s-map%d-rep%d-agent%d.tgz" % (expID, mission_no, i,p) )
            my_mission_record.recordCommands()
            if p == len(agent_hosts)-1:
                my_mission_record.recordMP4(20, 400000)
            my_mission_record.recordRewards()
            my_mission_record.recordObservations()
            startMission(agent_hosts[p], my_mission, client_pool,  my_mission_record, p,"%s-%d" % (expID, mission_no))

        # Wait for mission to start - complicated by having multiple agent hosts, and the potential
        # for multiple errors to occur in the start-up process.
        print "Waiting for the mission to start ",
        hasBegun = False
        hadErrors = False
        while not hasBegun and not hadErrors:
            sys.stdout.write(".")
            time.sleep(0.1)
            for ah in agent_hosts:
                world_state = ah.getWorldState()
                if world_state.has_mission_begun:
                    hasBegun = True
                if len(world_state.errors):
                    hadErrors = True
                    print "Errors from agent " + agentName(agent_hosts.index(ah))
                    for error in world_state.errors:
                        print "Error:",error.text

        if hadErrors:
            print "ABORTING"
            exit(1)

        time.sleep(1)
        # When an agent is killed, it stops getting observations etc. Track this, so we know when to bail.
        unresponsive_count = [10 for x in range(NUM_AGENTS)]
        num_responsive_agents = lambda: sum([urc > 0 for urc in unresponsive_count])
        timed_out = False

        total_reward = [0 for x in range(NUM_AGENTS)]
        current_r = [0 for x in range(NUM_AGENTS)]
        prev_x = [0 for x in range(NUM_AGENTS)]
        prev_z = [0 for x in range(NUM_AGENTS)]


        tol = 0.01
        for a in agents:
            a.prev_s = None
            a.prev_a = None
        if mission_no % 1 == 0:
            agents_order = range(NUM_AGENTS)
        else:
            agents_order =  list(reversed(range(NUM_AGENTS)))
        for a in agents_order:
            # wait for a valid observation
            world_state = agent_hosts[a].peekWorldState()
            while world_state.is_mission_running and all(e.text=='{}' for e in world_state.observations):
                world_state = agent_hosts[a].peekWorldState()
            world_state = agent_hosts[a].getWorldState()
            for err in world_state.errors:
                print err
            obs = json.loads( world_state.observations[-1].text )
            prev_x[a] = obs['XPos']
            prev_z[a] = obs['ZPos']
            
            total_reward[a] += agents[a].act(world_state,agent_hosts[a],current_r[a],a)

            if agent_hosts[0].receivedArgument("qs") and agent_hosts[0].receivedArgument("ep-dec") and i < num_repeats*agent_hosts[0].getFloatArgument('ep-dec'):
                if a == 0:
                    agents[a].epsilon -= agent_hosts[0].getFloatArgument('epsilon')/(num_repeats)

            if agent_hosts[0].receivedArgument("qq") and agent_hosts[0].receivedArgument("ep-dec") and i < num_repeats*agent_hosts[0].getFloatArgument('ep-dec'):
                agents[a].epsilon -= agent_hosts[0].getFloatArgument('epsilon')/(num_repeats*agent_hosts[0].getFloatArgument('ep-dec'))

            require_move = True

        #main loop
        while num_responsive_agents() > 0 and not timed_out:
            for j in agents_order:
                # wait for the position to have changed and a reward received
                # print 'Waiting for data...', j
                while unresponsive_count[j] > 0:
                    world_state = agent_hosts[j].peekWorldState()
                    if not world_state.is_mission_running:
                        print 'mission ended.'
                        timed_out = True
                        break
                    if len(world_state.rewards) > 0 and not all(e.text=='{}' for e in world_state.observations):
                        obs = json.loads( world_state.observations[-1].text )
                        unresponsive_count[j] = 10
                        curr_x = obs['XPos']
                        curr_z = obs['ZPos']
                        if require_move:
                            if math.hypot( curr_x - prev_x[j], curr_z - prev_z[j] ) > tol:
                                # print 'received.'
                                break
                        else:
                            # print 'received.'
                            break
                    else:
                        time.sleep(0.05)
                        unresponsive_count[j] -=1
                if unresponsive_count[j]<=0:
                    continue

                world_state = agent_hosts[j].getWorldState()
                for err in world_state.errors:
                    print err

                current_r[j] = sum(r.getValue() for r in world_state.rewards)

                if world_state.is_mission_running:
                    obs = json.loads( world_state.observations[-1].text )
                    curr_x = obs['XPos']
                    curr_z = obs['ZPos']
                    prev_x[j] = curr_x
                    prev_z[j] = curr_z

                    if agent_hosts[0].receivedArgument("slow"):
                        time.sleep(2)

                    # act
                    total_reward[j] += agents[j].act(world_state, agent_hosts[j], current_r[j],j)
            time.sleep(0.05)


        if not timed_out:
            # All agents except the watcher have died.
            # We could wait for the mission to time out, but it's quicker
            # to make the watcher quit manually:
            agent_hosts[-1].sendCommand("quit")
        time.sleep(1)
        print "Waiting for mission to end ",
        for k in range(NUM_AGENTS):
            world_state = agent_hosts[k].getWorldState()
            for err in world_state.errors:
                print err

            current_r[k] = sum(r.getValue() for r in world_state.rewards)

            # process final reward
            total_reward[k] += current_r[k]
            cumulative_rewards[k][mission_no] += [ total_reward[k] ]

            if agent_hosts[0].receivedArgument("qs"):
                # update Q values
                if agents[0].training and agents[0].prev_s is not None and agents[0].prev_a is not None:
                    old_q = agents[0].q_table[agents[0].prev_s][agents[0].prev_a]
                    agents[0].q_table[agents[0].prev_s][agents[0].prev_a] = old_q + agents[0].alpha * ( current_r[0] - old_q )

            elif agent_hosts[0].receivedArgument("qq"):
                # update Q values
                if agents[k].training and agents[k].prev_s is not None and agents[k].prev_a is not None:
                    old_q = agents[k].q_table[agents[k].prev_s][agents[k].prev_a]
                    agents[k].q_table[agents[k].prev_s][agents[k].prev_a] = old_q + agents[k].alpha * ( current_r[k] - old_q )

        time.sleep(0.05)
        # Mission should have ended already, but we want to wait until all the various agent hosts
        # have had a chance to respond to their mission ended message.
        hasEnded = False
        while not hasEnded:
            hasEnded = True # assume all good
            sys.stdout.write(".")
            time.sleep(0.1)
            for ah in agent_hosts:
                world_state = ah.getWorldState()
                if world_state.is_mission_running:
                    hasEnded = False # all not good
        time.sleep(2)
        if agent_hosts[0].receivedArgument("qs"):
            if agents[0].training:
                with open('qtable_collecting_items_agent_'+str(0)+'.txt', 'w') as outfile:
                    json.dump(agents[0].q_table, outfile)

        elif agent_hosts[0].receivedArgument("qq"):
            for agent_index in range(len(agents)):
                if agents[agent_index].training:
                    with open('qtable_collecting_items_agent_'+str(agent_index)+'.txt', 'w') as outfile:
                        json.dump(agents[agent_index].q_table, outfile)
        with open('cumulative_rewards_c_i.txt', 'w') as outfile:
            json.dump(cumulative_rewards, outfile)

    print "Done."
    print "Cumulative rewards for all %d runs:" % num_repeats
    print cumulative_rewards

    time.sleep(2)
