import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, call # Added AsyncMock, call
import json # Added json

# Assuming TemplateService, MissingVariableError, A2AClientAdapter, GenericRequestData are correctly importable
from backend.src.app.service_layer.template_service import TemplateService, MissingVariableError
from backend.src.app.adapters.a2a_client_adapter import A2AClientAdapter
from backend.src.app.service_layer.template_extensions import GenericRequestData


class TestTemplateService:
    # Assuming TemplateService __init__ needs to be updated to accept a2a_client_adapter
    # This is based on the test setup requirement: TemplateService(a2a_client_adapter=mock_a2a_adapter)
    # If TemplateService is not meant to change, this test setup implies a different way
    # for the adapter to be available to extensions.
    # For now, proceeding as if __init__ is being adapted for the test's purpose.

    @pytest.mark.asyncio
    async def test_render_with_simple_variables(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = "Hello {{name}}! Today is {{day}}."
        variables = {'name': 'World', 'day': 'Monday'}
        expected_output = "Hello World! Today is Monday."
        assert await service.render(template_content, variables) == expected_output

    @pytest.mark.asyncio
    async def test_render_with_extra_variables(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = "Hello {{name}}!"
        variables = {'name': 'World', 'day': 'Tuesday'} # 'day' is extra
        expected_output = "Hello World!"
        assert await service.render(template_content, variables) == expected_output

    @pytest.mark.asyncio
    async def test_render_raises_for_missing_variable(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = "Hello {{name}}! You are {{age}} years old."
        variables = {'name': 'World'} # 'age' is missing
        
        with pytest.raises(MissingVariableError) as excinfo:
            await service.render(template_content, variables)
        
        # The MissingVariableError was simplified to just take a message.
        assert "Missing variable: age" in str(excinfo.value)


    @pytest.mark.asyncio
    async def test_render_with_empty_template(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = ""
        variables: Dict[str, Any] = {}
        expected_output = ""
        assert await service.render(template_content, variables) == expected_output

    @pytest.mark.asyncio
    async def test_render_with_no_variables_in_template(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = "Hello World, no variables here."
        variables = {'name': 'Test'}
        expected_output = "Hello World, no variables here."
        assert await service.render(template_content, variables) == expected_output

    @pytest.mark.asyncio
    async def test_render_with_variables_having_leading_trailing_spaces_in_template(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = "Hello {{ name }}! Today is {{day }}. Weather is {{ condition }}."
        variables = {'name': 'Spacey', 'day': 'Wednesday', 'condition': 'Sunny'}
        expected_output = "Hello Spacey! Today is Wednesday. Weather is Sunny."
        assert await service.render(template_content, variables) == expected_output
        
    @pytest.mark.asyncio
    async def test_render_with_non_string_values(self):
        service = TemplateService(a2a_client_adapter=None)
        template_content = "Name: {{name}}, Age: {{age}}, Active: {{is_active}}"
        variables = {'name': 'Tester', 'age': 30, 'is_active': True}
        expected_output = "Name: Tester, Age: 30, Active: True"
        assert await service.render(template_content, variables) == expected_output

    @pytest.mark.asyncio
    async def test_render_delegated_research_pattern(self) -> None:
        mock_a2a_adapter = AsyncMock(spec=A2AClientAdapter)

        web_search_payload = {"results": ["link1", "link2", "text snippet about topic"]}
        analysis_payload = {"points": ["key point 1 from search", "key point 2 from search"]}
        
        mock_a2a_adapter.execute_remote_capability.side_effect = [
            web_search_payload, 
            analysis_payload
        ]

        # Instantiate TemplateService with the mock adapter
        # This implies TemplateService.__init__ is modified or this is a specific test setup.
        template_service = TemplateService(a2a_client_adapter=mock_a2a_adapter)

        pattern_content = """### Delegated Research and Summarization Workflow

**Objective:** To research a complex topic by first performing a web search through a specialized agent, then extracting key points from the search results using another specialized agent, and finally summarizing these key points using a local LLM.

**Input:**
- `input_query`: The complex research topic.

**Workflow:**

1.  **Perform Web Search:**
    Delegate to `WebSearchAgent` to get raw search results for the `input_query`.
    `{{a2a:invoke:agent_url=http://websearch.agent/a2a:capability=perform_search:query={{input_query}}:output_variable=web_search_results}}`

2.  **Extract Key Points:**
    Delegate to `DataAnalysisAgent` to extract key points from the `web_search_results`.
    `{{a2a:invoke:agent_url=http://dataanalysis.agent/a2a:capability=extract_key_points:data={{web_search_results}}:output_variable=extracted_key_points}}`

3.  **Summarize Key Points:**
    Use the local LLM to summarize the `extracted_key_points`.

    **Prompt to LLM:**
    Based on the following key points, please provide a concise summary of the research topic "{{input_query}}":

    {{extracted_key_points}}
"""
        variables: Dict[str, Any] = {"input_query": "future of AI in healthcare"}
        
        # The TemplateService.render method needs to be async for this to work with async extensions
        # If it's not async, the test or the service needs adjustment.
        # Assuming render is made async or can handle async extensions correctly.
        # Based on previous work, `TemplateExtensionRegistry.process_template_extensions` is async.
        # So, `TemplateService.render` should also be async if it calls that.
        # For now, let's assume render is async as per the test being async.
        rendered_template = await template_service.render(template=pattern_content, variables=variables)

        assert mock_a2a_adapter.execute_remote_capability.call_count == 2
        call_args_list = mock_a2a_adapter.execute_remote_capability.call_args_list

        # Call 1: Web Search
        call1_kwargs = call_args_list[0].kwargs
        assert call1_kwargs['agent_url'] == "http://websearch.agent/a2a"
        assert call1_kwargs['capability_name'] == "perform_search"
        assert isinstance(call1_kwargs['request_payload'], GenericRequestData)
        # The payload for the first call is constructed from input_query
        # The template extension logic would have evaluated {{input_query}}
        # and built the payload_str like '{"query": "future of AI in healthcare"}'
        # So, request_payload.model_dump() should match that.
        # This assertion assumes _a2a_invoke_extension_async is modified/fixed
        # to correctly parse arbitrary key-value pairs like 'query={{input_query}}'
        # into the payload, and render '{{input_query}}' using the 'variables' dict.
        expected_payload1_dict = {"query": "future of AI in healthcare"}
        assert call1_kwargs['request_payload'].model_dump() == expected_payload1_dict
        
        # Call 2: Data Analysis
        call2_kwargs = call_args_list[1].kwargs
        assert call2_kwargs['agent_url'] == "http://dataanalysis.agent/a2a"
        assert call2_kwargs['capability_name'] == "extract_key_points"
        assert isinstance(call2_kwargs['request_payload'], GenericRequestData)
        # Similarly, this assumes 'data={{web_search_results}}' is correctly processed,
        # where '{{web_search_results}}' is resolved from the 'variables' dict
        # (populated by the first call's output_variable) and its dictionary value
        # is used as the value for the "data" key in the payload.
        expected_payload2_dict = {"data": web_search_payload} 
        assert call2_kwargs['request_payload'].model_dump() == expected_payload2_dict

        # Assert the final rendered template
        expected_template = f"""### Delegated Research and Summarization Workflow

**Objective:** To research a complex topic by first performing a web search through a specialized agent, then extracting key points from the search results using another specialized agent, and finally summarizing these key points using a local LLM.

**Input:**
- `input_query`: The complex research topic.

**Workflow:**

1.  **Perform Web Search:**
    Delegate to `WebSearchAgent` to get raw search results for the `input_query`.
    

2.  **Extract Key Points:**
    Delegate to `DataAnalysisAgent` to extract key points from the `web_search_results`.
    

3.  **Summarize Key Points:**
    Use the local LLM to summarize the `extracted_key_points`.

    **Prompt to LLM:**
    Based on the following key points, please provide a concise summary of the research topic "{variables["input_query"]}":

    {json.dumps(analysis_payload)}
"""
        assert rendered_template.strip() == expected_template.strip()
