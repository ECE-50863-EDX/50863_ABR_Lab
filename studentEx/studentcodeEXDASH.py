import random

random.seed(None)

def student_entrypoint(Measured_Bandwidth, Previous_Throughput, Buffer_Occupancy, Available_Bitrates, Video_Time, Chunk, Rebuffering_Time, Preferred_Bitrate ):
    #student can do whatever they want from here going forward
    R_i = list(Available_Bitrates.items())
    # R_i.sort(key=lambda tup: tup[1] , reverse=True)
    return HYB(buffer_time =Buffer_Occupancy['time'],B =Previous_Throughput  ,est_bandwidth=Measured_Bandwidth, beta=.2, L = Buffer_Occupancy['current'], R_i = R_i)
    # return random_choice(Available_Bitrates)
    #pass

def random_choice(bitrates):
    bitrates_list = [(key, value) for key, value in bitrates.items()]
    choiceind = random.randrange(1, len(bitrates))
    return bitrates_list[choiceind - 1][0]


def DASH(buf_current = TestInput.buffer_occupancy.current, rebuffering = TestInput.rebuffering_time ,est_bandwidth=TestInput.measured_bandwidth, T_low=4, T_rich=20, R_i = TestInput.available_bitrates, previous_bitrate =[144,200]):
    '''
    Input: 
    T_low = 4: the threshold for deciding that the buffer length is low
    T_rich = 20: the threshold for deciding that the buffer length is sufficient 
    est_bandwidth: estimated bandwidth
    rebuffering: flag stating that was rebuffing from last bitrate decision
    buf_current: number of bytes occupied in the buffer
    R_i: Array of bitrates of videos, key will be bitrate, and value will be the byte size of the chunk
    previous_bitrate:

    Output: 
    Rate_next: The next video rate
    '''
    #throughput rule:
    m = len(R_i)-1
    if buf_current >= T_low*2:
        for k in range(0, m):
            if est_bandwidth >= R_i[k][1]:
                rate_next = R_i[k][1]
                break
    # print(rate_next)
    # print('^1st')
    
    #insufficient buffer rule: 
    
    if rebuffering == 0:
        rate_next = R_i[m][1]
        # print(rate_next)
    elif T_low < buf_current and buf_current < T_low *2:
        # print(previous_bitrate)
        # print(R_i)
        R_min = match(min(i[1] for i in R_i),R_i)
        # print(R_min)
        i=index(previous_bitrate,R_i)
        if R_min == R_i[i]:
            rate_next = R_i[i][1]
        else:
            rate_next = R_i[i+1][1]    
        # print(i)
        # print(rate_next)
    # print(rate_next)
    # print('^2nd')
    
    # #buffer occupany rule: 
    if buf_current > T_rich:
        rate_next = R_i[0][1]
    # print(rate_next)
    # print('^last')
    return rate_next