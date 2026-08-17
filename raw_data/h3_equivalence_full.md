# H3: institutional sanctioning does not reduce Gini inequality

**H3 (confirmatory, uniform_fair x scale_free, both environments):**
institutional peer sanctioning does not reduce the Gini inequality of
final payoffs -- even in the condition where sanctioning demonstrably
targets high-degree agents disproportionately -- i.e. the effect of
sanctioning on/off on Gini is, within a pre-specified practical
equivalence margin (+/-0.05), statistically indistinguishable from
zero, not merely "not significant". The other ten cells (per
environment) are reported descriptively, not part of the confirmatory
claim -- the same asymmetric scope H1 itself uses.

Bootstrap CI (95%, 10000 resamples) on mean(Gini | sanctioning=on) - mean(Gini | sanctioning=off).

| Env | Population | Topology | Confirmatory | n off/on | delta Gini | CI | Equivalent (within margin)? |
|---|---|---|---|---|---|---|---|
| commons | uniform_fair | fully_connected | descriptive | 8/8 | -0.1187 | [-0.3562, +0.0000] | no |
| commons | uniform_fair | clustered | descriptive | 20/20 | +0.0101 | [-0.0238, +0.0463] | **yes** |
| commons | uniform_fair | scale_free | **yes** | 20/20 | +0.0460 | [+0.0124, +0.0791] | no |
| commons | mixed | fully_connected | descriptive | 8/8 | -0.0140 | [-0.0352, +0.0098] | **yes** |
| commons | mixed | clustered | descriptive | 20/20 | -0.0068 | [-0.0239, +0.0097] | **yes** |
| commons | mixed | scale_free | descriptive | 8/8 | +0.0008 | [-0.0224, +0.0258] | **yes** |
| triage | uniform_fair | fully_connected | descriptive | 8/8 | +0.0505 | [+0.0006, +0.1016] | no |
| triage | uniform_fair | clustered | descriptive | 8/8 | -0.0124 | [-0.0711, +0.0429] | no |
| triage | uniform_fair | scale_free | **yes** | 8/8 | -0.0029 | [-0.0486, +0.0425] | **yes** |
| triage | mixed | fully_connected | descriptive | 8/8 | +0.0087 | [-0.0272, +0.0437] | **yes** |
| triage | mixed | clustered | descriptive | 8/8 | +0.0064 | [-0.0248, +0.0332] | **yes** |
| triage | mixed | scale_free | descriptive | 8/8 | +0.0168 | [-0.0332, +0.0731] | no |
