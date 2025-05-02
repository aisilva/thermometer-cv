from noaa_sdk import NOAA

n = NOAA()
#res = n.get_forecasts('02134', 'US')#2025 May 1: residing in Allston MA
#for i in res:
#    print(i, '\n')

def get_current_temp():
    observations = n.get_observations('02134', 'US')
    for observation in observations:
        #print(observation)
        #for i in observation: 
        #    print(i, '\n')
        #print(observation['timestamp'], observation['temperature'])
        return observation['temperature']['value']

