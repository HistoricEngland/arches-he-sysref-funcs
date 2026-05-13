from django.db import migrations, models
from django.utils.translation import gettext as _


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        (
            "arches_he_sysref_funcs",
            "90092_initial_generate_unique_refererences_function",
        ),
    ]

    def add_functions(apps, schema_editor):
        Function = apps.get_model("models", "Function")

        if not Function.objects.filter(
            pk="74f7bac7-85d2-405b-ab3e-b1b743ad2dd6"
        ).exists():

            Function.objects.update_or_create(
                functionid="74f7bac7-85d2-405b-ab3e-b1b743ad2dd6",
                defaults={
                    "name": "Generate ResourceID",
                    "functiontype": "node",
                    "modulename": "populate_resourceid.py",
                    "description": "Checks for Resource ID nodes populated and, if not populated, generates it",
                    "defaultconfig": {
                        "simpleuid_node": "",
                        "nodegroup_nodes": [],
                        "resourceid_node": "",
                        "triggering_nodegroups": [],
                        "uniqueresource_nodegroup": "",
                    },
                    "classname": "GenerateResourceID",
                    "component": "views/components/functions/populate-resourceid",
                },
            )

    def remove_functions(apps, schema_editor):
        Function = apps.get_model("models", "Function")

        for fn in Function.objects.filter(
            pk__in=[
                "74f7bac7-85d2-405b-ab3e-b1b743ad2dd6",
            ]
        ):
            fn.delete()

    operations = [
        migrations.RunPython(add_functions, remove_functions),
    ]
