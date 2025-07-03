import subprocess
import time
import random
import re
import numpy as np
import threading
import requests
from statistics import mean, median,variance,stdev

# get the url of a function
def getUrlByFuncName(funcName):
    try:
        output = subprocess.check_output("kn service describe " + funcName + " -vvv", shell=True).decode("utf-8")
    except Exception as e:
        print("Error in kn service describe == " + str(e))
        return None
    lines = output.splitlines()
    for line in lines:
        if "URL:"  in line:
            url = line.split()[1]
            return url

output = subprocess.check_output("kn service list", shell=True).decode("utf-8")
lines = output.splitlines()
lines = lines[1:] # delete the first line

services = [
    "http://cnn-serving.default.127.0.0.1.sslip.io",
    "http://img-res.default.127.0.0.1.sslip.io",
    "http://img-rot.default.127.0.0.1.sslip.io",
    "http://ml-train.default.127.0.0.1.sslip.io",
    "http://vid-proc.default.127.0.0.1.sslip.io",
    "http://web-serve.default.127.0.0.1.sslip.io"
]
# serviceNames = []

# for line in lines:
#     serviceName = line.split()[0] 
#     if serviceName not in serviceNames:
#         serviceNames.append(serviceName)

# for serviceName in serviceNames:
#     services.append(getUrlByFuncName(serviceName))

def lambda_func(service):
    global times
    t1 = time.time()
    r = requests.post(service, json={"name": "test"})
    # print(r.text)
    t2 = time.time()
    times.append(t2-t1)

def EnforceActivityWindow(start_time, end_time, instance_events):
    events_iit = []
    events_abs = [0] + instance_events
    event_times = [sum(events_abs[:i]) for i in range(1, len(events_abs) + 1)]
    event_times = [e for e in event_times if (e > start_time)and(e < end_time)]
    try:
        events_iit = [event_times[0]] + [event_times[i]-event_times[i-1]
                                         for i in range(1, len(event_times))]
    except:
        pass
    return events_iit

def delete_service(yaml_file: str):
    """
    delete service at KNative
    """
    try:            
        subprocess.run([
            'kubectl', 'delete', '-f' , f'{yaml_file}'
        ], check=True)
        print(f"delete service {yaml_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error scaling to zero: {e}")

def deploy_service(yaml_file: str):
    """
    deploy service at KNative
    """
    try:            
        subprocess.run([
            'kubectl', 'apply', '-f' , f'{yaml_file}'
        ], check=True)
        print(f"deploy service {yaml_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error scaling to zero: {e}")

def up_down_service(services):
    for service in services:
        n_service = service.split("://")[1].split(".")[0].replace('-', '_')

        delete_service(f"./{n_service}/{n_service}.yaml")
        time.sleep(5)  # Wait for deletion

        deploy_service(f"./{n_service}/{n_service}.yaml")
        # time.sleep()  # Wait for complete deployment

def down_service(services):
    for service in services:
        n_service = service.split("://")[1].split(".")[0].replace('-', '_')

        delete_service(f"./{n_service}/{n_service}.yaml")
        time.sleep(5)  # Wait for deletion


def down_minikube():
    subprocess.run([
        "minikube", "stop"
    ])
    time.sleep(2)
    subprocess.run([
        "minikube", "delete", "--profile=minikube"
    ])
    
def up_minikube():
    subprocess.run(["bash", "./deploy_only.sh"])
    time.sleep(30)


loads = [1, 8, 15]
# loads = [5, 30, 80]
# loads = [8, 20, 40]
load_desc = ["LOW_LOAD", "MED_LOAD", "HIGH_LOAD"]

output_file = open("run-all-out-1-0.txt", "w")

indR = 0
for load in loads:
    duration = 1
    seed = 100
    rate = load
    # generate Poisson's distribution of events 
    inter_arrivals = []
    np.random.seed(seed)
    beta = 1.0/rate
    oversampling_factor = 2
    inter_arrivals = list(np.random.exponential(scale=beta, size=int(oversampling_factor*duration*rate)))
    instance_events = EnforceActivityWindow(0,duration,inter_arrivals)
    
    print(services)
    # up_down_service(services)
    # print(serviceNames)
    for service in services:
        
        n_service = service.split("://")[1].split(".")[0].replace('-', '_')
        threads = []
        times = []
        after_time, before_time = 0, 0

        st = 0
        for t in instance_events:
            st = st + t - (after_time - before_time)
            before_time = time.time()
            if st > 0:
                time.sleep(st)

            threadToAdd = threading.Thread(target=lambda_func, args=(service, ))
            threads.append(threadToAdd)
            threadToAdd.start()
            after_time = time.time()
    
        for thread in threads:
            thread.join()

        print("=====================" + n_service + "_" + load_desc[loads.index(load)] +"=====================", file=output_file, flush=True)
        print("first output")
        print(mean(times), file=output_file, flush=True)
        print(median(times), file=output_file, flush=True)
        print(np.percentile(times, 90), file=output_file, flush=True)
        print(np.percentile(times, 95), file=output_file, flush=True)
        print(np.percentile(times, 99), file=output_file, flush=True)
        print("last output")

    # down_minikube()
    if load == loads[0]: 
        sleep_time = random.randint(3 * 60, 5 * 60)
        time.sleep(sleep_time)
    elif load == loads[1]:
        sleep_time = random.randint(5 * 60, 7 * 60)
        time.sleep(sleep_time)
    else:
        time.sleep(10)

    
    if load != loads[-1]:
        # up_minikube()
        time.sleep(10)
    