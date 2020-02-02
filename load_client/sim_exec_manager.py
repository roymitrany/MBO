import logging
import math
import os
import random
from time import sleep, time

from load_client.auto_scaler import BasicAS, create_as_obj
from load_client.data_collector import DataCollectionManager
from load_client.global_vars import log_filename
from load_client.load_balancers import BasicLB, create_lb_obj
from load_client.request_generator import RequestGenerator
from load_client.servers_management import ServerManager


class SimulationParams:
    # Force to specify the params in object construction
    def __init__(self, num_of_tasks=0, avg_load_level=0, initial_num_of_servers=0, average_rate=0.0,
                 deviation:float = 0, server_startup_time=0, pie_file:str="pie.txt"):
        self.num_of_tasks = num_of_tasks
        self.avg_load_level = avg_load_level
        self.initial_num_of_servers = initial_num_of_servers
        self.average_rate = average_rate
        self.server_startup_time = server_startup_time
        self.deviation = deviation
        self.pie_file = pie_file

        # Initialize offset arrays
        self.off_array = [0.0]*25
        for i in range (25):
            self.off_array[i] = math.trunc(random.uniform(0-deviation,deviation)*100)/100



class SimExecManager:
    simulation_params:SimulationParams
    data_collector:DataCollectionManager
    srv_mgr:ServerManager
    lb_obj:BasicLB
    as_obj:BasicAS
    tasks_completed:int
    def __init__(self, simu_params:SimulationParams, lb_type="jsq", as_type="threshold"):
        ts = time()
        folder_str = str (simu_params.average_rate) + "_" + str (simu_params.num_of_tasks) + "_" + \
                     str (simu_params.deviation) + "_" + \
                     lb_type + "_" + as_type + "_" + str(ts).split(".")[0][-4:]
        self.res_path = os.path.join(os.getcwd(), "results", folder_str)
        os.makedirs(self.res_path)

        # the number of tasks to be completed before we stop the test
        self.simulation_params = simu_params
        # Number of the tasks that were completed (not sure if we will ever use it)
        self.tasks_completed = 0

        # Number of rejected tasks (due to full servers)
        self.num_of_rejections = 0

        # Index for the request (not sure if we will ever use it)
        self.tasks_global_index = 0

        # Indicator that simulation is finished (in order to stop data collection
        self.simulation_finished = False

        self.srv_mgr = ServerManager(self, simu_params.initial_num_of_servers)
        self.lb_obj = create_lb_obj(lb_type, self)
        self.as_obj = create_as_obj(as_type, self)

        self.data_collector = DataCollectionManager(self)
        self.request_generator = RequestGenerator()

        log_file_name = os.path.join (self.res_path, log_filename)
        # create logger with 'spam_application'
        self.logger = logging.getLogger (str(ts))
        self.logger.setLevel (logging.DEBUG)

        # create file handler which logs even debug messages
        fh = logging.FileHandler (log_file_name)
        fh.setLevel (logging.DEBUG)
        # create console handler with a higher log level
        ch = logging.StreamHandler ()
        ch.setLevel (logging.ERROR)

        formatter = logging.Formatter ('%(asctime)s.%(msecs)03d: %(funcName)s: %(message)s',datefmt='%H:%M:%S')
        fh.setFormatter (formatter)
        ch.setFormatter (formatter)

        # add the handlers to the logger
        self.logger.addHandler (fh)
        self.logger.addHandler (ch)



    def get_num_of_completed_tasks(self):
        return self.tasks_completed

    def inc_num_of_completed_tasks(self):
        self.tasks_completed += 1

    def get_num_of_rejections(self):
        return self.num_of_rejections

    def inc_num_of_rejections(self):
        self.num_of_rejections += 1

    def is_simulation_finished(self):
        return self.simulation_finished

    def set_simulation_finished(self):
        self.simulation_finished = True

    def run_simulation(self):
        # Loop for generating requests
        interval = int(self.simulation_params.num_of_tasks/20)
        curr_rate = self.simulation_params.average_rate
        factor_iteration_counter = 0
        offset_counter:int = 0
        for taskk in range (self.simulation_params.num_of_tasks):
            time_to_sleep = random.expovariate (curr_rate)
            if time_to_sleep<0: continue
            sleep (time_to_sleep)
            self.logger.info (">>>>>>>>>Starting task " + str (taskk))

            self.request_generator.generate_request (self)
            factor_iteration_counter+=1
            # If we had enough iterations with the current factor, create a new factor and reset the counter
            if factor_iteration_counter >= interval:
                factor_iteration_counter = 0
                offset = sim_params.off_array[offset_counter]
                curr_rate = self.simulation_params.average_rate + offset
                self.logger.debug("New iteration offset is: " + str(offset) + " new curr_rate is " + str(curr_rate))
                offset_counter+=1
        self.set_simulation_finished ()
        logging.shutdown ()


