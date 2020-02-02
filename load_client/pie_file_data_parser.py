import re
from typing import List

from load_client.servers_management import ServerManager, SERVER_STATE_INIT, SERVER_STATE_AVAILABLE


def get_index_for_queue_list(queue_list:List[str])->int:
    '''
    Convert a list of queue lengths to decimal integer
    :param queue_list: the list of queue lengths, as strings
    :return: a converted integer, that look a lot like the original list
    '''
    index: int = 0
    curr_queue: int
    for curr_queue in queue_list:
        index = index * 10 + int(curr_queue)
    return index

class PieDataParser:
    queue_length = 5
    num_of_servers = 5
    def __init__(self, filename):
        # The scale in policy setermines the operation that we should do for each server.
        # the easiest way is to keep it as a string of "0"s and "1"s
        # empty string means that no policy assignment for this state. After parsing, should be only for illegal states
        self.scale_in_policy_list: List[str] = [""] * 100000
        self.scale_out_policy_list: List[int] = [0] * 100000  # By default do nothing
        self.load_balance_policy_list: List[int] = [-2] * 100000  # By default do nothing
        self.load_data(filename)
        print('done loading AS data')


    def load_data(self, filename):

        # Read the pie_file
        f = open (filename, "r")
        for line in f.readlines():

            # Parse both parts of the line
            match_obj = re.match(r'\[(.*)\]\s+=>\s+\[(.*)\]', line)

            queue_state_str = match_obj.group(1).strip()
            # Convert the strings to lists, and verify legality
            queue_state_list = re.split(r'\s+', queue_state_str)
            if len(queue_state_list) != self.num_of_servers: # Verify that the list size matches number of server
                continue
            try:
                # Convert to int and add 2 to all numbers (0=>idle, 1=>initializing, 2=>empty queue, 3=> queue len=1 etc)
                queue_state_list = [str(int (i)+2) for i in queue_state_list]
            except ValueError: # Verify that the list contains only numbers
                #prin("errrrorrrrrr: ",queue_state_str)
                continue
            if not all ((0 <= int(x) <= self.queue_length+2 for x in queue_state_list)):
                continue # One of the numbers is out of range

            operation_str = match_obj.group(2).strip()
            operation_str = re.sub (r'\.', "", operation_str) # Get rid of the dots
            operation_list = re.split(r'[\s]+', operation_str)
            try:
                operation_list = [int (i) for i in operation_list] #
            except ValueError: # Verify that the list contains only numbers
                continue

            if not all ((0 <= x <= 1 for x in operation_list[0:-1])):
                continue # One of the numbers is out of range

            if not 0 <= operation_list[-1] <= 2*self.num_of_servers+1:
                continue

            # Now that we know that the line is legal we can add it to the Auto Scaler Lookup list
            # Build an index number from the queue state list. The number should look a lot like an n digit
            # number that the list forms. For example, if the list is [1,7,7,3,0] then the index number would be 17730
            index:int = get_index_for_queue_list(queue_state_list)
            if index == 22022:
                print ("Hehe")

            # build the scale down policy lookup out of the boolean values for each server.
            op:str = ""
            for curr_op in operation_list[0:-2]:
               op = op+str(curr_op)
            #prin(index, "->", op)

            self.scale_in_policy_list[index]=op

            if operation_list[-1]>self.num_of_servers:
                self.scale_out_policy_list[index]=1 # Otherwise will stay 0
            #prin(index, "->", self.scale_out_policy_list[index])

            srv_index = operation_list[-1]%(self.num_of_servers+1)
            if srv_index == self.num_of_servers:
                srv_index = -1
            self.load_balance_policy_list[index] = srv_index

def get_queue_state_index (mgr:ServerManager)->int:
    # Build index out of servers queue
    queue_state_list: List[str] = [] * 0
    for server in mgr.full_srv_list:
        if server.running_state == SERVER_STATE_INIT:
            queue_state_list.append ('1')
        elif server.running_state == SERVER_STATE_AVAILABLE:
            num_of_tasks = min(server.current_running_tasks, PieDataParser.queue_length)
            queue_state_list.append (str(num_of_tasks+2))
        else:
            queue_state_list.append ('0')

    index = get_index_for_queue_list(queue_state_list)
    return index