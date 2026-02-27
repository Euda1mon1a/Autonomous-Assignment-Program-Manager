import inspect
import importlib
import os
from pathlib import Path

os.environ["DEBUG"] = "true"

constraint_dir = Path('backend/app/scheduling/constraints')
registry = []

for filepath in constraint_dir.glob('*.py'):
    if filepath.name == '__init__.py' or filepath.name == 'base.py':
        continue

    module_name = f'app.scheduling.constraints.{filepath.stem}'
    try:
        module = importlib.import_module(module_name)
    except Exception as e:
        print(f"Failed to import {module_name}: {e}")
        continue

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if obj.__module__ == module_name and 'Constraint' in name and name not in ('Constraint', 'HardConstraint', 'SoftConstraint'):
            bases = [b.__name__ for b in obj.__bases__]
            constraint_type = 'Hard' if 'HardConstraint' in bases else ('Soft' if 'SoftConstraint' in bases else 'Unknown')
            doc = ''
            if obj.__doc__:
                doc_lines = obj.__doc__.strip().splitlines()
                if doc_lines:
                    doc = doc_lines[0].strip()
            registry.append(f'| `{name}` | `{filepath.name}` | {constraint_type} | {doc} |')

output = []
output.append('# Scheduling Engine Constraints Registry')
output.append('')
output.append('This document lists all the constraints available to the CP-SAT scheduling engine.')
output.append('')
output.append('| Constraint Class | File | Type | Description |')
output.append('| --- | --- | --- | --- |')
for row in sorted(registry):
    output.append(row)

output_str = "\n".join(output) + "\n"

with open('docs/scheduling/CONSTRAINTS_REGISTRY.md', 'w') as f:
    f.write(output_str)
