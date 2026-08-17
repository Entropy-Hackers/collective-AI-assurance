# H2 self-report classification, full 192-run dataset

LLM-judge (deepseek-v4-flash, same model as the agents) over every 
agent-round's free-text reason. 46157 unique texts classified 
(deduplicated from 55238 total agent-round texts).

| Env | Population | Topology | Sanctioning | n | Aware % | Fair % |
|---|---|---|---|---|---|---|
| commons | mixed | clustered | off | 2147/2147 | 10.9% | 50.3% |
| commons | mixed | clustered | on | 1693/1693 | 11.3% | 48.1% |
| commons | mixed | fully_connected | off | 2153/2153 | 9.1% | 52.7% |
| commons | mixed | fully_connected | on | 2063/2063 | 9.5% | 51.1% |
| commons | mixed | scale_free | off | 2111/2111 | 12.2% | 48.1% |
| commons | mixed | scale_free | on | 1945/1945 | 10.4% | 48.5% |
| commons | uniform_fair | clustered | off | 2400/2400 | 0.3% | 100.0% |
| commons | uniform_fair | clustered | on | 2400/2400 | 0.2% | 100.0% |
| commons | uniform_fair | fully_connected | off | 2399/2399 | 0.6% | 100.0% |
| commons | uniform_fair | fully_connected | on | 2400/2400 | 0.5% | 100.0% |
| commons | uniform_fair | scale_free | off | 2400/2400 | 0.2% | 100.0% |
| commons | uniform_fair | scale_free | on | 2400/2400 | 0.1% | 100.0% |
| triage | mixed | clustered | off | 2398/2398 | 60.1% | 41.7% |
| triage | mixed | clustered | on | 2394/2394 | 59.9% | 43.9% |
| triage | mixed | fully_connected | off | 2399/2399 | 60.4% | 42.6% |
| triage | mixed | fully_connected | on | 2399/2399 | 60.4% | 44.8% |
| triage | mixed | scale_free | off | 2400/2400 | 58.8% | 40.0% |
| triage | mixed | scale_free | on | 2378/2378 | 59.9% | 37.9% |
| triage | uniform_fair | clustered | off | 2394/2394 | 86.0% | 84.1% |
| triage | uniform_fair | clustered | on | 2394/2394 | 88.0% | 78.9% |
| triage | uniform_fair | fully_connected | off | 2396/2396 | 82.2% | 85.8% |
| triage | uniform_fair | fully_connected | on | 2397/2397 | 83.2% | 83.0% |
| triage | uniform_fair | scale_free | off | 2398/2398 | 87.0% | 79.1% |
| triage | uniform_fair | scale_free | on | 2378/2378 | 90.7% | 74.9% |
