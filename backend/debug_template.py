#!/usr/bin/env python3

import json

# Test what the f-string is actually producing
expected_workflow_id = "wf_123"
input_data = {"param1": "value1", "param2": 100}
input_data_json_str = json.dumps(input_data)

template_content = f"Output: {{activepieces:run_workflow:{expected_workflow_id}:{input_data_json_str}}}"

print("Template content:")
print(repr(template_content))
print("Template content (raw):")
print(template_content)

# Test boundary detection
from src.app.service_layer.template_extensions import TemplateExtensionRegistry

registry = TemplateExtensionRegistry()
boundaries = registry._find_extension_boundaries(template_content)
print(f"Found boundaries: {boundaries}")
