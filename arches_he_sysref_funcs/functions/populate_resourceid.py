from uuid import UUID
from arches.app.functions.base import BaseFunction
from arches.app.models import models
from arches.app.models.system_settings import settings
from arches.app.models.tile import Tile
from django.db import connection
import logging
import json
from datetime import datetime

details = {
    "name": "Generate ResourceID",
    "type": "node",
    "description": "Checks for Resource ID nodes populated and, if not populated, generates it",
    "defaultconfig": {
        "resourceid_node": "",
        "uniqueresource_nodegroup": "",
        "triggering_nodegroups": [],
        "nodegroup_nodes": [],
    },
    "classname": "GenerateResourceID",
    "component": "views/components/functions/populate-resourceid",
    "functionid": "74f7bac7-85d2-405b-ab3e-b1b743ad2dd6",
}


class GenerateResourceID(BaseFunction):

    # def __init__(self,):
    #    super(GenerateResourceID, self).__init__()
    #    self.logger = logging.getLogger(__name__)

    def get(self):
        raise NotImplementedError

    def save(self, tile, request, context=None):
        self.logger = logging.getLogger(__name__)

        try:
            resourceIdValue = tile.resourceinstance_id
            resourceIdNode = self.config["resourceid_node"]
            refNodegroup = self.config["uniqueresource_nodegroup"]
            language_code = settings.LANGUAGE_CODE
            default_language_direction = models.Language.objects.get(
                code=language_code
            ).default_direction

            def checkAndPopulateUIDS(currentTile, resid_node, resourceidval):
                """
                Checks the input tile to see if it contains the correct resource id and simpleid
                values.  If not, populates these ids.
                """
                try:

                    def get_localized_value(node_value):
                        if isinstance(node_value, dict):
                            return (
                                node_value.get(language_code, {}).get("value")
                                if node_value.get(language_code)
                                else ""
                            )
                        return node_value

                    def set_localized_value(new_value):
                        currentTile.data[resid_node] = {
                            language_code: {
                                "value": str(new_value),
                                "direction": default_language_direction,
                            }
                        }

                    current_value = currentTile.data.get(resid_node)
                    candidate_value = get_localized_value(current_value)

                    if (
                        candidate_value is not None
                        and str(candidate_value).strip() != ""
                    ):
                        try:
                            UUID(str(candidate_value))
                            # Datatype 'string' values should be localized dictionaries.
                            if not isinstance(current_value, dict):
                                set_localized_value(candidate_value)
                        except:
                            set_localized_value(resourceidval)
                    else:
                        set_localized_value(resourceidval)

                    return True
                except (
                    KeyboardInterrupt,
                    SystemExit,
                    ImportError,
                    RuntimeError,
                    SyntaxError,
                ) as c:
                    self.logger.critical(str(c))
                    return False

                except (
                    AttributeError,
                    EOFError,
                    LookupError,
                    NameError,
                    MemoryError,
                    ValueError,
                    IOError,
                ) as e:
                    self.logger.error(str(e))
                    return False

                except Warning as w:
                    self.logger.warning(str(w))
                    return False

                except Exception as ex:
                    self.logger.error(str(ex))
                    return False

            # if the current tile context is a refNG (i.e. it has trigger its own save then don't trigger another save)
            if str(tile.nodegroup_id) == refNodegroup:
                checkAndPopulateUIDS(tile, resourceIdNode, resourceIdValue)
                return

            previously_saved_tiles = Tile.objects.filter(
                nodegroup_id=refNodegroup, resourceinstance_id=resourceIdValue
            )

            if len(previously_saved_tiles) > 0:
                for p in previously_saved_tiles:
                    try:
                        if (
                            checkAndPopulateUIDS(p, resourceIdNode, resourceIdValue)
                            == True
                        ):
                            p.save()
                        else:
                            self.logger.debug(
                                "Error.  Could not save Unique Identifiers tile."
                            )

                    except (
                        KeyboardInterrupt,
                        SystemExit,
                        ImportError,
                        RuntimeError,
                        SyntaxError,
                    ) as c:
                        self.logger.critical(str(c))

                    except (
                        AttributeError,
                        EOFError,
                        LookupError,
                        NameError,
                        MemoryError,
                        ValueError,
                        IOError,
                    ) as e:
                        self.logger.error(str(e))

                    except Warning as w:
                        self.logger.warning(str(w))

                    except Exception as ex:
                        self.logger.error(str(ex))
            else:
                newRefTile = Tile().get_blank_tile_from_nodegroup_id(
                    refNodegroup, resourceid=resourceIdValue, parenttile=None
                )
                if (
                    checkAndPopulateUIDS(newRefTile, resourceIdNode, resourceIdValue)
                    == True
                ):
                    newRefTile.save()
                else:
                    self.logger.debug("Error.  Could not save Unique Identifiers tile.")

            return

        except (
            KeyboardInterrupt,
            SystemExit,
            ImportError,
            RuntimeError,
            SyntaxError,
        ) as c:
            self.logger.critical(str(c))

        except (
            AttributeError,
            EOFError,
            LookupError,
            NameError,
            MemoryError,
            ValueError,
            IOError,
        ) as e:
            self.logger.error(str(e))

        except Warning as w:
            self.logger.warning(str(w))

        except Exception as ex:
            self.logger.error(str(ex))

    def delete(self, tile, request):
        raise NotImplementedError

    def on_import(self, tile):
        raise NotImplementedError

    def after_function_save(self, tile, request):
        raise NotImplementedError
