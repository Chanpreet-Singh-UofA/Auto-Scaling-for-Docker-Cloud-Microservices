import docker

from redis import Redis
import requests
import math
import time
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

import numpy as np

redis = Redis(host='10.2.6.150', port=6379)

fig = go.FigureWidget()

global workload
global responseTime
global size

workload=[]
responseTime=[]
size=[]
prevHit=int(redis.get('hits').decode())

def updatePlot():
    global workload
    global responseTime
    global size
    global prevHit

    newHit = int(redis.get('hits').decode())
    workload.append(newHit-prevHit)
    prevHit=newHit

    fig = make_subplots(rows=3, cols=1, subplot_titles=("Workload", "Response Time", "Swarm Size"))
    fig.update_layout(height=800, width=800, title_text='AutoScaler Plot')

    fig.add_trace(go.Scatter(x=list(range(len(workload))), y=workload, mode='lines', name='Workload'), row=1, col=1)
    fig.add_trace(go.Scatter(x=list(range(len(responseTime))), y=responseTime, mode='lines', name='Response Time'), row=2, col=1)
    fig.add_trace(go.Scatter(x=list(range(len(size))), y=size, mode='lines', name='Swarm Size'), row=3, col=1)

    fig.update_xaxes(title_text='', row=3, col=1)
    fig.update_yaxes(title_text='Workload', row=1, col=1)
    fig.update_yaxes(title_text='Response Time', row=2, col=1)
    fig.update_yaxes(title_text='Swarm Size', row=3, col=1)

    fig.layout.xaxis.type = 'linear'
    fig.layout.update()
    pio.write_image(fig, 'plots.png')

if __name__ == "__main__":
    print("AutoScale ON")

    compute_time=[]
    #set default to 2
    set_replicas=2
    os.system('docker service scale app_name_web='+str(set_replicas))
    size.append(set_replicas)


    while True:
        t0 = time.time()
        requests.get('http://' + '10.2.1.38' + ':8000/').content
        t1 = time.time()

        updatePlot()
        compute_time.append(t1-t0)

        print('The estimated compute time is '+str(t1-t0))
        responseTime.append(t1-t0)

        if(len(compute_time)>=10): 
            average_compute_time = sum(compute_time) / len(compute_time)
            print('The average compute time is '+str(average_compute_time)+' for last '+str(len(compute_time))+' hits.')
            if(average_compute_time>=5):
                print('Increasing Replicas!')
                set_replicas = set_replicas+1
                print('Replicas set as '+str(set_replicas))
                size.append(set_replicas)
                os.system('docker service scale app_name_web='+str(set_replicas))
            elif(average_compute_time<2.5 and set_replicas > 2):
                print('Decreasing Replicas!')
                set_replicas = set_replicas-1
                print('Replicas set as '+str(set_replicas))
                size.append(set_replicas)
                os.system('docker service scale app_name_web='+str(set_replicas))
            else:
                print('Average time and Replicas are within right limits.')
            compute_time = [] 
        
        time.sleep(1)







