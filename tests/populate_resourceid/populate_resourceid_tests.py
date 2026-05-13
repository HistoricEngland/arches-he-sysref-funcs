import os
import random
import uuid

from django.test import TransactionTestCase
from arches.app.models.graph import Graph
from arches.app.models import models
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.data_management.resource_graphs.importer import (
    import_graph as resource_graph_importer,
)
from django.contrib.auth.models import User
from arches.app.models.resource import Resource
from arches.app.models.tile import Tile
from django.core.management import call_command

# These tests can be run from the command line via:
#     python manage.py test tests.populate_resourceid.populate_resourceid_tests --settings="tests.test_settings"
# or if using Docker:
#     python manage.py test tests.populate_resourceid.populate_resourceid_tests --settings="tests.test_settings_for_docker"


class TestPopulateResourceIDFunction(TransactionTestCase):

    serialized_rollback = True

    test_model_graph_id = "7a9d0a60-63f0-11f0-9f7e-460d1d596ee6"

    # Node IDs from test_model.json fixture
    resourceid_node_id = "7a9d162c-63f0-11f0-9f7e-460d1d596ee6"
    system_reference_nodegroup_id = "7a9d0cfe-63f0-11f0-9f7e-460d1d596ee6"
    description_node_id = "7a9d1924-63f0-11f0-9f7e-460d1d596ee6"
    description_nodegroup_id = "7a9d1226-63f0-11f0-9f7e-460d1d596ee6"
    language_code = "en"
    default_direction = "ltr"

    def setUp(self):
        super().setUp()

        # Need to register function before the graphs are imported
        source = os.path.join(
            "arches_he_sysref_funcs",
            "functions",
            "populate_resourceid.py",
        )

        call_command("fn", "register", source=source)

        admin = User.objects.get(username="admin")

        # Import test_model graph
        with open(
            os.path.join("tests/fixtures/resource_graphs/test_model_populateid.json"),
            "r",
        ) as f:
            archesfile = JSONDeserializer().deserialize(f)
        resource_graph_importer(archesfile["graph"])

        # Ensure the imported test model is bound to the registered function.
        registered_function = models.Function.objects.get(name="Generate ResourceID")
        graph_function = models.FunctionXGraph.objects.filter(
            graph_id=self.test_model_graph_id
        ).first()
        if (
            graph_function
            and graph_function.function_id != registered_function.functionid
        ):
            graph_function.function_id = registered_function.functionid
            graph_function.save(update_fields=["function_id"])

        graph = Graph.objects.get(graphid=self.test_model_graph_id)
        graph.publish(user=admin)

    def create_and_assert_resource(
        self, graph_id, tile_data, nodegroup_id, resourceid_node=None
    ):
        """
        Creates a resource with a tile and verifies the Resource ID is correctly populated.

        Args:
            graph_id: The graph to create the resource in
            tile_data: The tile data to save
            nodegroup_id: The nodegroup ID for the tile
            resourceid_node: The node ID that should contain the Resource ID

        Returns:
            A tuple of (populated_resourceid_value, resource_instance_id)
        """
        if resourceid_node is None:
            resourceid_node = self.resourceid_node_id

        graph = Graph.objects.get(pk=graph_id)
        resource = Resource(graph=graph)
        tile = Tile(data=tile_data, nodegroup_id=nodegroup_id)
        resource.tiles.append(tile)
        resource.save()

        # Fetch the saved tile to get the populated resourceid
        saved_tiles = Tile.objects.filter(
            nodegroup_id=nodegroup_id, resourceinstance_id=resource.resourceinstanceid
        )

        if saved_tiles.exists():
            saved_tile = saved_tiles.first()
            populated_resourceid = saved_tile.data.get(resourceid_node)
            return populated_resourceid, str(resource.resourceinstanceid)

        return None, str(resource.resourceinstanceid)

    # Test methods are named alphabetically, so the order of execution is predictable.

    def _localized(self, value):
        return {
            self.language_code: {
                "value": value,
                "direction": self.default_direction,
            }
        }

    def _extract_resourceid_value(self, node_value):
        if isinstance(node_value, dict):
            return node_value.get(self.language_code, {}).get("value")
        return node_value

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
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
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
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": self._localized(""),
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
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
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": self._localized(
                "This is NOT a valid UUID"
            ),
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
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
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": self._localized(valid_uuid),
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
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
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": self._localized("12345"),
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
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
                "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": None,
                "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
                "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
                "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
                "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": None,
                "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
            }
            populated_resourceid, resource_id = self.create_and_assert_resource(
                self.test_model_graph_id,
                tile_data,
                self.system_reference_nodegroup_id,
            )
            resource_ids.append(self._extract_resourceid_value(populated_resourceid))

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
