import ctypes
from ctypes import byref, POINTER
import pylab as pl
import PyDAQmx as daq
import ctypes
import numpy as np
import os
import time

def Acquire(ChanName, Filepath,Save = 1, ACQtime=1, LaserLength=200e-6,Resolution =0.5e-6) :

    # ACQtime=1
    # LaserLength=200e-6
    # Resolution =0.5e-6  # it should be in seconds(100 ns resolution is the max)
    
    Start = time.time()
    print("Acquiring signalTrig(s)...\n")
    
    DATA = {}
    flag=0
    flag2=1
    split=2
    SLaserLength=int(LaserLength/Resolution)
    while flag==0:
        if ACQtime>split:
            ACQtimeSub=split
            ACQtime=ACQtime-split
        else:
            ACQtimeSub=ACQtime
            flag=1    
        
        Counter1 = daq.Task()
        Counter2 = daq.Task()
        read2 = daq.c_uint64()
        
        Clock = daq.Task()
        read = daq.c_ulong()
        rate = 1000
        n_samples = 1000
        duty_cycle = 0.5
        _RWTimeout = 100
        
        n_read_samples = daq.int32()
        
        period=Resolution * 2
        samples = int(np.ceil(ACQtimeSub / period))
        
        count_data = np.empty((1, 2 * samples), dtype=np.uint32)
        count_data2 = np.empty((1, 2 * samples), dtype=np.uint32)
        
        
        
        my_clock_channel = '/Dev1/Ctr2'
        Clock.CreateCOPulseChanFreq(my_clock_channel,
                                         "myClockTask",
                                         daq.DAQmx_Val_Hz,
                                         daq.DAQmx_Val_Low,
                                         0,
                                         1 / float(period),
                                         duty_cycle,
                                         )
        
        Clock.CfgImplicitTiming(
            daq.DAQmx_Val_ContSamps,
            1000  # the buffer size
        )
        
        Clock.SetPauseTrigType(daq.DAQmx_Val_DigLvl) #Pause the measurement or generation while a digital signal is at either a high or low state.
        Clock.SetDigLvlPauseTrigSrc("PFI2") #Specifies the name of a terminal where there is a digital signal to use as the source of the Pause Trigger.
        Clock.SetDigLvlPauseTrigWhen(daq.DAQmx_Val_Low) #Specifies whether the task pauses while the signal is high or low
        
        ch2 = '/Dev1/Ctr1'
        Counter2.CreateCISemiPeriodChan(
            ch2,
            'Counter Channel 1',  # The name to assign to the created virtual channel.
            0,  # Expected minimum count value
            2,  # Expected maximum count value
        
            daq.DAQmx_Val_Ticks,  # The units to use to return the measurement. Here are timebase ticks
            ''
        )
        Counter2.SetCISemiPeriodTerm(# Sync
            ch2,  # assign a named Terminal
            '/Dev1/Ctr2' + 'InternalOutput')
        Counter2.SetCICtrTimebaseSrc(ch2,
                                          '/Dev1/PFI2') 
        
        Counter2.CfgImplicitTiming(daq.DAQmx_Val_ContSamps,
                                        2 ** 25
                                        # 2**30 is maximum. buffer length which stores  temporarily the number of generated samples
                                        )
        
        
        Counter1.CreateCISemiPeriodChan(
            '/Dev1/Ctr0',  # use this counter channel. The name of the counter to use to create virtual channels.
            'Counter Channel 1',  # The name to assign to the created virtual channel.
            0,  # Expected minimum count value
            2,  # Expected maximum count value
        
            daq.DAQmx_Val_Ticks,  # The units to use to return the measurement. Here are timebase ticks
            ''  # customScaleName, in case of different units(DAQmx_Val_FromCustomScale).
        )
        
        
        
        
        
        Counter1.SetCISemiPeriodTerm(
            '/Dev1/Ctr0',
            '/Dev1/Ctr2' + 'InternalOutput')
        
        
        Counter1.SetCICtrTimebaseSrc('/Dev1/Ctr0',
                                          '/Dev1/PFI1') 
        
        
        
        
        Counter1.CfgImplicitTiming(daq.DAQmx_Val_ContSamps,
                                        2 ** 25
                                        # 2**30 is maximum.
                                        )
        
        Counter1.SetArmStartTrigType(daq.DAQmx_Val_DigEdge)           #############################Changed
        Counter1.SetDigEdgeArmStartTrigSrc("PFI2")#############################Changed
        Counter1.SetDigEdgeArmStartTrigEdge(daq.DAQmx_Val_Rising)#############################Changed
        Counter2.SetArmStartTrigType(daq.DAQmx_Val_DigEdge)#############################Changed
        Counter2.SetDigEdgeArmStartTrigSrc("PFI2")#############################Changed
        Counter2.SetDigEdgeArmStartTrigEdge(daq.DAQmx_Val_Rising)#############################Changed
        try:
            Counter1.StartTask()
            Counter2.StartTask()
        # print('1')
        # time.sleep(0.1)
        except Exception as e:
            print('exception Happened')
            print(e)
            Clock.StopTask()
            Clock.ClearTask()
        Clock.StartTask()
        
        
        
        
        n_read_samples = daq.int32()
        
        
        count_data = np.empty((1, 2 * samples), dtype=np.uint32)
        count_data2 = np.empty((1, 2 * samples), dtype=np.uint32)
        
        
        Counter1.ReadCounterU32(2 * samples,
                                     _RWTimeout,
                                     count_data[0],
                                     2 * samples,
                                     byref(n_read_samples),
                                     None)
        
        Counter2.ReadCounterU32(2 * samples,
                                     _RWTimeout,
                                     count_data2[0],
                                     2 * samples,
                                     byref(n_read_samples),
                                     None)  #
        
        
        Laser = count_data[0, :]
        Sync = count_data2[0, :]
        # pl.close('all')
        # pl.plot(Sync,'b+')
        # pl.figure()
        # pl.plot(Laser,'b+')
        try:
            Counter1.StopTask()
            Counter1.ClearTask()
            Counter2.StopTask()
            Counter2.ClearTask()
            Clock.StopTask()
            Clock.ClearTask()
            
            #print('task stoped1')
        except:
            pass
        a = np.argwhere(Sync > 0.5)
        #############################Changed
        ArraySize = np.min(np.diff(np.transpose(a)))-1
        mydata = np.zeros(ArraySize)
        if flag2==1:
            mydataMain=np.zeros(ArraySize)
            flag2=0
        
        for i in range(np.size(a) - 2):
            if i != int(np.size(a)) - 1:
                mydata = mydata+Laser[int(a[i])+1:int(a[i])+ArraySize+1] 
        mydataMain=mydataMain+mydata
            
    print("Signal of "+ str(np.size(a))+" pulses acquired in "+ str(round(time.time()-Start,2)) + "s.\n")
    
    # pl.figure()
    # pl.plot(1e6*Resolution*np.arange(np.size(mydata)),mydata)
    
    DATA[ChanName] = list(mydataMain)
    DATA['TimeScale'] = list( Resolution*np.arange(np.size(mydataMain)) )
    
    
    # Saving DATA under .txt :
    if Save == 1:
    # Saving data #
        os.makedirs(os.path.dirname(Filepath), exist_ok=True)
        with open(Filepath, 'a') as f:
            print(DATA, file=f)  
            time.sleep(1)

    return DATA[ChanName], DATA['TimeScale']
    # return mydata, Resolution*np.arange(np.size(mydata))





