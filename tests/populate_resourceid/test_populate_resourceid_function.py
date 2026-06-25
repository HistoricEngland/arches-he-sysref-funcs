import os
import random
import uuid

from arches.app.models.graph import Graph
from arches.app.models import models
from .base_test import BasePopulateResourceIDTestCase

# These tests can be run from the command line via:
#     python manage.py test tests.populate_resourceid.test_populate_resourceid_function --settings="tests.test_settings"
# or if using Docker:
#     python manage.py test tests.populate_resourceid.test_populate_resourceid_function --settings="tests.test_settings_for_docker"


class TestPopulateResourceIDFunction(BasePopulateResourceIDTestCase):

    # Test methods are named alphabetically, so the order of execution is predictable.

    # Has the function been registered?
    def test_01_function_exists(self):
        fn = models.Function.objects.all()
        self.assertTrue(fn.filter(name="Generate ResourceID").exists())

    # Does the test graph exist?
    def test_02_graph_exists(self):
        graph = Graph.objects.filter(graphid=self.test_model_graph_id)
        self.assertTrue(graph.exists())

    # Is the test graph configured to run the populate_resourceid function?
    def test_02b_graph_uses_generate_resourceid_function(self):
        registered_function = models.Function.objects.get(name="Generate ResourceID")
        self.assertTrue(
            models.FunctionXGraph.objects.filter(
                graph_id=self.test_model_graph_id,
                function_id=registered_function.functionid,
            ).exists()
        )

    # Model: Test Model; Save tile with None ResourceID - should populate with resource instance ID
    def test_03_create_test_model_with_none_resourceid(self):
        """
        When a tile in the resource reference nodegroup is saved with a None resource ID,
        the function should populate it with the resource instance ID.
        """
        tile_data = {
            "282839be-58f8-11f1-a45a-02e06202dcc7": None,
            "28283784-58f8-11f1-a45a-02e06202dcc7": None,
            "28283540-58f8-11f1-a45a-02e06202dcc7": None,
            "282828e8-58f8-11f1-a45a-02e06202dcc7": None,
            "28283f5e-58f8-11f1-a45a-02e06202dcc7": None,
            "28284404-58f8-11f1-a45a-02e06202dcc7": None,
        }
        populated_resourceid, resource_id = self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            self.system_reference_nodegroup_id,
        )
        populated_resourceid_value = self._extract_resourceid_value(
            populated_resourceid
        )
        # ResourceID should be populated with the resource instance ID
        self.assertEqual(populated_resourceid_value, resource_id)
        # Verify it's a valid UUID
        try:
            uuid.UUID(populated_resourceid_value)
        except (ValueError, TypeError):
            self.fail(f"Resource ID '{populated_resourceid_value}' is not a valid UUID")

    # Model: Test Model; Save tile with empty string ResourceID
    def test_04_create_test_model_with_empty_string_resourceid(self):
        """
        When a tile is saved with an empty string in resource ID, the function should
        populate it with the resource instance ID.
        """
        tile_data = {
            "282839be-58f8-11f1-a45a-02e06202dcc7": self._localized(""),
            "28283784-58f8-11f1-a45a-02e06202dcc7": None,
            "28283540-58f8-11f1-a45a-02e06202dcc7": None,
            "282828e8-58f8-11f1-a45a-02e06202dcc7": None,
            "28283f5e-58f8-11f1-a45a-02e06202dcc7": None,
            "28284404-58f8-11f1-a45a-02e06202dcc7": None,
        }
        populated_resourceid, resource_id = self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            self.system_reference_nodegroup_id,
        )
        populated_resourceid_value = self._extract_resourceid_value(
            populated_resourceid
        )
        self.assertEqual(populated_resourceid_value, resource_id)

    # Model: Test Model; Save tile with invalid string ResourceID
    def test_05_create_test_model_with_invalid_string_resourceid(self):
        """
        When a tile is saved with an invalid (non-UUID) string in resource ID,
        the function should replace it with the resource instance ID.
        """
        tile_data = {
            "282839be-58f8-11f1-a45a-02e06202dcc7": self._localized(
                "This is NOT a valid UUID"
            ),
            "28283784-58f8-11f1-a45a-02e06202dcc7": None,
            "28283540-58f8-11f1-a45a-02e06202dcc7": None,
            "282828e8-58f8-11f1-a45a-02e06202dcc7": None,
            "28283f5e-58f8-11f1-a45a-02e06202dcc7": None,
            "28284404-58f8-11f1-a45a-02e06202dcc7": None,
        }
        populated_resourceid, resource_id = self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            self.system_reference_nodegroup_id,
        )
        populated_resourceid_value = self._extract_resourceid_value(
            populated_resourceid
        )
        self.assertEqual(populated_resourceid_value, resource_id)

    # Model: Test Model; Save tile with valid UUID ResourceID
    def test_06_create_test_model_with_valid_uuid_resourceid(self):
        """
        When a tile is saved with a valid UUID in the resource ID field,
        the function should preserve that UUID.
        """
        valid_uuid = str(uuid.uuid4())
        tile_data = {
            "282839be-58f8-11f1-a45a-02e06202dcc7": self._localized(valid_uuid),
            "28283784-58f8-11f1-a45a-02e06202dcc7": None,
            "28283540-58f8-11f1-a45a-02e06202dcc7": None,
            "282828e8-58f8-11f1-a45a-02e06202dcc7": None,
            "28283f5e-58f8-11f1-a45a-02e06202dcc7": None,
            "28284404-58f8-11f1-a45a-02e06202dcc7": None,
        }
        populated_resourceid, resource_id = self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            self.system_reference_nodegroup_id,
        )
        populated_resourceid_value = self._extract_resourceid_value(
            populated_resourceid
        )
        # Valid UUID should be preserved
        self.assertEqual(populated_resourceid_value, valid_uuid)

    # Model: Test Model; Save tile with numeric ResourceID (invalid)
    def test_07_create_test_model_with_numeric_resourceid(self):
        """
        When a tile is saved with a numeric value in the resource ID field,
        the function should replace it with the resource instance ID.
        """
        tile_data = {
            "282839be-58f8-11f1-a45a-02e06202dcc7": self._localized("12345"),
            "28283784-58f8-11f1-a45a-02e06202dcc7": None,
            "28283540-58f8-11f1-a45a-02e06202dcc7": None,
            "282828e8-58f8-11f1-a45a-02e06202dcc7": None,
            "28283f5e-58f8-11f1-a45a-02e06202dcc7": None,
            "28284404-58f8-11f1-a45a-02e06202dcc7": None,
        }
        populated_resourceid, resource_id = self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            self.system_reference_nodegroup_id,
        )
        populated_resourceid_value = self._extract_resourceid_value(
            populated_resourceid
        )
        self.assertEqual(populated_resourceid_value, resource_id)

    # Model: Test Model; Save non-reference tile with None ResourceID
    def test_08_create_test_model_description_tile_with_none_resourceid(self):
        """
        When a non-reference tile (Description) is saved with None resource ID,
        the function should find or create reference tiles and populate their resource ID.
        """
        tile_data = {
            self.description_node_id: {
                "en": {"value": "Test description", "direction": "ltr"}
            }
        }
        populated_resourceid, resource_id = self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            self.description_nodegroup_id,
            resourceid_node=self.resourceid_node_id,
        )
        self.assertIsNotNone(resource_id)

    # Model: Test Model; Multiple resources with ResourceIDs
    def test_09_create_multiple_resources_with_resourceids(self):
        """
        Create multiple resources and verify each gets a unique ResourceID.
        """
        resource_ids = []
        for i in range(5):
            tile_data = {
                "282839be-58f8-11f1-a45a-02e06202dcc7": None,
                "28283784-58f8-11f1-a45a-02e06202dcc7": None,
                "28283540-58f8-11f1-a45a-02e06202dcc7": None,
                "282828e8-58f8-11f1-a45a-02e06202dcc7": None,
                "28283f5e-58f8-11f1-a45a-02e06202dcc7": None,
                "28284404-58f8-11f1-a45a-02e06202dcc7": None,
            }
            populated_resourceid, resource_id = self.create_and_assert_resource(
                self.test_model_graph_id,
                tile_data,
                self.system_reference_nodegroup_id,
            )
            extracted = self._extract_resourceid_value(populated_resourceid)
            # Each resource's ID should match its own instance ID
            self.assertEqual(extracted, resource_id)
            resource_ids.append(extracted)

        # Verify all resource IDs are unique
        self.assertEqual(len(resource_ids), len(set(resource_ids)))

    # Run all tests in a randomized order multiple times
    def test_10_run_randomized_tests_multiple_times(self):
        """
        Run all test scenarios in randomized order multiple times to ensure
        the function handles concurrent operations correctly.
        """
        test_methods = [
            self.test_03_create_test_model_with_none_resourceid,
            self.test_04_create_test_model_with_empty_string_resourceid,
            self.test_05_create_test_model_with_invalid_string_resourceid,
            self.test_06_create_test_model_with_valid_uuid_resourceid,
            self.test_07_create_test_model_with_numeric_resourceid,
            self.test_08_create_test_model_description_tile_with_none_resourceid,
        ]
        for i in range(25):
            random.shuffle(test_methods)
            for test in test_methods:
                test()
