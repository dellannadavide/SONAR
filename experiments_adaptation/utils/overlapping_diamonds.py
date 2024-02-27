diam = {
    "DUTY": ["High", "Low", "Low"],
    "INTELLECT": ["Medium", "Low", "Low"],
    "ADVERSITY": ["High", "High", "High"],
    "MATING": ["Low", "Low", "Low"],
    "POSITIVITY": ["Medium", "High", "High"],
    "NEGATIVITY": ["High", "Medium", "Medium"],
    "DECEPTION": ["Low", "Medium", "Medium"],
    "SOCIALITY": ["Medium", "Medium", "Medium"]
}

not_overlapping = {}
for d in diam:
    not_overlapping[d] = set()
    for d1 in diam:
        found_overlapping = False
        for i in range(len(diam[d])):
            if diam[d][i] == diam[d1][i]:
                found_overlapping = True
        if not found_overlapping:
            not_overlapping[d].add(d1)

for k, s in not_overlapping.items():
    print(str(k) + ": " + str(s))
    print(len(s))

print(not_overlapping)

"""
DUTY: {'DECEPTION', 'POSITIVITY', 'SOCIALITY'}
3
INTELLECT: {'DECEPTION', 'NEGATIVITY', 'ADVERSITY'}
3
ADVERSITY: {'MATING', 'DECEPTION', 'INTELLECT', 'SOCIALITY'}
4
MATING: {'POSITIVITY', 'NEGATIVITY', 'ADVERSITY', 'SOCIALITY'}
4
POSITIVITY: {'MATING', 'DECEPTION', 'NEGATIVITY', 'DUTY'}
4
NEGATIVITY: {'MATING', 'POSITIVITY', 'INTELLECT'}
3
DECEPTION: {'POSITIVITY', 'INTELLECT', 'ADVERSITY', 'DUTY'}
4
SOCIALITY: {'MATING', 'ADVERSITY', 'DUTY'}
3
{'DUTY': {'DECEPTION', 'POSITIVITY', 'SOCIALITY'}, 'INTELLECT': {'DECEPTION', 'NEGATIVITY', 'ADVERSITY'}, 'ADVERSITY': {'MATING', 'DECEPTION', 'INTELLECT', 'SOCIALITY'}, 'MATING': {'POSITIVITY', 'NEGATIVITY', 'ADVERSITY', 'SOCIALITY'}, 'POSITIVITY': {'MATING', 'DECEPTION', 'NEGATIVITY', 'DUTY'}, 'NEGATIVITY': {'MATING', 'POSITIVITY', 'INTELLECT'}, 'DECEPTION': {'POSITIVITY', 'INTELLECT', 'ADVERSITY', 'DUTY'}, 'SOCIALITY': {'MATING', 'ADVERSITY', 'DUTY'}}


** Process exited - Return Code: 0 **
Press Enter to exit terminal

"""
