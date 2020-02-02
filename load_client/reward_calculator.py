import os
import re

from load_client.global_vars import reward_scale_out, reward_scale_in, reward_reject, reward_response, \
    reward_use_per_second, exec_summary_filename, response_duration_filename, reward_delay_per_ms, \
    num_of_servers_filename
from typing import TYPE_CHECKING


class CostCalculator:

    def __init__(self, res_path):
        self.res_path = res_path
        self.scale_out_cost = self.scale_in_cost = self.rejection_cost = self.delay_cost  = 0
        self.response_cost = self.server_execution_cost = self.total_reward = self.reward_per_task = 0


    def calculate_cost(self):
        num_of_tasks:int = 0
        # Take from summary data
        filename = os.path.join (self.res_path, exec_summary_filename)
        f = open(filename, "r")
        res_str = f.read() # Read all the file as one string
        match_obj = re.match (r'.+scale_outs:\s+(\d+)', res_str, flags=re.DOTALL)
        if match_obj:
            self.scale_out_cost = int(match_obj.group (1))*reward_scale_out
        match_obj = re.match (r'.+scale_ins:\s+(\d+)', res_str, flags=re.DOTALL)
        if match_obj:
            self.scale_in_cost = int (match_obj.group (1))*reward_scale_in
        match_obj = re.match (r'.+num_of_tasks:\s+(\d+)', res_str, flags=re.DOTALL)
        if match_obj:
            num_of_tasks = int (match_obj.group (1))
        match_obj = re.match (r'.+rejections:\s+(\d+)', res_str, flags=re.DOTALL)
        if match_obj:
            rejection_counter = int (match_obj.group (1))
            self.rejection_cost = rejection_counter*reward_reject
        f.close()

        # File response_duration should be transposed and then it will be easy to read
        # the file back to lists and calculate the cost
        filename = os.path.join (self.res_path, response_duration_filename)
        f = open(filename, "r")
        response_counter = 0
        total_delay = 0
        for line in f.readlines():
            response_duration_list = [int(i) for i in line.split(":")[1].split()]
            response_counter += len(response_duration_list)
            total_delay += sum (response_duration_list)

        self.response_cost = response_counter*reward_response
        self.delay_cost = total_delay*reward_delay_per_ms
        f.close()

        # Count the total cost of holding n servers each second
        # Take the data from file _num_of _servers (file is good as is)
        filename = os.path.join (self.res_path, num_of_servers_filename)
        f = open(filename, "r")
        total_servers = 0
        for line in f.readlines ():
            total_servers+=int(line.split(",")[1].strip())
        self.server_execution_cost = total_servers*reward_use_per_second

        # Sum the total cost or reward
        self.total_reward = self.scale_out_cost + self.scale_in_cost + self.rejection_cost\
                            + self.response_cost + self.delay_cost + self.server_execution_cost


        if num_of_tasks!=0:
            self.reward_per_task = self.total_reward / num_of_tasks
        f.close()

        # Save the calculated cost
        filename = os.path.join (self.res_path, exec_summary_filename)
        f = open (filename, "a")

        # Write header
        f.write("====================== Rewards Calculations ===========================\n")
        # write the reward parameters
        param_str = "Parameters:\n-----------\n"
        param_str+= "reward_scale_in: " + str(reward_scale_in) + "\n"
        param_str+= "reward_scale_out: " + str(reward_scale_out) + "\n"
        param_str+= "reward_use_per_second: " + str(reward_use_per_second) + "\n"
        param_str+= "reward_response: " + str(reward_response) + "\n"
        param_str+= "reward_delay_per_ms: " + str(reward_delay_per_ms) + "\n"
        param_str+= "reward_reject: " + str(reward_reject) + "\n"
        f.write(param_str + "\n\n")


        # Write the cost summary to the file
        cost_str =  "Total cost: \n-----------\n"
        cost_str +=  "scale_out_cost: " + str(self.scale_out_cost) + "\n"
        cost_str += "scale_in_cost: " + str(self.scale_in_cost) + "\n"
        cost_str += "rejection_cost: " + str(self.rejection_cost) + "\n"
        cost_str += "delay_cost: " + str(self.delay_cost) + "\n"
        cost_str += "server_execution_cost: " + str(self.server_execution_cost) + "\n"
        cost_str += "response_cost: " + str(self.response_cost) + "\n"
        cost_str += "total_reward: " + str(self.total_reward) + "\n"
        cost_str += "reward_per_task: " + str(self.reward_per_task)
        f.write(cost_str + "\n\n\n")
        f.close()

if __name__ == "__main__":
    '''if len(sys.argv) < 2:
        print ("Please provide path as parameter")
        exit(-1)
    result_path = sys.argv[1]
    if not os.path.isdir(result_path):
        print (result_path + " is not a directory")
        exit(-1)
    '''
    root_path = "C:\\Users\\Roy\\Technion\OneDrive - Technion\\WebDev\\mark_lb_model\\load_client\\results\\5_29999_0_bellman_bellman_8440"
    '''dirlist = os.listdir(root_path)
    for dir in dirlist:
        result_path = os.path.join (root_path, dir)
        ok = True
        summary_filename = os.path.join (result_path, exec_summary_filename)
        if not os.path.isfile (summary_filename):
            print ("There are no results in this directory: " + result_path)
            ok = False
        if ok:
            cost_calc_obj = CostCalculator (result_path)
            cost_calc_obj.calculate_cost()'''
    ok = True
    summary_filename = os.path.join (root_path, exec_summary_filename)
    if not os.path.isfile (summary_filename):
        print ("There are no results in this directory: " + root_path)
        ok = False
    if ok:
        cost_calc_obj = CostCalculator (root_path)
        cost_calc_obj.calculate_cost()

