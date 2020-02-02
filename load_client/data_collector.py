import threading
import time
import os
from typing import List
from abc import ABC, abstractmethod
import matplotlib.pyplot as plt
import matplotlib
from typing import TYPE_CHECKING

from load_client.reward_calculator import CostCalculator

matplotlib.use('Agg')
plt.rc('font', size=16)

from load_client.global_vars import data_collection_interval, response_duration_filename, exec_summary_filename, \
    queues_filename, num_of_servers_filename, calculated_cost_filename
from load_client.servers_management import ServerManager


class DataCollector(ABC):

    def __init__(self, sim_mgr, res_path):
        self.sim_manager: 'SimExecManager' = sim_mgr
        self.srv_mgr: ServerManager = sim_mgr.srv_mgr
        self.res_path:str = res_path
        self.x_list: List[int] = []
        self.y_list: List[List[int]] = []
        self.counter = 1
        self.f = None


        # Create an empty list of each server
        for i in range(len(self.srv_mgr.full_srv_list)):
            self.y_list.append([]*0)

    @abstractmethod
    def save_ongoing_data(self):
        pass

    @abstractmethod
    def save_summary_data(self):
        pass

    @abstractmethod
    def print_data(self):
        pass

    @abstractmethod
    def plot_data(self):
        pass

    def simulation_finished(self):
        self.f.close()
        self.print_data()
        self.plot_data()

