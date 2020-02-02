import threading

from load_client.servers_management import ServerManager, Server
from load_client.global_vars import max_server_queue_len

"""
This is the main class to holds a data structure for courses
Since we run this only once, everything is declared in the class level. We do not need
to instantiate an object (but we can).
Create the dictionary, and parse the file from which we take the course number index.
For each course number, add an element to the dictionary. The key for the element is
the course number, and the value is Course TypedDict object. We only fill the num
attribute in this new object, and other values are added in separate function, each
value in its special function.
"""

class RequestGenerator:
    def generate_request(self, sim_manager):
        server_obj:Server = sim_manager.lb_obj.pick_server ()
        # We are good with the queue, send the request
        sim_manager.as_obj.trigger_scale_out()


        if (server_obj is None) or (server_obj.current_running_tasks >= max_server_queue_len):

            # The queue in the server side is full. Reject the request
            sim_manager.inc_num_of_rejections()
            sim_manager.inc_num_of_completed_tasks()
            sim_manager.logger.info("============== REJECT!!!!!!!!!! " + str (sim_manager.get_num_of_completed_tasks()))
            return

        server_obj.start_req(sim_manager.simulation_params.avg_load_level)