# Initialize the server manager first, everything depends on it



sim_params = SimulationParams(num_of_tasks=18999, avg_load_level=6, initial_num_of_servers=5, average_rate=5,
                              server_startup_time=8, pie_file="pie_dpl_013.txt")

s = SimExecManager (sim_params, lb_type="bellman", as_type="bellman")
s.run_simulation ()

for sst in [2,5,8,10,20]:
    sim_params = SimulationParams(num_of_tasks=18999, avg_load_level=6, initial_num_of_servers=5, average_rate=5, server_startup_time=sst)
    s = SimExecManager (sim_params, lb_type="jsq", as_type="threshold")
    s.run_simulation ()

for rate in range(3,7):
    sim_params = SimulationParams(num_of_tasks=18999, avg_load_level=6, initial_num_of_servers=5, average_rate=rate, server_startup_time=20)
    s = SimExecManager (sim_params, lb_type="jsq", as_type="threshold")
    s.run_simulation ()

    sim_params.pie_file = "pie_losing_" + str(rate) + ".txt"
    s = SimExecManager (sim_params, lb_type="bellman", as_type="bellman")
    s.run_simulation ()

'''
for i in range(65,90,5):
    rate = i/10
    sim_params = SimulationParams(num_of_tasks=9999, avg_load_level=6, initial_num_of_servers=5, average_rate=rate, server_startup_time=2)
    s = SimExecManager (sim_params, lb_type="jsq", as_type="threshold")
    s.run_simulation ()

    s = SimExecManager (sim_params, lb_type="bellman", as_type="bellman")
    s.run_simulation ()

    sim_params.initial_num_of_servers = min(int(rate/2)+2,5)
    s = SimExecManager (sim_params, lb_type="jsq", as_type="dumb")
    s.run_simulation ()



for i in range (18, 30, 2):
    devi:float = i/10
    sim_params = SimulationParams (num_of_tasks=20001, avg_load_level=6, initial_num_of_servers=5, average_rate=5,
                                   deviation=devi, server_startup_time=20)
    s=SimExecManager(sim_params, lb_type="bellman", as_type="bellman")
    s.run_simulation()

    s=SimExecManager(sim_params, lb_type="jsq", as_type="threshold")
    s.run_simulation()

    sim_params.initial_num_of_servers = min(int(devi/2)+4,5)
    s = SimExecManager (sim_params, lb_type="jsq", as_type="dumb")
    s.run_simulation ()


sim_params = SimulationParams (num_of_tasks=500, avg_load_level=6, initial_num_of_servers=2, average_rate=10,
                                   deviation=0, server_startup_time=2)
s=SimExecManager(sim_params, lb_type="bellman", as_type="bellman")
s.run_simulation()
for i in range (12, 24, 4):
    devi:float = i/10
    sim_params = SimulationParams (num_of_tasks=50, avg_load_level=7, initial_num_of_servers=5, average_rate=4,
                                   deviation=devi, server_startup_time=2)
    s=SimExecManager(sim_params, lb_type="jsq", as_type="threshold")
    s.run_simulation()

    s=SimExecManager(sim_params, lb_type="bellman", as_type="bellman")
    s.run_simulation()

    s = SimExecManager (sim_params, lb_type="jsq", as_type="dumb")
    s.run_simulation ()
'''
exit(0)
