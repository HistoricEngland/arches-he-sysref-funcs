import os
import random
import concurrent.futures

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
from django.conf import settings


# These tests can be run from the command line via:
#     python manage.py test tests.generate_unique_references.generate_unique_references_tests --settings="tests.test_settings"
# or if using Docker:
#     python manage.py test tests.generate_unique_references.generate_unique_references_tests --settings="tests.test_settings_for_docker"


class TestGenerateUniqueReferencesFunction(TransactionTestCase):

    serialized_rollback = True

    test_model_graph_id = "7a9d0a60-63f0-11f0-9f7e-460d1d596ee6"
    second_test_model_graph_id = "41c228b2-b3ce-4174-9ed6-5632bded986c"

    initial_seed = getattr(settings, "PRIMARY_REFERENCE_NUMBER_INITIAL_SEED", 1)

    prn = 0

    def setUp(self):
        super().setUp()

        # Need to register function before the graphs are imported
        source = os.path.join(
            "arches_he_sysref_funcs",
            "functions",
            "generate_unique_references_function.py",
        )

        call_command("fn", "register", source=source)

        admin = User.objects.get(username="admin")

        # Import test_model graph
        with open(
            os.path.join("tests/fixtures/resource_graphs/test_model.json"), "r"
        ) as f:
            archesfile = JSONDeserializer().deserialize(f)
        resource_graph_importer(archesfile["graph"])
        graph = Graph.objects.get(graphid=self.test_model_graph_id)
        graph.publish(user=admin)

        # Import second_test_model graph
        with open(
            os.path.join("tests/fixtures/resource_graphs/second_test_model.json"), "r"
        ) as f:
            archesfile = JSONDeserializer().deserialize(f)
        resource_graph_importer(archesfile["graph"])
        graph = Graph.objects.get(graphid=self.second_test_model_graph_id)
        graph.publish(user=admin)

    def create_and_assert_resource(
        self, graph_id, tile_data, nodegroup_id, assert_prn=False
    ):
        graph = Graph.objects.get(pk=graph_id)
        resource = Resource(graph=graph)
        tile = Tile(data=tile_data, nodegroup_id=nodegroup_id)
        resource.tiles.append(tile)
        resource.save()

        resource_prn = resource.get_node_values("Primary Reference Number")[0]
        resource_uuid = (
            resource.get_node_values("ResourceID")[0].get("en", {}).get("value")
        )

        self.assertEqual(str(resource.resourceinstanceid), resource_uuid)

        if assert_prn:
            self.assertEqual(
                TestGenerateUniqueReferencesFunction.prn + self.initial_seed,
                resource_prn,
            )
            TestGenerateUniqueReferencesFunction.prn += 1

    # Test methods are named alphabetically, so the order of execution is predictable.
    # This is necessary so that the Primary Reference Number (PRN) is generated and tested sequentially.
    # The PRN is expected to be (0 + initial_seed) initially and incremented by 1 for each new resource created.

    # Has the function been registered?
    def test_01_function_exists(self):
        fn = models.Function.objects.all()
        self.assertTrue(fn.filter(name="Generate Unique References").exists())

    # Do the two test graphs exist?
    def test_02_graphs_exist(self):
        # Check if the test graphs exist
        graph1 = Graph.objects.filter(graphid=self.test_model_graph_id)
        graph2 = Graph.objects.filter(graphid=self.second_test_model_graph_id)
        self.assertTrue(graph1.exists())
        self.assertTrue(graph2.exists())

    # Model: Test Model; Save 'Description' node
    def test_03_create_new_test_model_with_description(self):
        description_node_id = "7a9d1924-63f0-11f0-9f7e-460d1d596ee6"
        description_nodegroup_id = "7a9d1226-63f0-11f0-9f7e-460d1d596ee6"
        tile_data = {
            description_node_id: {
                "en": {"value": "Test Resource with description", "direction": "ltr"}
            }
        }
        self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            description_nodegroup_id,
            assert_prn=True,
        )

    # Model: Test Model; Save 'Description' node; same operation as above - do we get a new Primary Reference Number (PRN)?
    def test_04_create_another_test_model_with_description(self):
        description_node_id = "7a9d1924-63f0-11f0-9f7e-460d1d596ee6"
        description_nodegroup_id = "7a9d1226-63f0-11f0-9f7e-460d1d596ee6"
        tile_data = {
            description_node_id: {
                "en": {
                    "value": "Another Test Resource with description",
                    "direction": "ltr",
                }
            }
        }
        self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            description_nodegroup_id,
            assert_prn=True,
        )

    # Model: Test Model; This simulates the user creating a new System Reference tile explicitly
    def test_05_create_test_model_without_description(self):
        tile_data = {
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": {
                "en": {"direction": "ltr", "value": ""}
            },
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": 0,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
        }
        nodegroup_id = "7a9d0cfe-63f0-11f0-9f7e-460d1d596ee6"
        self.create_and_assert_resource(
            self.test_model_graph_id,
            tile_data,
            nodegroup_id,
            self.prn + self.initial_seed,
        )

    # Model: Test Model; Same as above - do we get a new PRN?
    def test_06_create_another_test_model_without_description(self):
        tile_data = {
            "7a9d162c-63f0-11f0-9f7e-460d1d596ee6": {
                "en": {"direction": "ltr", "value": ""}
            },
            "7a9d150a-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1b90-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1c9e-63f0-11f0-9f7e-460d1d596ee6": None,
            "7a9d1e6a-63f0-11f0-9f7e-460d1d596ee6": 0,
            "7a9d211c-63f0-11f0-9f7e-460d1d596ee6": None,
        }
        nodegroup_id = "7a9d0cfe-63f0-11f0-9f7e-460d1d596ee6"
        self.create_and_assert_resource(
            self.test_model_graph_id, tile_data, nodegroup_id, assert_prn=True
        )

    # Model: Second Test Model; This simulates the user creating a new System Reference tile explicitly
    def test_07_create_second_test_model_without_description(self):
        tile_data = {
            "b4d8a7a4-624a-11f0-8f24-96a8a23bc0be": {
                "en": {"direction": "ltr", "value": ""}
            },
            "eba9e4aa-624a-11f0-8f24-96a8a23bc0be": None,
            "61f674ee-624a-11f0-8f24-96a8a23bc0be": None,
            "fd70c92a-6249-11f0-8f24-96a8a23bc0be": None,
            "2a060860-624a-11f0-8f24-96a8a23bc0be": 0,
            "d19f9384-624a-11f0-8f24-96a8a23bc0be": None,
        }
        nodegroup_id = "cb07f788-6249-11f0-8f24-96a8a23bc0be"
        self.create_and_assert_resource(
            self.second_test_model_graph_id, tile_data, nodegroup_id, assert_prn=True
        )

    # Model: Second Test Model; Save 'Description' node
    def test_08_create_another_second_test_model_with_description(self):
        description_node_id = "25ec1592-63c8-11f0-b057-62c8cdfa6e19"
        description_nodegroup_id = "6799975e-63c7-11f0-9d19-62c8cdfa6e19"
        tile_data = {
            description_node_id: {
                "en": {
                    "value": "Second Test Resource with description",
                    "direction": "ltr",
                }
            }
        }
        self.create_and_assert_resource(
            self.second_test_model_graph_id,
            tile_data,
            description_nodegroup_id,
            self.prn + self.initial_seed,
        )

    def test_09_invalid_resourceid(self):
        # PRN is set to an arbitrary value since we are not checking it here.
        # This prevents the PRN from being incremented by the function.
        tile_data = {
            "b4d8a7a4-624a-11f0-8f24-96a8a23bc0be": {
                "en": {"direction": "ltr", "value": "This is NOT a valid resource UUID"}
            },
            "eba9e4aa-624a-11f0-8f24-96a8a23bc0be": None,
            "61f674ee-624a-11f0-8f24-96a8a23bc0be": None,
            "fd70c92a-6249-11f0-8f24-96a8a23bc0be": None,
            # PRN is set, so the function will not increment it
            "2a060860-624a-11f0-8f24-96a8a23bc0be": 1,
            "d19f9384-624a-11f0-8f24-96a8a23bc0be": None,
        }
        nodegroup_id = "cb07f788-6249-11f0-8f24-96a8a23bc0be"
        # Only check the resourceid is set correctly, even though it is invalid.
        # Not checking the expected PRN. As a result, PRN will not be incremented - assert_prn is set to False
        self.create_and_assert_resource(
            self.second_test_model_graph_id, tile_data, nodegroup_id, assert_prn=False
        )

    def test_10_invalid_prn_float(self):
        tile_data = {
            "b4d8a7a4-624a-11f0-8f24-96a8a23bc0be": {
                "en": {"direction": "ltr", "value": ""}
            },
            "eba9e4aa-624a-11f0-8f24-96a8a23bc0be": None,
            "61f674ee-624a-11f0-8f24-96a8a23bc0be": None,
            "fd70c92a-6249-11f0-8f24-96a8a23bc0be": None,
            # Can't specify a string, as the _pre_save function will fail
            "2a060860-624a-11f0-8f24-96a8a23bc0be": 3.1415927,
            "d19f9384-624a-11f0-8f24-96a8a23bc0be": None,
        }
        nodegroup_id = "cb07f788-6249-11f0-8f24-96a8a23bc0be"
        # PRN is set to an invalid value, and will be set to the next available number.
        self.create_and_assert_resource(
            self.second_test_model_graph_id, tile_data, nodegroup_id, assert_prn=True
        )

    def test_11_invalid_prn_none(self):
        tile_data = {
            "b4d8a7a4-624a-11f0-8f24-96a8a23bc0be": {
                "en": {"direction": "ltr", "value": ""}
            },
            "eba9e4aa-624a-11f0-8f24-96a8a23bc0be": None,
            "61f674ee-624a-11f0-8f24-96a8a23bc0be": None,
            "fd70c92a-6249-11f0-8f24-96a8a23bc0be": None,
            "2a060860-624a-11f0-8f24-96a8a23bc0be": None,  # None is invalid
            "d19f9384-624a-11f0-8f24-96a8a23bc0be": None,
        }
        nodegroup_id = "cb07f788-6249-11f0-8f24-96a8a23bc0be"
        # PRN is set to None, and will be set to the next available number.
        self.create_and_assert_resource(
            self.second_test_model_graph_id, tile_data, nodegroup_id, assert_prn=True
        )

    def test_12_invalid_resourceid_and_invalid_prn(self):
        # PRN is set to an arbitrary value since we are not checking it here.
        # This prevents the PRN from being incremented by the function.
        tile_data = {
            "b4d8a7a4-624a-11f0-8f24-96a8a23bc0be": {
                "en": {"direction": "ltr", "value": "This is NOT a valid resource UUID"}
            },
            "eba9e4aa-624a-11f0-8f24-96a8a23bc0be": None,
            "61f674ee-624a-11f0-8f24-96a8a23bc0be": None,
            "fd70c92a-6249-11f0-8f24-96a8a23bc0be": None,
            "2a060860-624a-11f0-8f24-96a8a23bc0be": 3.1415927,
            "d19f9384-624a-11f0-8f24-96a8a23bc0be": None,
        }
        nodegroup_id = "cb07f788-6249-11f0-8f24-96a8a23bc0be"
        # Both resourceid and PRN are invalid. Function should increment the PRN and set the resourceid.
        self.create_and_assert_resource(
            self.second_test_model_graph_id, tile_data, nodegroup_id, assert_prn=True
        )

    # Run all tests in a randomized order multiple times, incrementing the PRN each time

    def test_13_run_randomized_tests_multiple_times(self):
        test_methods = [
            self.test_03_create_new_test_model_with_description,
            self.test_04_create_another_test_model_with_description,
            self.test_05_create_test_model_without_description,
            self.test_06_create_another_test_model_without_description,
            self.test_07_create_second_test_model_without_description,
            self.test_08_create_another_second_test_model_with_description,
            self.test_09_invalid_resourceid,
            self.test_10_invalid_prn_float,
            self.test_11_invalid_prn_none,
            self.test_12_invalid_resourceid_and_invalid_prn,
        ]
        for i in range(50):
            random.shuffle(test_methods)
            for j, test in enumerate(test_methods, start=1):
                test()
