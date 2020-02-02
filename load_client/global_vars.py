# Full list of server IP addresses and ports (we trust the programmer that they have the same length
#full_srv_ip_addr_list = ["35.170.37.1", "35.174.93.186", "52.87.31.244", "34.232.193.79", "18.208.140.33"]
#full_srv_ip_addr_list = ["10.0.31.59", "10.0.31.232", "10.0.31.225", "10.0.31.21", "10.0.31.254"]
full_srv_ip_addr_list = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]
full_srv_port_list = [5000, 5001, 5002, 5003, 5004]
#full_srv_port_list = [5006, 5007, 5008, 5009, 5010]

#The server's timeout (in seconds)
server_timeout = 45

# Maximal queue length
#max_server_queue_len =  int(server_timeout*average_rate/num_of_servers)
max_server_queue_len = 10

# Interval in seconds between statistics data collection
data_collection_interval = 1

as_high_threshold = 0.6
as_low_threshold = 0.3

############################# Results filenames ###############################
response_duration_filename = "response_duration.txt"
exec_summary_filename = "exec_summary.txt"
queues_filename = "queues.txt"
num_of_servers_filename = "num_of_servers.txt"
calculated_cost_filename = "calculated_cost.txt"
log_filename = "operation_log.txt"
scale_in_filename = "bellman_scale_in_mapping.txt"
scale_out_filename = "bellman_scale_out_mapping.txt"
lb_filename = "bellman_lb_mapping.txt"

############################# Reward Parameters ###############################
# Penalties get negative values. Reward get positive values. This way we can treat everything as a reward
# and let the global definition take the decision what is a reward and what is a penalty
reward_scale_in = 0
reward_scale_out = 0
reward_use_per_second = -400
reward_response = 150
reward_delay_per_ms = 0
reward_reject = -10
'''

#Mark model 1
dpl_rate = 0.05 #3 1/<server startup/boot time>
build_cost = 0 #5
reward = 150  #100 #120
reject = 10  #100  #50
destroy_cost = 0
hold_cost = 380 #1  #2
delay_pen = [0, 0, 0, 1, 1.0, 1.0, 1.0, 1.0, 1.0]
#delay_pen = [0, 0, 0, 1, 1.1, 1.5, 1.7, 1.8, 2.3]
delay_factor = 0

#Mark model 2
dpl_rate = 3 #3 1/<server startup/boot time>
build_cost = 150 #5
reward = 150  #100 #120
reject = 100  #100  #50
destroy_cost = 0
hold_cost = 1 #1  #2
delay_pen = [0, 0, 0, 1, 1.0, 1.0, 1.0, 1.0, 1.0]
#delay_pen = [0, 0, 0, 1, 1.1, 1.5, 1.7, 1.8, 2.3]
delay_factor = 0


# Losing model
reward_scale_in = 0
reward_scale_out = -100
reward_use_per_second = -250
reward_response = 120
reward_delay_per_ms = 0
reward_reject = -100
'''

'''dpl_rate = 0.05
build_cost = 100 #5
reward = 120  #100 #120
reject = 300  #100  #50
destroy_cost = 0
hold_cost = 250 #1  #2
delay_factor = 1
srv_rate = 1.5
arr_rate = 7
delay_pen = [0, 0, 0, 1, 1.0, 1.0, 1.0, 1.0, 1.0]
'''