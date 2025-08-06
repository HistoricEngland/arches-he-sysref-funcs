from django.db import migrations, models
from django.utils.translation import gettext as _


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("models", "11499_add_editlog_resourceinstance_idx"),
    ]

    def add_functions(apps, schema_editor):
        Function = apps.get_model("models", "Function")

        Function.objects.update_or_create(
            functionid="39d627ae-6973-4ddb-8b62-1f0230e1e3f9",
            defaults={
                "name": "Generate Unique References",
                "functiontype": "node",
                "modulename": "generate_unique_references_function.py",
                "description": "Checks for Simple UID and Resource ID nodes populated and, if not populated, generates them",
                "defaultconfig": {
                    "simpleuid_node": "",
                    "nodegroup_nodes": [],
                    "resourceid_node": "",
                    "triggering_nodegroups": [],
                    "uniqueresource_nodegroup": "",
                },
                "classname": "GenerateUniqueReferences",
                "component": "views/components/functions/generate-unique-references-function",
            },
        )

    def remove_functions(apps, schema_editor):
        Function = apps.get_model("models", "Function")

        for fn in Function.objects.filter(
            pk__in=[
                "39d627ae-6973-4ddb-8b62-1f0230e1e3f9",
            ]
        ):
            fn.delete()

    operations = [
        migrations.RunPython(add_functions, remove_functions),
    ]
