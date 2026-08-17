# H2 self-report classification, full 192-run dataset

LLM-judge (deepseek-v4-flash, same model as the agents) over every 
agent-round's free-text reason. 59440 unique texts classified 
(deduplicated from 75822 total agent-round texts).

| Env | Population | Topology | Sanctioning | n | Aware % | Fair % |
|---|---|---|---|---|---|---|
| commons | mixed | clustered | off | 5382/5382 | 9.2% | 51.9% |
| commons | mixed | clustered | on | 4647/4647 | 8.0% | 49.8% |
| commons | mixed | fully_connected | off | 2154/2154 | 7.1% | 53.6% |
| commons | mixed | fully_connected | on | 2063/2063 | 6.4% | 52.4% |
| commons | mixed | scale_free | off | 2111/2111 | 9.2% | 49.2% |
| commons | mixed | scale_free | on | 1945/1945 | 8.3% | 49.8% |
| commons | uniform_fair | clustered | off | 5998/5998 | 0.2% | 100.0% |
| commons | uniform_fair | clustered | on | 6000/6000 | 0.2% | 100.0% |
| commons | uniform_fair | fully_connected | off | 2399/2399 | 0.2% | 100.0% |
| commons | uniform_fair | fully_connected | on | 2400/2400 | 0.2% | 100.0% |
| commons | uniform_fair | scale_free | off | 6000/6000 | 0.1% | 100.0% |
| commons | uniform_fair | scale_free | on | 5997/5997 | 0.1% | 100.0% |
| triage | mixed | clustered | off | 2398/2398 | 54.5% | 49.6% |
| triage | mixed | clustered | on | 2394/2394 | 55.3% | 50.0% |
| triage | mixed | fully_connected | off | 2399/2399 | 54.1% | 48.1% |
| triage | mixed | fully_connected | on | 2399/2399 | 54.8% | 48.1% |
| triage | mixed | scale_free | off | 2400/2400 | 52.8% | 48.0% |
| triage | mixed | scale_free | on | 2378/2378 | 55.0% | 47.1% |
| triage | uniform_fair | clustered | off | 2395/2395 | 75.8% | 91.8% |
| triage | uniform_fair | clustered | on | 2394/2394 | 78.6% | 91.3% |
| triage | uniform_fair | fully_connected | off | 2396/2396 | 68.9% | 88.5% |
| triage | uniform_fair | fully_connected | on | 2397/2397 | 72.2% | 87.2% |
| triage | uniform_fair | scale_free | off | 2398/2398 | 75.4% | 88.5% |
| triage | uniform_fair | scale_free | on | 2378/2378 | 81.4% | 88.4% |