class ResponseDurationData(DataCollector):
    def __init__(self, sim_mgr, res_path):
        super ().__init__ (sim_mgr, res_path)
        self.filename = os.path.join(self.res_path, response_duration_filename)
        self.f = open (self.filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_mgr.full_srv_list)):
            self.y_list.append([]*0)

    def save_ongoing_data(self):
        return

    def save_summary_data(self):
        """
        The response duration is event driven metric, and is collected by the server.
        Therefore we have to call this method only once, when the simulation is completed, and take the data from
        the server objects
        :return:
        """
        # We have to find out which of the servers collected the most events. This will determine
        # the dimension of the x_list and y_lists (all have to be with same length
        max_len = 0
        for  server in self.srv_mgr.full_srv_list:
            # Update the duration list max_len
            max_len = max(max_len, len(server.response_duration_list))

        # build y lists and x list for plot
        for i in range (0, len (self.srv_mgr.full_srv_list)):
            server = self.srv_mgr.full_srv_list[i]

            # Simply copy the duration list as a new y list, and pad with 0's until you reach max_length
            self.y_list[i] = server.response_duration_list + [0]*(max_len-len(server.response_duration_list))

        self.x_list = range(1, max_len+1) # Build the x axis according to max_len

        # Create the results file
        for server in self.srv_mgr.full_srv_list:
            line = str(server.srv_port) + ":"
            for res in server.response_duration_list:
                line+= str(res) + " "
            self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        #print ("X axis: " + str(self.x_list))
        #for i in range(0,len(self.srv_manager.full_srv_list)):
        #    print ("Y axis for     ", str(self.srv_manager.full_srv_list[i].srv_port), ": ", str (self.y_list[i]))
        return


    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Response Count', ylabel='Response Time',
                title='Server Response time')
        ax.grid ()

        for i in range(len(self.srv_mgr.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_mgr.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper left')
        fig.savefig(os.path.join(self.res_path, "srv_resp_time.png"))

class SummaryData(DataCollector):
    """
    This class handles all the summary information about the execution. It includes the summary results, performance
    grade as well as the initial data for the batch
    """
    cost_calc_obj: CostCalculator


    def __init__(self, sim_mgr, res_path, cost_calc_obj):
        super ().__init__ (sim_mgr, res_path)
        self.filename = os.path.join (res_path, exec_summary_filename)
        self.cost_calc_obj = cost_calc_obj
        self.response_counter = 0
        self.total_delay = 0
        self.num_of_servers_list:List[int] = []*0
        self.num_of_servers_list.append(0)


    def save_ongoing_data(self):
        return

    def save_summary_data(self):
        """
        The Summary data is collected only when the simulation is finished
        :return:
        Request rate: 3.6
        LB policy: Bellman
        AS Policy: Bellman
        Initial servers: 5
        load level 10 (1.1 sec per request)

        """
        for server in self.srv_mgr.full_srv_list:
            self.response_counter += len(server.response_duration_list)
            self.total_delay += sum(server.response_duration_list)

        param_obj = self.sim_manager.simulation_params
        self.f = open (self.filename, "a")
        # Write the test parameters to the file
        param_str = "test_parameters:\n"
        param_str += "load_balancer: " + str(self.sim_manager.lb_obj.__class__.__name__) + "\n"
        param_str += "auto scaler: " + str(self.sim_manager.as_obj.__class__.__name__) + "\n"
        param_str += "num_of_tasks: " + str(param_obj.num_of_tasks) + "\n"
        param_str += "avg_load_level: " + str(param_obj.avg_load_level) + "\n"
        param_str += "initial_num_of_servers: " + str(param_obj.initial_num_of_servers) + "\n"
        param_str += "average_rate: " + str(param_obj.average_rate) + "\n"
        param_str += "server_startup_time: " + str(param_obj.server_startup_time) + "\n"
        param_str += "load_deviation: " + str (param_obj.deviation) + "\n"
        self.f.write (param_str + "\n")

        # Write the result summary
        res_str = "Test Results: \n"
        res_str += "scale_outs: " + str(self.srv_mgr.total_scale_out_counter) +  "\n"
        res_str += "scale_ins: " + str(self.srv_mgr.total_scale_in_counter) +  "\n"
        res_str += "rejections: " + str(self.sim_manager.get_num_of_rejections()) + "\n"
        res_str += "total_server_responses: " + str(self.response_counter) +  "\n"
        res_str += "sum_of_all_server_processing_time: " + str(self.total_delay) +  "\n"
        self.f.write(res_str + "\n")

        self.f.close()



    def print_data(self):
        # print totals
        self.sim_manager.logger.info ("==================total started tasks: " + str (self.sim_manager.get_num_of_completed_tasks()))
        self.sim_manager.logger.info ("==================Number of rejects: " + str (self.sim_manager.get_num_of_rejections()))
        self.sim_manager.logger.info ("==========  requests per server ===========")
        for server in self.srv_mgr.full_srv_list:
            self.sim_manager.logger.info ("server %s sent %d requests" % (server.srv_port, len (server.response_duration_list)))

        for server in self.srv_mgr.full_srv_list:
            log_str = "server " + str(server.srv_port) +  " duration: "

            # Print task processing duration
            for num in server.response_duration_list:
                log_str += str(num) + " "
            self.sim_manager.logger.info(log_str)

            # Print queueing queue length
            log_str =  "server " + str(server.srv_port)  + " queue length: "
            for num in server.response_tasks_queue_list:
                log_str += str(num) + " "
            self.sim_manager.logger.info(log_str)

    def plot_data(self):
            pass # Summary does not produce a graph


class QueueLenData(DataCollector):
    """
    This data collector counts the enqueueing queue length every interval of time. It makes more sense to measure
    by time, because is servers scale in and out, graphs that are shown by event are doing to be meaningless
    """
    def __init__(self, sim_mgr, res_path):
        super ().__init__ (sim_mgr, res_path)
        filename = os.path.join(self.res_path, queues_filename)
        self.f = open (filename, "a")


        # Create an empty list of each server
        for i in range(len(self.srv_mgr.full_srv_list)):
            self.y_list.append([]*0)

    def save_summary_data(self):
        return

    def save_ongoing_data (self):
        """
        The queue len data is periodic driven, and therefore called periodically from the "collect_data": thread
        It indicates the dequeuing queue length, which is shorter than the enqueueing queue length
        :return:
        """
        self.counter += 1
        self.x_list.append(self.counter*data_collection_interval) # add the x axis (currently counter) element
        line = str(self.counter) # start a line string for the csv record
        for i in range (0, len (self.srv_mgr.full_srv_list)):
            server = self.srv_mgr.full_srv_list[i]
            line = line + "," + str(server.current_running_tasks) # append a value to the csv line
            self.y_list[i].append(server.current_running_tasks) # append the queue length value to the server's array
        self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        for i in range(0, len(self.srv_mgr.full_srv_list)):
            # For debug, print also the queue length measured in client side
            self.sim_manager.logger.info ("server version " + str (self.srv_mgr.full_srv_list[i].srv_port) + ": " +\
                   str (self.srv_mgr.full_srv_list[i].response_tasks_queue_list))

    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Time(seconds)', ylabel='Queue Length',
                title='Server Queue Length by Time')
        ax.grid ()

        for i in range(len(self.srv_mgr.full_srv_list)):
            srv_queue_arr = self.y_list[i]
            srv_port = self.srv_mgr.full_srv_list[i].srv_port
            ax.plot (self.x_list, srv_queue_arr, label=str(srv_port))
        plt.legend (loc='upper right')
        fig.savefig(os.path.join(self.res_path, "srv_queue.png"))


class NumOfServersData(DataCollector):
    """
    This data collector counts the the number of active servers every interval of time.
    """
    def __init__(self, sim_mgr, res_path):
        super ().__init__ (sim_mgr, res_path)
        self.filename = os.path.join(self.res_path, num_of_servers_filename)
        self.f = open (self.filename, "a")
        self.y_list.append ([] * 0) # This graph has only one line, will be filled in y_list[0]

    def save_summary_data(self):
        return

    def save_ongoing_data (self):
        """
        The num of servers counter data is periodic driven, and therefore called periodically from the "collect_data": thread
        :return:
        """
        self.counter += 1
        self.x_list.append(self.counter*data_collection_interval) # add the x axis (currently counter) element
        line = str(self.counter) # start a line string for the csv record
        #srv_num:int = len(self.srv_mgr.active_srv_list) # This is the right value to collect
        srv_num:int = len(self.srv_mgr.available_srv_list) # we temporarily use this value instead
        line = line + "," + str(srv_num)
        self.y_list[0].append(srv_num)
        self.f.write(line + "\n") # write the csv line to the file

    def print_data(self):
        #print ("X axis: " + str(self.x_list))
        self.sim_manager.logger.info ("num of active servers each sample interval" + str(self.y_list[0]))

    def plot_data(self):
        fig, ax = plt.subplots (figsize=(30,15))

        ax.set (xlabel='Time(seconds)', ylabel='Active Servers',
                title='Number of Active Servers by Time')
        ax.grid ()
        ax.plot (self.x_list, self.y_list[0])

        fig.savefig(os.path.join(self.res_path, "active_srv.png"))

class DataCollectionManager:
    def __init__(self, sim_mgr):
        res_path = sim_mgr.res_path
        # Create folder for all the results
        self.cost_calc_obj = CostCalculator(res_path)

        # Create a class of queue length data
        queue_len_data = QueueLenData(sim_mgr, res_path)
        self.response_duration_data = ResponseDurationData(sim_mgr, res_path)
        self.summary_data = SummaryData(sim_mgr, res_path, self.cost_calc_obj)
        self.num_of_servers_data = NumOfServersData(sim_mgr, res_path)

        data_collection_thread = threading.Thread (target=collect_data, args=(self,sim_mgr,))
        data_collection_thread.start ()

        self.data_collection_list:List[DataCollector] = [queue_len_data, self.response_duration_data,
                                                         self.summary_data, self.num_of_servers_data]


    def save_ongoing_data(self):
        for data_collector in self.data_collection_list:
            data_collector.save_ongoing_data()

    def simulation_finished(self):

        # Generate Summary data
        for data_collector in self.data_collection_list:
            data_collector.save_summary_data()

        # Save and print
        for data_collector in self.data_collection_list:
            data_collector.simulation_finished()

        self.cost_calc_obj.calculate_cost()

def collect_data(data_collector, sim_mgr):
    while True:
        time.sleep (data_collection_interval)
        data_collector.save_ongoing_data()
        if sim_mgr.is_simulation_finished():
            data_collector.simulation_finished()
            break

