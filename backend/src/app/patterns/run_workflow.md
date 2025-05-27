---
name: "Run ActivePieces Workflow"
description: "Runs a specified ActivePieces workflow with the given input data (must be a JSON string)."
variables:
  workflow_id: "string"
  input_data_json: "string" # This variable must be a valid JSON string
---
Okay, I will run workflow `{{workflow_id}}`.
I will use this data:
```json
{{input_data_json}}
```
Workflow result:
{{activepieces:run_workflow:{{workflow_id}}:{{input_data_json}}}}
