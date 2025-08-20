from uuid import UUID
from arches.app.functions.base import BaseFunction
from arches.app.models import models
from arches.app.models.tile import Tile
from arches.app.models.system_settings import settings
from django.db import connection

import logging

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


class GenerateUniqueReferences(BaseFunction):

    def get(self):
        raise NotImplementedError

    def save(self, tile, request, context=None):
        self.logger = logging.getLogger(__name__)
        try:

            def create_simpleid_nextval_sequence(start=1):
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            CREATE SEQUENCE IF NOT EXISTS simpleid_nextval_id_seq MINVALUE 1 START %s;
                            """,
                            [start],
                        )
                except Exception as ex:
                    self.logger.error(f"Failed to create sequence: {ex}")
                    raise

            def get_current_sequence_number_from_database():
                funcs = models.FunctionXGraph.objects.filter(
                    function_id=details["functionid"]
                )
                nodeinfos = [
                    {
                        "simpleid": fn.config.get("simpleuid_node"),
                        "unique_ng_id": fn.config.get("uniqueresource_nodegroup"),
                    }
                    for fn in funcs
                    if "simpleuid_node" in fn.config
                    and "uniqueresource_nodegroup" in fn.config
                ]

                if not nodeinfos:
                    return None

                sql_node_str = ", ".join("t.tiledata ->> %s::text" for _ in nodeinfos)
                sql_nodegroups = tuple(ni["unique_ng_id"] for ni in nodeinfos)
                sql_params = [str(ni["simpleid"]) for ni in nodeinfos] + [
                    sql_nodegroups
                ]

                sql = f"""
                    SELECT results.simple_id::int
                    FROM (
                        SELECT
                            COALESCE({sql_node_str}, '0') AS simple_id
                        FROM tiles t
                        WHERE nodegroupid IN %s
                    ) AS results
                    ORDER BY results.simple_id::int DESC
                    LIMIT 1
                """

                with connection.cursor() as cursor:
                    cursor.execute(sql, sql_params)
                    result = cursor.fetchone()
                if result and result[0] is not None:
                    try:
                        return int(result[0])
                    except (ValueError, TypeError):
                        return None
                return None

            def get_next_simple_id():
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
                    exists = cursor.fetchone()[0]
                    if exists:
                        cursor.execute("SELECT nextval('simpleid_nextval_id_seq');")
                        return cursor.fetchone()[0]
                    else:
                        current_sequence_number = (
                            get_current_sequence_number_from_database()
                        )
                        next_database_value = (
                            current_sequence_number + 1
                            if current_sequence_number is not None
                            else 1
                        )
                        initial_sequence_number = max(
                            getattr(
                                settings, "PRIMARY_REFERENCE_NUMBER_INITIAL_SEED", 1
                            ),
                            next_database_value,
                        )
                        create_simpleid_nextval_sequence(start=initial_sequence_number)
                        return get_next_simple_id()

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
                    code=language_code
                ).default_direction

                def populate_simple_id(currentTile, simple_node_id):
                    try:
                        nextsimpleval = get_next_simple_id()
                        currentTile.data[simple_node_id] = nextsimpleval
                    except Exception as ex:
                        self.logger.error(f"Could not populate simple id: {ex}")
                        raise

                try:
                    # Process simpleid
                    current_simpleid_value = currentTile.data.get(simpleid_node, 0)
                    if (
                        not current_simpleid_value
                        or not str(current_simpleid_value).isdigit()
                    ):
                        populate_simple_id(currentTile, simpleid_node)
                        changes_made = True

                    # Process resourceid
                    resid_node_data = currentTile.data.get(resid_node) or {}
                    en_data = resid_node_data.get(language_code) or {}
                    resid_node_value = en_data.get("value")

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
                    tile, simpleNode, resourceIdNode, resourceIdValue
                )
                return

            # User saves another tile, and create system references if they do not exist
            previously_saved_tiles = Tile.objects.filter(
                nodegroup_id=refNodegroup, resourceinstance_id=resourceIdValue
            )

            # There should only be one tile in this nodegroup per resource instance
            if len(previously_saved_tiles) > 0:
                for p in previously_saved_tiles:
                    try:
                        if (
                            check_and_populate_uids(
                                p, simpleNode, resourceIdNode, resourceIdValue
                            )
                            == True
                        ):
                            p.save()
                    except Exception as ex:
                        self.logger.error(str(ex))
            else:
                newRefTile = Tile().get_blank_tile_from_nodegroup_id(
                    refNodegroup, resourceid=resourceIdValue, parenttile=None
                )
                if (
                    check_and_populate_uids(
                        newRefTile, simpleNode, resourceIdNode, resourceIdValue
                    )
                    == True
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
