import os

from django.test import TransactionTestCase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.conf import settings
from arches.app.models import models
from arches.app.models.graph import Graph
from arches.app.models.resource import Resource
from arches.app.models.tile import Tile
from arches.app.utils.betterJSONSerializer import JSONDeserializer
from arches.app.utils.data_management.resource_graphs.importer import (
    import_graph as resource_graph_importer,
)


class BasePopulateResourceIDTestCase(TransactionTestCase):
    """
    Base test case for populate_resourceid function tests.
    Provides graph/function setup and helper methods shared by test modules.
    """

    serialized_rollback = True

    test_model_graph_id = "7a9d0a60-63f0-11f0-9f7e-460d1d596ee6"

    # Node IDs from test_model_populateid.json fixture
    resourceid_node_id = "7a9d162c-63f0-11f0-9f7e-460d1d596ee6"
    system_reference_nodegroup_id = "7a9d0cfe-63f0-11f0-9f7e-460d1d596ee6"
    description_node_id = "7a9d1924-63f0-11f0-9f7e-460d1d596ee6"
    description_nodegroup_id = "7a9d1226-63f0-11f0-9f7e-460d1d596ee6"
    language_code = "en"
    default_direction = "ltr"

    def setUp(self):
        super().setUp()

        source = os.path.join(
            "arches_he_sysref_funcs",
            "functions",
            "populate_resourceid.py",
        )

        call_command("fn", "register", source=source)

        admin = User.objects.get(username="admin")

        with open(
            os.path.join("tests/fixtures/resource_graphs/test_model_populateid.json"),
            "r",
        ) as f:
            archesfile = JSONDeserializer().deserialize(f)
        resource_graph_importer(archesfile["graph"])

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
        if resourceid_node is None:
            resourceid_node = self.resourceid_node_id

        graph = Graph.objects.get(pk=graph_id)
        resource = Resource(graph=graph)
        tile = Tile(data=tile_data, nodegroup_id=nodegroup_id)
        resource.tiles.append(tile)
        resource.save()

        saved_tiles = Tile.objects.filter(
            nodegroup_id=nodegroup_id, resourceinstance_id=resource.resourceinstanceid
        )

        if saved_tiles.exists():
            saved_tile = saved_tiles.first()
            populated_resourceid = saved_tile.data.get(resourceid_node)
            return populated_resourceid, str(resource.resourceinstanceid)

        return None, str(resource.resourceinstanceid)

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
