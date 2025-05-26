import unittest
from unittest.mock import MagicMock, patch
import json

# Assuming PYTHONPATH is set up for 'app' to be found (e.g. backend/src is in PYTHONPATH)
from app.service_layer.template_service import TemplateService, UnknownExtensionError
from app.service_layer.template_extensions import mem0_add_extension_function, mem0_search_extension_function, ExtensionArgumentError
from app.adapters.mem0_adapter import Mem0Adapter # Actual adapter for type hint
# Assuming MemoryWriteRequest is not directly needed in test if checking call args on mock

class TestMem0AddExtension(unittest.TestCase):

    def setUp(self):
        self.template_service = TemplateService()
        self.mock_mem0_adapter = MagicMock(spec=Mem0Adapter)
        
        # Register the extension
        self.template_service.register_extension(
            namespace="mem0",
            operation="add",
            func=mem0_add_extension_function
        )
        # Provide the dependency
        self.template_service.dependencies['mem0_adapter'] = self.mock_mem0_adapter

    def test_mem0_add_extension_success(self):
        self.mock_mem0_adapter.add.return_value = "test_memory_id_123"
        
        template = "{{mem0:add:user_id=test_user,text_content=Hello Mem0}}"
        result = self.template_service.render(template_content=template, variables={})
        
        self.mock_mem0_adapter.add.assert_called_once()
        # Assuming MemoryWriteRequest is the type of the first argument to mock_mem0_adapter.add
        call_args = self.mock_mem0_adapter.add.call_args[0][0] 
        
        self.assertEqual(call_args.user_id, "test_user")
        self.assertEqual(call_args.text_content, "Hello Mem0")
        self.assertIsNone(call_args.metadata) # No metadata in this call
        self.assertEqual(result, "test_memory_id_123")

    def test_mem0_add_extension_with_metadata(self):
        self.mock_mem0_adapter.add.return_value = "test_memory_id_456"
        metadata_dict = {"source": "test_source", "timestamp": "12345"}
        # Convert dict to JSON string for the template argument
        metadata_json_string = json.dumps(metadata_dict)

        # Template needs to represent the metadata_json_string as a string argument.
        # If the argument parser expects arguments to be unquoted or only single/double quoted,
        # this needs to be handled carefully.
        # The current parser splits by key=val, val can be unquoted.
        # If metadata_json_string contains spaces, commas, or equals signs, it would break.
        # A robust way is to ensure the template syntax or parser can handle quoted strings
        # or that the JSON string is "safe" for the current parser.
        # For now, assume json.dumps produces a string that won't break the simple k=v parser
        # (e.g., no unquoted commas or equals signs within the JSON string itself).
        # A safer template might be: {{mem0:add:user_id=another_user,text_content=Data with metadata,metadata='{metadata_json_string}'}}
        # However, the current parser in TemplateService doesn't explicitly handle surrounding quotes for values.
        # Let's assume the JSON string produced by json.dumps is simple enough not to break parsing.
        # Example: '{"source": "test_source", "timestamp": "12345"}'
        # This string, if passed as metadata=..., should be fine.
        
        template = f"{{{{mem0:add:user_id=another_user,text_content=Data with metadata,metadata={metadata_json_string}}}}}"
        
        result = self.template_service.render(template_content=template, variables={})
        
        self.mock_mem0_adapter.add.assert_called_once()
        call_args = self.mock_mem0_adapter.add.call_args[0][0]
        
        self.assertEqual(call_args.user_id, "another_user")
        self.assertEqual(call_args.text_content, "Data with metadata")
        self.assertEqual(call_args.metadata, metadata_dict) # mem0_add_extension_function parses the JSON string
        self.assertEqual(result, "test_memory_id_456")

    def test_mem0_add_extension_missing_user_id(self):
        template = "{{mem0:add:text_content=Hello without user}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Argument 'user_id' is required"):
            self.template_service.render(template_content=template, variables={})
        self.mock_mem0_adapter.add.assert_not_called()

    def test_mem0_add_extension_missing_text_content(self):
        template = "{{mem0:add:user_id=test_user_missing_text}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Argument 'text_content' is required"):
            self.template_service.render(template_content=template, variables={})
        self.mock_mem0_adapter.add.assert_not_called()

    def test_mem0_add_extension_adapter_returns_none(self):
        self.mock_mem0_adapter.add.return_value = None
        template = "{{mem0:add:user_id=test_user_ret_none,text_content=Test None Return}}"
        result = self.template_service.render(template_content=template, variables={})
        self.assertEqual(result, "") 
        self.mock_mem0_adapter.add.assert_called_once()

    def test_mem0_add_extension_adapter_raises_exception(self):
        self.mock_mem0_adapter.add.side_effect = Exception("Adapter failure")
        template = "{{mem0:add:user_id=test_user_adapter_ex,text_content=Test Adapter Exception}}"
        result = self.template_service.render(template_content=template, variables={})
        self.assertEqual(result, "") # Extension catches exception and returns ""
        self.mock_mem0_adapter.add.assert_called_once()
        
    def test_mem0_add_extension_invalid_metadata_json(self):
        # Use a string that is definitely not valid JSON for the metadata argument
        # The template service argument parser will pass '{invalid_json_string}' as the value for metadata
        template = "{{mem0:add:user_id=test_user_invalid_json,text_content=Test Invalid JSON,metadata='{invalid_json_string}'}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Invalid JSON in 'metadata' argument"):
            self.template_service.render(template_content=template, variables={})
        self.mock_mem0_adapter.add.assert_not_called()

    def test_unknown_extension_namespace(self):
        template = "{{unknown:add:key=val}}"
        with self.assertRaisesRegex(UnknownExtensionError, "Unknown extension: unknown:add"):
            self.template_service.render(template_content=template, variables={})

    def test_unknown_extension_operation(self):
        template = "{{mem0:unknown_op:key=val}}"
        with self.assertRaisesRegex(UnknownExtensionError, "Unknown extension: mem0:unknown_op"):
            self.template_service.render(template_content=template, variables={})
            
    def test_mem0_add_extension_no_mem0_adapter_dependency(self):
        template_service_no_deps = TemplateService() # New service without dependencies
        template_service_no_deps.register_extension(
            namespace="mem0",
            operation="add",
            func=mem0_add_extension_function
        )
        # Note: self.mock_mem0_adapter is the one associated with self.template_service
        # Here, template_service_no_deps.dependencies['mem0_adapter'] is missing.
        
        template = "{{mem0:add:user_id=test_dep_fail,text_content=Hello}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Dependency 'mem0_adapter' not found"):
            template_service_no_deps.render(template_content=template, variables={})
        
        # Ensure the original mock (associated with self.template_service) was not called
        self.mock_mem0_adapter.add.assert_not_called()

