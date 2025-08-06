# Generate Unique References Function

## Overview
The **Generate Unique References** function is a custom Arches function designed to ensure that every resource instance in a graph has a unique, sequentially generated Primary Reference Number (PRN) and a valid Resource ID (UUID). If these identifiers are missing or invalid, the function will generate and assign them automatically.

## How It Behaves
- When a resource is saved, the function checks if the required PRN and Resource ID nodes are populated.
- If the PRN is missing, zero, or not a valid integer, the function assigns the next available number from a PostgreSQL sequence.
- If the Resource ID is missing or not a valid UUID, the function uses the tile's `resourceinstance_id`.
- The function can be triggered by saving a tile in a specific nodegroup or by saving a tile elsewhere in the resource, depending on configuration.
- The function ensures that only one "System Reference Numbers" tile exists per resource instance and will create or update it as needed.

## Graph Shape Requirements
To use this function, your resource graph **must** include:

- **A nodegroup for System Reference Numbers**: This nodegroup should contain the nodes for the PRN and Resource ID.
- **A node for Primary Reference Number (PRN)**: This should be an integer or string node that will store the unique reference number.
- **A node for Resource ID**: This should be a string node, typically with the alias `resourceid`, that will store the UUID.
- The nodegroup and nodes must be present in the graph definition (see `test_model.json` and `second_test_model.json` for examples).

**Example nodegroup and nodes:**
- Nodegroup name: `System Reference Numbers`
- PRN node: e.g., `Primary Reference Number` (integer/string)
- Resource ID node: e.g., `ResourceID` (string, alias: `resourceid`)

## How to Configure
1. **Register the Function**
   - Use the Arches CLI or management command to register the function, pointing to the Python file (e.g., `generate_unique_references_function.py`).

2. **Configure the Function on the Graph**
   - In the Arches Designer or via JSON, add the function to your resource graph.
   - Set the following configuration options:
     - `simpleuid_node`: The nodeid for the PRN node.
     - `resourceid_node`: The nodeid for the Resource ID node.
     - `uniqueresource_nodegroup`: The nodegroupid for the System Reference Numbers nodegroup.
     - `triggering_nodegroups`: (Optional) List of nodegroupids that should trigger the function when saved.
     - `nodegroup_nodes`: (Optional) List of nodeids in the System Reference Numbers nodegroup.

3. **Database Sequence**
   - The function will automatically create a PostgreSQL sequence (`simpleid_nextval_id_seq`) if it does not exist.
   - The initial value for the sequence can be set via the Django setting `PRIMARY_REFERENCE_NUMBER_INITIAL_SEED` (see `test_settings.py`).
   - **Important:** If you are installing this function into an existing Arches instance, it is your responsibility to determine the correct next number for the sequence. Set `PRIMARY_REFERENCE_NUMBER_INITIAL_SEED` to the next available number that will not conflict with existing Primary Reference Numbers. Failing to do so may result in duplicate or conflicting reference numbers.

4. **Language Support**
   - The function supports multi-language fields for the Resource ID node, using the default language code and direction from Arches settings.

## Example Configuration (JSON)
```json
{
  "simpleuid_node": "<nodeid-for-prn>",
  "resourceid_node": "<nodeid-for-resourceid>",
  "uniqueresource_nodegroup": "<nodegroupid-for-system-reference-numbers>",
  "triggering_nodegroups": ["<other-nodegroupid>"]
}
```

## Notes
- The function is robust to missing or invalid values and will always ensure a valid PRN and Resource ID are present after save.
- The function is designed to be idempotent: running it multiple times will not create duplicate reference numbers.
- **Note:** When installing this function into a pre-populated Arches system, it will not retroactively generate primary reference numbers for existing resources. Only resources that are created or updated after the function is installed will receive new primary reference numbers automatically.
- For more details, see the code in `generate_unique_references_function.py` and the test graphs in `test_model.json` and `second_test_model.json`.
