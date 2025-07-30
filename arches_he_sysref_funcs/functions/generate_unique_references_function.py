from uuid import UUID
from arches.app.functions.base import BaseFunction
from arches.app.models import models
from arches.app.models.tile import Tile
from arches.app.models.system_settings import settings
from django.db.models.functions import Cast
from django.db.models import Max, IntegerField
from django.db import connection, transaction

# from django.contrib.postgres.fields.jsonb import KeyTextTransform
import logging
import json
from datetime import datetime

details = {
    "name": "Generate Unique References",
    "type": "node",
    "description": "Checks for Simple UID and Resource ID nodes populated and, if not populated, generates them",
    "defaultconfig": {
        "simpleuid_node": "",
        "resourceid_node": "",
        "uniqueresource_nodegroup": "",
        "triggering_nodegroups": [],
        "nodegroup_nodes": [],
    },
    "classname": "GenerateUniqueReferences",
    "component": "views/components/functions/generate-unique-references-function",
    "functionid": "39d627ae-6973-4ddb-8b62-1f0230e1e3f9",
}


# Singleton functions need to be defined outside of the class to ensure they are not redefined on each instantiation
def simpleid_nextval_sequence_exists_singleton():
    if not hasattr(simpleid_nextval_sequence_exists_singleton, "exists"):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.sequences
                    WHERE sequence_schema = 'public'
                    AND sequence_name = 'simpleid_nextval_id_seq'
                );
                """
            )
            [result] = cursor.fetchone()
        simpleid_nextval_sequence_exists_singleton.exists = bool(result)
    return simpleid_nextval_sequence_exists_singleton.exists


class GenerateUniqueReferences(BaseFunction):

    def get(self):
        raise NotImplementedError

    def save(self, tile, request, context=None):
        self.logger = logging.getLogger(__name__)
        try:

            def create_simpleid_nextval_sequence(start=1):
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """CREATE SEQUENCE IF NOT EXISTS simpleid_nextval_id_seq MINVALUE 1 START %s;""",
                            [start]
                        )
                simpleid_nextval_sequence_exists_singleton.exists = True

            def get_next_simple_id():
                if not simpleid_nextval_sequence_exists_singleton():
                    initial_sequence_number = getattr(
                        settings, "PRIMARY_REFERENCE_NUMBER_INITIAL_SEED", 1)
                    create_simpleid_nextval_sequence(
                        start=initial_sequence_number)
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT nextval('simpleid_nextval_id_seq');"
                    )
                    [result] = cursor.fetchone()
                return int(result)

            resourceIdValue = tile.resourceinstance_id
            simpleNode = self.config["simpleuid_node"]
            resourceIdNode = self.config["resourceid_node"]
            refNodegroup = self.config["uniqueresource_nodegroup"]

            def check_and_populate_uids(
                currentTile, simpleid_node, resid_node, resourceidval
            ):

                changes_made = False
                language_code = settings.LANGUAGE_CODE
                default_language_direction = models.Language.objects.get(
                    code=language_code).default_direction

                def populate_simple_id(currentTile, simple_node_id):
                    nextsimpleval = get_next_simple_id()
                    currentTile.data[simple_node_id] = nextsimpleval

                try:
                    # Process simpleid
                    current_simpleid_value = currentTile.data.get(
                        simpleid_node, 0)
                    if not current_simpleid_value or not str(current_simpleid_value).isdigit():
                        populate_simple_id(currentTile, simpleid_node)
                        changes_made = True

                    # Process resourceid
                    resid_node_data = currentTile.data.get(resid_node) or {}
                    en_data = resid_node_data.get(language_code) or {}
                    resid_node_value = en_data.get('value')

                    update_resid_node_tile = False
                    if resid_node_value:
                        try:
                            UUID(resid_node_value)
                            pass
                        except:
                            update_resid_node_tile = True
                    else:
                        update_resid_node_tile = True

                    if update_resid_node_tile:

                        changes_made = True

                        currentTile.data[resid_node] = {
                            language_code: {
                                "value": str(resourceidval),
                                "direction": default_language_direction,
                            }
                        }

                    return changes_made

                except Exception as ex:
                    self.logger.error(str(ex))
                    return False

            # User is creating a new System Reference tile explicitly
            if str(tile.nodegroup_id) == refNodegroup:
                check_and_populate_uids(
                    tile,
                    simpleNode,
                    resourceIdNode,
                    resourceIdValue
                )
                return

            # User saves another tile, and create system references if they do not exist
            previously_saved_tiles = Tile.objects.filter(
                nodegroup_id=refNodegroup,
                resourceinstance_id=resourceIdValue
            )

            # There should only be one tile in this nodegroup per resource instance
            if len(previously_saved_tiles) > 0:
                for p in previously_saved_tiles:
                    try:
                        if (
                            check_and_populate_uids(
                                p,
                                simpleNode,
                                resourceIdNode,
                                resourceIdValue
                            ) == True
                        ):
                            p.save()
                    except Exception as ex:
                        self.logger.error(str(ex))
            else:
                newRefTile = Tile().get_blank_tile_from_nodegroup_id(
                    refNodegroup,
                    resourceid=resourceIdValue,
                    parenttile=None
                )
                if (
                    check_and_populate_uids(
                        newRefTile,
                        simpleNode,
                        resourceIdNode,
                        resourceIdValue
                    ) == True
                ):
                    newRefTile.save()

            return

        except Exception as ex:
            self.logger.error(str(ex))

    def delete(self, tile, request):
        raise NotImplementedError

    def on_import(self, tile):
        raise NotImplementedError

    def after_function_save(self, tile, request):
        raise NotImplementedError
