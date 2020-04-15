import json
from data_stru import TestInput2, BufferOccupancy


with open(r'example_algorithms\TestInputs\test_input2.json') as f:
  data = json.load(f)

Buffer= BufferOccupancy(
    current = data['Buffer Occupancy']['current'],
    size = data['Buffer Occupancy']['size'],
    time = data['Buffer Occupancy']['time'],
    left = None 
)
Chunk = BufferOccupancy(
    current = data['Chunk']['current'],
    size = data['Chunk']['size'],
    time = data['Chunk']['time'],
    left = data['Chunk']['left'] 
)

TestInput = TestInput2(
    measured_bandwidth=data['Measured Bandwidth'],
    buffer_occupancy = Buffer,
    available_bitrates = data['Available Bitrates'], 
    video_time = data['Video Time'],  
    rebuffering_time = data['Rebuffering Time'],
    rebuffing_flag = data['Rebuffing Flag'], 
    chunk = Chunk,
    previous_bitrate = data["Previous Bitrate"],
    preferred_bitrate = data["Preferred Bitrate"] 
    )


def match(value, list_of_list): 
    for e in list_of_list:
        if value in e:
            return e


def bitmovin(time =TestInput.video_time , rate_sug =TestInput.previous_bitrate[0] , rate_pref =TestInput.preferred_bitrate , R_i = TestInput.available_bitrates, buf_now=TestInput.buffer_occupancy.current):
    '''
    Input: 
    time: the time passed from start (assuming in sec)
    rate_sug: the rate suggested by other switching methods, if at start this is 0p
    R_pre: the preferred startup rate
    buf_now: number of bytes occupied in the buffer
    R_i: Array of bitrates of videos, key will be bitrate, and value will be the byte size of the chunk
    
    Output: 
    Rate_next: The next video rate
    '''
    
    m = len(R_i)-1
    #Preferred Startup Switching
    def perfstartup(time = time, rate_sug = rate_sug, rate_pref = rate_pref, R_i = TestInput.available_bitrates, m =m ):
        s = match(rate_sug,R_i)
        p = match(rate_pref,R_i)
        if time < 10:
            for k in range(m):
                if k == s:
                    rate_next = s[1]
                    return rate_next
                if R_i[k][1] <= p[1]:
                    rate_next = p[1]
                    return rate_next
            rate_next = R_i[0][1]
            return rate_next
        else:
            rate_next = s[1]
            return rate_next
    rate_next = perfstartup(time, rate_sug, rate_pref, R_i = TestInput.available_bitrates)
    #Rate based Swtiching
    R_min = float("inf")
    R_max = 0
    for k in range(m,0,-1):
        if R_max < R_i[k][1] and R_i[k][1] < buf_now:
            R_max = R_i[k][1]
        if R_min > R_i[k][1]:
            R_min = R_i[k][1]
    if R_max > 0:
        rate_next = R_max
    else:
        rate_next = R_min
    return rate_next

next_rate = bitmovin(time =9 , rate_sug ="720p" , rate_pref ="1080p" , R_i = TestInput.available_bitrates, buf_now=TestInput.buffer_occupancy.current)
print(next_rate)


print(match(next_rate,TestInput.available_bitrates)[0])