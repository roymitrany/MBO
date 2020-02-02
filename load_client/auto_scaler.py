'''
Auto scaler classes.
We will define an abstract class, and then some types of auto scaler, such as high and low threshold.
Mark's LB algorithm will be added right here.
'''
import os
from abc import ABC, abstractmethod
from time import time

from load_client.global_vars import max_server_queue_len, as_high_threshold, as_low_threshold, scale_in_filename, \
    scale_out_filename
from load_client.pie_file_data_parser import  PieDataParser, get_queue_state_index
from load_client.servers_management import SERVER_STATE_AVAILABLE
#from load_client.sim_exec_manager import SimExecManager


class BasicAS(ABC):

    def __init__(self, sim_mgr):
        self.sim_manager = sim_mgr
        self.srv_manager = sim_mgr.srv_mgr


    @abstractmethod
    def trigger_scale_in(self, srv_index):
        pass

    @abstractmethod
    def trigger_scale_out(self):
        pass

class DumbAS(BasicAS):

    def trigger_scale_in(self, srv_index):
        return

    def trigger_scale_out(self):
        return



class ThresholdAS(BasicAS):
    last_scale_change = time ()

    def trigger_scale_in(self, srv_index):
        self.trigger_scale_in_out()

    def trigger_scale_out(self):
        self.trigger_scale_in_out()

    def trigger_scale_in_out(self):
        # check if we should do some scaling work. The code is pretty much the same for both sides, so we better
        # implement it once and pay the price of one unnecessary if
        overall_possible_tasks = len(self.srv_manager.available_srv_list) * max_server_queue_len
        overall_current_tasks = 0
        # Count the current number of tasks
        for server in self.srv_manager.active_srv_list:
            overall_current_tasks += server.current_running_tasks

        # If number of active servers is smaller than the number of available servers, probably we already stopped
        # a server, so do not stop another one
        if len(self.srv_manager.active_srv_list)!=len(self.srv_manager.available_srv_list):
            self.sim_manager.logger.debug(" Num of active servers: " +
                                          str(len(self.srv_manager.active_srv_list)) +
                                          " Num of available servers: " +
                                          str(len(self.srv_manager.available_srv_list)))
            return


        # If we number of tasks is above threshold, scale out
        if overall_current_tasks>as_high_threshold*overall_possible_tasks:
            # If to little time passed since last change, do nothing
            last_change_delta = time () - self.last_scale_change
            if last_change_delta < self.srv_manager.cool_down_period:
                self.sim_manager.logger.debug("Too soon to start a server. Time from last change: " + str(last_change_delta))
                return

            self.srv_manager.scale_out()
            self.last_scale_change = time ()

        if overall_current_tasks<as_low_threshold*overall_possible_tasks:
            last_change_delta = time () - self.last_scale_change
            if last_change_delta < self.srv_manager.cool_down_period*2:
                self.sim_manager.logger.debug("Too soon to stop a server. Time from last change: " + str(last_change_delta))
                return

            # Do not delete the last server
            if len (self.srv_manager.available_srv_list) <= 3:
                return

            self.srv_manager.scale_in()
            self.last_scale_change = time ()

class BellmanAS(BasicAS):

    def __init__(self, mgr:'SimExecManager'):
        super ().__init__ (mgr)
        pie_file: str = mgr.simulation_params.pie_file
        self.data_parser:PieDataParser = PieDataParser(pie_file)

        self.print_scale_in_file()


        # Another separate file for AS scale out mapping
        filename = os.path.join(self.sim_manager.res_path, scale_out_filename)
        f = open (filename, "w")

        for index in range(len(self.data_parser.scale_out_policy_list)):
            op = self.data_parser.scale_out_policy_list[index]
            if  op == 1:
                f.write(str(index) + "--> Scale out!!\n")
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

    def trigger_scale_in(self, srv_index):

        # get index out of servers queue
        index = get_queue_state_index (self.srv_manager) # TODO manipulate index to take the one where current server has one task more than indicated

        # UGLY PATCH: increment 1 for the current server to match with pie (mark reduces the queue length only after scale in decision)
        # But the index can't exceed the max queue len don't do this trick
        if int(str(index).zfill (5)[srv_index]) < PieDataParser.queue_length:
            index = index + 10**(4-srv_index)


        op = self.data_parser.scale_in_policy_list[index]
        self.sim_manager.logger.debug ("Index is " + str (index) + \
                                      " op is: " + str (op) + \
                                      " current available servers: " + self.get_available_servers_vec () + \
                                      " current running tasks: " + self.get_current_running_tasks_vec ())
        self.sim_manager.logger.debug(" scale in for server " + str(srv_index) + " queue size " + str(self.srv_manager.full_srv_list[srv_index].current_running_tasks))
        if (int(op[srv_index])==1) and (self.srv_manager.full_srv_list[srv_index].current_running_tasks ==0):
            self.sim_manager.logger.info ("---------Bellman scale in: index is " + str (index) +  \
                                           " op is: " + str (op) + \
                                           " current available servers: " + self.get_available_servers_vec () + \
                                           " current running tasks: " + self.get_current_running_tasks_vec ())
            self.srv_manager.scale_in(srv_index)

    def trigger_scale_out(self):

        index = get_queue_state_index (self.srv_manager)
        op = self.data_parser.scale_out_policy_list[index]
        if op>0:
            self.sim_manager.logger.info ("+++++++++Bellman scale out: index is " + str (index))
            self.srv_manager.scale_out()

    def print_scale_in_file(self):
        # Start a separate file, and write in the AS scale in mapping
        filename = os.path.join(self.sim_manager.res_path, scale_in_filename)
        f = open (filename, "w")

        num_of_scale_ins=0
        num_of_ignores=0
        highest_scale_in_num_of_tasks = 0
        for index in range(len(self.data_parser.scale_in_policy_list)):
            op = self.data_parser.scale_in_policy_list[index]
            if  op == "":
                continue
            else:
                scale_in_str = str(index).zfill(5)
                empty_server = scale_in_str.find("3")
                if empty_server>=0:
                    do_scale_in = op[empty_server]
                    if do_scale_in=='1':
                        total_tasks = -1 # delete one for the task that just completed
                        total_active_servers = 0
                        for i in range(len(scale_in_str)):
                            if int(scale_in_str[i])>=2:
                                total_active_servers+=1
                                total_tasks+=(int(scale_in_str[i])-2)
                                if total_tasks>highest_scale_in_num_of_tasks:
                                    highest_scale_in_num_of_tasks=total_tasks
                        f.write(scale_in_str + "-->" + op + ":  INNNNN: Active servers: " + str(total_active_servers) +
                                " Active Tasks: " + str(total_tasks) + "\n")
                        num_of_scale_ins+=1
                    else:
                        f.write(scale_in_str + "-->" + op + ":  IGNORE\n")
                        num_of_ignores+=1
        f.write("total states with scale in: " + str(num_of_scale_ins) + "\n")
        f.write("total states without scale in: " + str(num_of_ignores) + "\n")
        f.write("Highest number of tasks with scale in: " + str(highest_scale_in_num_of_tasks) + "\n")

        f.close()


def create_as_obj(as_type, mgr)->BasicAS: #TODO Throw exception for type mismatch
    if as_type == "dumb":
        return DumbAS(mgr)
    if as_type == "threshold":
        return ThresholdAS(mgr)
    if as_type == "bellman":
        return BellmanAS(mgr)
