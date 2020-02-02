'''
Load balancer classes.
We will define an abstract class, and then some types of LB such as random, round robin, optimal etc.
Mark's LB algorithm will be added right here.
'''
import os
from abc import ABC, abstractmethod
import random
from typing import Optional, TYPE_CHECKING

from load_client.global_vars import lb_filename
from load_client.pie_file_data_parser import PieDataParser, get_queue_state_index
from load_client.servers_management import ServerManager, Server, SERVER_STATE_AVAILABLE
#from load_client.sim_exec_manager import SimExecManager


class BasicLB(ABC):
    def __init__(self, sim_mgr:'SimExecManager'):
        self.sim_manager = sim_mgr
        self.srv_manager:ServerManager = sim_mgr.srv_mgr

    @abstractmethod
    def pick_server(self)->Server:
        pass


class RandomLB(BasicLB):
    def pick_server(self)->Server:
        server_index = random.randint(0, len(self.srv_manager.available_srv_list) - 1)
        return self.srv_manager.available_srv_list[server_index]

class RoundRobinLB(BasicLB):
    curr_srv:int=0
    def pick_server(self)->Server:
        self.curr_srv += 1
        if self.curr_srv>=len(self.srv_manager.available_srv_list):
            self.curr_srv=0
        return self.srv_manager.available_srv_list[self.curr_srv]

class JsqLB(BasicLB):
    '''
    Find the shortest queue from all available servers, and return it
    '''
    def pick_server(self)->Optional[Server]:
        min_length:int = 9999
        curr_srv: Optional[Server] = None
        for server in self.srv_manager.available_srv_list:
            num = server.current_running_tasks
            self.sim_manager.logger.debug("Queue length for server %s is %d" % (server.srv_port, num))
            if num<min_length:
                # Set the current server as the favorite pick
                min_length = num
                curr_srv = server

        if curr_srv:
            self.sim_manager.logger.debug ("Picked server %d with %d tasks" % (curr_srv.srv_port, num))
            return curr_srv
        else:
            self.sim_manager.logger.debug ("No available servers")
            return None

class BellmanLB(BasicLB):
    def __init__(self, mgr):
        super ().__init__ (mgr)
        pie_file: str = mgr.simulation_params.pie_file
        self.data_parser:PieDataParser = PieDataParser()

        # Start a separate file, and write in the LB scale in mapping
        filename = os.path.join(self.sim_manager.res_path, lb_filename)
        f = open (filename, "w")

        for index in range(len(self.data_parser.load_balance_policy_list)):
            op = self.data_parser.load_balance_policy_list[index]
            if  op == -2:
                continue
            elif op == -1:
                index_str = str(index).zfill(5)
                f.write(index_str + "-->REJECT!!\n")
            else:
                index_str = str(index).zfill(5)
                f.write (index_str + "-->Send to " + str(op) + "\n")
        f.close()


    def get_available_servers_vec(self)->str:
        ret_str = ''
        for server in self.srv_manager.full_srv_list:
            if server.running_state == SERVER_STATE_AVAILABLE:
                ret_str+='1'
            else:
                ret_str+='0'
        return ret_str

    def get_current_running_tasks_vec(self)->str:
        ret_str = ''
        for server in self.srv_manager.full_srv_list:
            ret_str+=str(server.current_running_tasks)
        return ret_str

    def pick_server(self)->Optional[Server]:
        queue_state_index = get_queue_state_index (self.srv_manager)
        srv_index = self.data_parser.load_balance_policy_list[queue_state_index]

        # If we need to reject, let's do it now
        if srv_index == -1:
            self.sim_manager.logger.debug ("REJECTING BY POLICY: queue_state_index " + \
                                           str(queue_state_index).zfill(self.data_parser.num_of_servers))
            return None

        self.sim_manager.logger.debug ("index is " + str(queue_state_index).zfill(self.data_parser.num_of_servers) + \
                                       " picked server is: " + str(srv_index) + \
                                       " current available servers: " + str(self.get_available_servers_vec ()) + \
                                       " current server queue: " + str(self.get_current_running_tasks_vec ()))

        server:Server =  self.srv_manager.full_srv_list[srv_index]

        # Check if the server is available
        if server.running_state!= SERVER_STATE_AVAILABLE:
            self.sim_manager.logger.debug ("REJECTING BY STATE: server " + str(srv_index) + \
                                           " running state: " + str(server.running_state))
            return None

        return server

def create_lb_obj(lb_type, mgr)->BasicLB: #TODO Throw exception for type mismatch
    if lb_type == "random":
        return RandomLB(mgr)
    if lb_type == "round_robin":
        return RoundRobinLB(mgr)
    if lb_type == "jsq":
        return JsqLB(mgr)
    if lb_type == "bellman":
        return BellmanLB(mgr)
