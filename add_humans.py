import json

with open("C:\\PersonalRepo\\portfolio\\autogen\\autogen_dashboard\\blueprints.py", "r", encoding="utf-8") as f:
    content = f.read()

# We need to add the human-operator node to each phase, and link it to the first meta node.
# e.g., Phase 1: 1.1 Intent Translation
# Phase 2: 2.1 Feature Impl
# Phase 3: 3.1 Auto Test Gen
# Phase 4: 4.1 Auto Patching
# Phase 5: 5.1 PR Review
# Phase 6: 6.1 Continuous Tech Debt

import re

for i in range(1, 7):
    node_str = f'    {{"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": f"p{i}-group"}},'
    edge_str = f'    {{"type": "edge_created", "data": {{"id": f"p{i}-e0", "source": "human-operator", "target": f"{i}.1", "label": "Triggers Phase"}}}},'
    
    # Add node
    search_node = f'phase{i}_nodes = [\n    {{"id": "p{i}-group"'
    replace_node = f'phase{i}_nodes = [\n    {{"id": "p{i}-group"...\n{node_str}'
    content = re.sub(
        rf'phase{i}_nodes = \[\n    {{"id": "p{i}-group"(.*?)\]',
        lambda m: f'phase{i}_nodes = [\n    {{"id": "p{i}-group"{m.group(1).split(",")[0] + "," + m.group(1).split(",", 1)[1]}\n{node_str}',
        content,
        flags=re.DOTALL
    )
    # The regex approach is messy, let's just do simple splits.

def add_human(phase_num):
    global content
    
    # Add node
    target_node = f'{{"id": "p{phase_num}-group"'
    idx = content.find(target_node)
    end_of_line = content.find('\n', idx)
    node_str = f'\n    {{"id": "human-operator", "label": "Human Operator (You)", "type": "customNode", "status": "System Prompt", "instructions": "You govern the entire OS.", "parentId": "p{phase_num}-group"}},'
    content = content[:end_of_line] + node_str + content[end_of_line:]
    
    # Add edge
    target_edge = f'phase{phase_num}_edges = ['
    idx = content.find(target_edge)
    end_of_line = content.find('\n', idx)
    edge_str = f'\n    {{"type": "edge_created", "data": {{"id": "p{phase_num}-e0", "source": "human-operator", "target": "{phase_num}.1", "label": "Triggers Phase"}}}},'
    content = content[:end_of_line] + edge_str + content[end_of_line:]

with open("C:\\PersonalRepo\\portfolio\\autogen\\autogen_dashboard\\blueprints.py", "r", encoding="utf-8") as f:
    content = f.read()

for i in range(1, 7):
    add_human(i)

with open("C:\\PersonalRepo\\portfolio\\autogen\\autogen_dashboard\\blueprints.py", "w", encoding="utf-8") as f:
    f.write(content)