if __name__ == '__main__':
    unittest.main()

# Mock search result object if needed for testing serialization
class MockSearchResult:
    def __init__(self, id, text, score, **kwargs):
        self.id = id
        self.text = text
        self.score = score
        self.extra_data = kwargs # To simulate other potential fields

    def dict(self): # Simulate a Pydantic model's dict() method
        return {"id": self.id, "text": self.text, "score": self.score, **self.extra_data}

    def __str__(self):
        return f"MockSearchResult(id={self.id}, text='{self.text}', score={self.score})"


class TestMem0SearchExtension(unittest.TestCase):

    def setUp(self):
        self.template_service = TemplateService()
        self.mock_mem0_adapter = MagicMock(spec=Mem0Adapter)
        
        # Register the extension
        self.template_service.register_extension(
            namespace="mem0",
            operation="search",
            func=mem0_search_extension_function
        )
        # Provide the dependency
        self.template_service.dependencies['mem0_adapter'] = self.mock_mem0_adapter

    def test_mem0_search_extension_success(self):
        mock_results = [
            MockSearchResult(id="res1", text="Result 1", score=0.9, source="doc1"),
            MockSearchResult(id="res2", text="Result 2", score=0.8, source="doc2")
        ]
        self.mock_mem0_adapter.search.return_value = mock_results
        
        template = "{{mem0:search:user_id=test_user,query=my query}}"
        result_json = self.template_service.render(template_content=template, variables={})
        
        self.mock_mem0_adapter.search.assert_called_once_with(
            user_id="test_user", 
            query="my query", 
            limit=None, 
            min_score=None
        )
        
        expected_output = json.dumps([res.dict() for res in mock_results])
        self.assertEqual(result_json, expected_output)

    def test_mem0_search_extension_with_limit_and_min_score(self):
        mock_results = [MockSearchResult(id="res3", text="Limited Result", score=0.95)]
        self.mock_mem0_adapter.search.return_value = mock_results
        
        template = "{{mem0:search:user_id=test_user,query=specific query,limit=5,min_score=0.7}}"
        result_json = self.template_service.render(template_content=template, variables={})
        
        self.mock_mem0_adapter.search.assert_called_once_with(
            user_id="test_user", 
            query="specific query", 
            limit=5, 
            min_score=0.7
        )
        expected_output = json.dumps([res.dict() for res in mock_results])
        self.assertEqual(result_json, expected_output)

    def test_mem0_search_extension_missing_user_id(self):
        template = "{{mem0:search:query=some query}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Argument 'user_id' is required"):
            self.template_service.render(template_content=template, variables={})
        self.mock_mem0_adapter.search.assert_not_called()

    def test_mem0_search_extension_missing_query(self):
        template = "{{mem0:search:user_id=test_user_no_query}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Argument 'query' is required"):
            self.template_service.render(template_content=template, variables={})
        self.mock_mem0_adapter.search.assert_not_called()

    def test_mem0_search_invalid_limit(self):
        template = "{{mem0:search:user_id=test_user,query=q,limit=not_an_int}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Argument 'limit' must be an integer"):
            self.template_service.render(template, {})
        self.mock_mem0_adapter.search.assert_not_called()

    def test_mem0_search_invalid_min_score(self):
        template = "{{mem0:search:user_id=test_user,query=q,min_score=not_a_float}}"
        with self.assertRaisesRegex(ExtensionArgumentError, "Argument 'min_score' must be a float"):
            self.template_service.render(template, {})
        self.mock_mem0_adapter.search.assert_not_called()
        
    def test_mem0_search_extension_no_results(self):
        self.mock_mem0_adapter.search.return_value = []
        template = "{{mem0:search:user_id=test_user_no_res,query=query for no results}}"
        result_json = self.template_service.render(template_content=template, variables={})
        self.assertEqual(result_json, "[]")
        self.mock_mem0_adapter.search.assert_called_once()

    def test_mem0_search_extension_adapter_raises_exception(self):
        self.mock_mem0_adapter.search.side_effect = Exception("Adapter search failure")
        template = "{{mem0:search:user_id=test_user_adapter_ex,query=query causing exception}}"
        result_json = self.template_service.render(template_content=template, variables={})
        self.assertEqual(result_json, "[]") # Expect empty JSON array on error
        self.mock_mem0_adapter.search.assert_called_once()
        
    def test_mem0_search_extension_serialization_fallback_str(self):
        # Test the case where results items don't have .dict() but are convertible to string
        class SimpleObject:
            def __init__(self, value):
                self.value = value
            def __str__(self):
                return f"Simple: {self.value}"

        mock_results = [SimpleObject("data1"), SimpleObject("data2")]
        self.mock_mem0_adapter.search.return_value = mock_results
        
        template = "{{mem0:search:user_id=test_user_fallback,query=fallback query}}"
        result_json = self.template_service.render(template_content=template, variables={})
        
        # json.dumps will call str() on objects if they are not directly serializable
        # and are part of a list being dumped.
        expected_output = json.dumps([str(res) for res in mock_results])
        self.assertEqual(result_json, expected_output)
        self.mock_mem0_adapter.search.assert_called_once()

    def test_mem0_search_extension_serialization_failure(self):
        # Test the case where results items are not JSON serializable at all
        class NonSerializableObject:
            pass

        mock_results = [NonSerializableObject(), NonSerializableObject()]
        self.mock_mem0_adapter.search.return_value = mock_results
        
        template = "{{mem0:search:user_id=test_user_unserializable,query=unserializable query}}"
        result_json = self.template_service.render(template_content=template, variables={})
        
        # Based on the implementation, it should fall back to "[]"
        self.assertEqual(result_json, "[]")
        self.mock_mem0_adapter.search.assert_called_once()
