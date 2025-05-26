import pytest
from typing import Dict, Any
from backend.src.app.service_layer.template_service import TemplateService, MissingVariableError

class TestTemplateService:
    def test_render_with_simple_variables(self):
        service = TemplateService()
        template_content = "Hello {{name}}! Today is {{day}}."
        variables = {'name': 'World', 'day': 'Monday'}
        expected_output = "Hello World! Today is Monday."
        assert service.render(template_content, variables) == expected_output

    def test_render_with_extra_variables(self):
        service = TemplateService()
        template_content = "Hello {{name}}!"
        variables = {'name': 'World', 'day': 'Tuesday'} # 'day' is extra
        expected_output = "Hello World!"
        assert service.render(template_content, variables) == expected_output

    def test_render_raises_for_missing_variable(self):
        service = TemplateService()
        template_content = "Hello {{name}}! You are {{age}} years old."
        variables = {'name': 'World'} # 'age' is missing
        
        with pytest.raises(MissingVariableError) as excinfo:
            service.render(template_content, variables)
        
        assert excinfo.value.variable_name == "age"
        assert str(excinfo.value) == "Missing variable: age"

    def test_render_with_empty_template(self):
        service = TemplateService()
        template_content = ""
        variables: Dict[str, Any] = {}
        expected_output = ""
        assert service.render(template_content, variables) == expected_output

    def test_render_with_no_variables_in_template(self):
        service = TemplateService()
        template_content = "Hello World, no variables here."
        variables = {'name': 'Test'}
        expected_output = "Hello World, no variables here."
        assert service.render(template_content, variables) == expected_output

    def test_render_with_variables_having_leading_trailing_spaces_in_template(self):
        service = TemplateService()
        template_content = "Hello {{ name }}! Today is {{day }}. Weather is {{ condition }}."
        variables = {'name': 'Spacey', 'day': 'Wednesday', 'condition': 'Sunny'}
        expected_output = "Hello Spacey! Today is Wednesday. Weather is Sunny."
        assert service.render(template_content, variables) == expected_output
        
    def test_render_with_non_string_values(self):
        service = TemplateService()
        template_content = "Name: {{name}}, Age: {{age}}, Active: {{is_active}}"
        variables = {'name': 'Tester', 'age': 30, 'is_active': True}
        expected_output = "Name: Tester, Age: 30, Active: True"
        assert service.render(template_content, variables) == expected_output
