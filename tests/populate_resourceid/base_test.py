import os
import uuid

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

    test_model_graph_id = "2828122c-58f8-11f1-a45a-02e06202dcc7"

    # Node IDs from test_model_populateid.json fixture
    resourceid_node_id = "282839be-58f8-11f1-a45a-02e06202dcc7"
    system_reference_nodegroup_id = "2828170e-58f8-11f1-a45a-02e06202dcc7"
    description_node_id = "282830b8-58f8-11f1-a45a-02e06202dcc7"
    description_nodegroup_id = "28282280-58f8-11f1-a45a-02e06202dcc7"
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
            os.path.join(
                "tests/fixtures/pkg/graphs/resource_models/test_model_populateid.json"
            ),
            "r",
        ) as f:
            archesfile = JSONDeserializer().deserialize(f)
        resource_graph_importer(archesfile["graph"])

        registered_function = models.Function.objects.get(name="Generate ResourceID")
        models.FunctionXGraph.objects.get_or_create(
            graph_id=self.test_model_graph_id,
            function_id=registered_function.functionid,
        )

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
            return populated_resourceid, (
                str(resource.resourceinstanceid)
                if resource.resourceinstanceid is not None
                else None
                )
        
        else:
            return None, (
                str(resource.resourceinstanceid)
                if resource.resourceinstanceid is not None
                else None
            )

    def _localized(self, value):
        return {
            self.language_code: {
                "value": value,
                "direction": self.default_direction,
            }
        }

    def _extract_resourceid_value(self, node_value):
        if isinstance(node_value, dict):
            node_value = node_value.get(self.language_code, {}).get("value")

        if node_value is None:
            return None

        node_value = str(node_value)

        try:
            uuid.UUID(node_value)
        except (ValueError, TypeError, AttributeError):
            return None

        return node_value
