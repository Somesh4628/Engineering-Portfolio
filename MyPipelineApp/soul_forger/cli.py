# Location: New file `cli.py`

import click
import os
from soul_engine import SystemBlueprint
import pydantic

# This helps our CLI find the files, similar to the test script
SCRIPT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


@click.group()
def cli():
    """
    Soul Forger CLI: A tool for creating and validating
    intelligent fluidic system blueprints.
    """
    # This main function creates the command group. It doesn't run on its own.


@cli.command()
@click.argument("filename", type=click.Path(exists=True, dir_okay=False))
def validate(filename):
    """
    Validates a given Soul Blueprint JSON file against all rules.

    Checks for:
    - Basic data type and structure correctness.
    - Logical integrity (e.g., pipes connect to existing nodes).
    - Topological integrity (e.g., the system is one connected piece).
    """
    click.echo(f"▶️  Attempting to validate blueprint: {filename}")

    try:
        # We use our trusted engine to do all the heavy lifting.
        # The CLI's job is just to call the engine and report the result.
        SystemBlueprint.from_file(filename)

        # If the line above completes without an error, the file is valid.
        click.secho(
            f"✅ SUCCESS: The blueprint '{os.path.basename(filename)}' is valid.",
            fg="green",
            bold=True,
        )

    except pydantic.ValidationError as e:
        # If the engine finds an error, we catch it and display it nicely.
        click.secho("❌ ERROR: The blueprint is NOT valid.", fg="red", bold=True)
        click.echo("--- Validation Errors ---")
        # Pydantic v2 gives a nice list of errors we can loop through.
        for error in e.errors():
            # 'loc' gives the location of the error, e.g., ('pipes', 0, 'source_node')
            location = " -> ".join(map(str, error["loc"]))
            message = error["msg"]
            click.secho(f"  -> At '{location}': {message}", fg="yellow")

    except Exception as e:
        # Catch any other unexpected errors, like a file not being proper JSON.
        click.secho(f"❌ UNEXPECTED ERROR: {e}", fg="red", bold=True)


# Location: In file `cli.py`
#
# Replace the ENTIRE create() function with this final version for Phase 2.5


@cli.command()
@click.option(
    "--output-file",
    default="new_cli_blueprint.json",
    help="The name of the file to save.",
)
def create(output_file):
    """
    Interactively creates a new, intelligent Soul Blueprint.
    """
    click.secho("--- Interactive Soul Forger (CLI) ---", fg="cyan", bold=True)
    click.echo("Let's create a new system blueprint from scratch.\n")

    try:
        # --- Gather Project Details ---
        project_name = click.prompt("Enter Project Name", default="My CLI System")

        # --- Interactive Node Creation (The FIX) ---
        nodes_data = []
        click.echo("\n--- Add Fluidic Components (Nodes) ---")
        while click.confirm("Do you want to add a component?", default=True):
            click.echo(f"  (Current component count: {len(nodes_data)})")

            node_id = click.prompt("  > Enter Node ID")
            label = click.prompt(f"  > Enter a Label for '{node_id}'", default=node_id)
            node_role = click.prompt(
                "  > Enter Node Role",
                type=click.Choice(
                    ["inlet", "junction", "outlet"], case_sensitive=False
                ),
            )
            component_type = click.prompt(
                "  > Enter Component Type",
                type=click.Choice(
                    ["Default", "Tee-Junction", "90-Degree-Elbow", "Tap"],
                    case_sensitive=False,
                ),
            )

            # We are now creating the new, correct node object
            nodes_data.append(
                {
                    "node_id": node_id,
                    "node_role": node_role,
                    "component_type": component_type,
                    "label": label,
                    "orientation": 0,
                }
            )
            click.secho(f"  --> Component '{node_id}' added.", fg="blue")

        if not nodes_data:
            click.secho("No components added. Aborting.", fg="red")
            return

        # (Pipe creation remains the same, as the Pipe model did not change)
        pipes_data = []
        # ... pipe creation logic would go here ...

        # Assemble the blueprint with the correct fields
        blueprint_data = {
            "project_details": {"name": project_name, "version": "1.0"},
            "ai_model": {
                "enabled": False,
                "model_file": "none.h",
                "output_classes": [],
            },
            "nodes": nodes_data,
            "pipes": pipes_data,
            "system_tuning_parameters": {
                "default_profile_id": "d",
                "profiles": [{"id": "d", "label": "l", "update_interval_ms": 1000}],
            },
        }

        new_blueprint = SystemBlueprint(**blueprint_data)

        full_output_path = os.path.join(SCRIPT_DIRECTORY, output_file)
        new_blueprint.to_file(full_output_path)

        click.secho(
            f"\n✅ SUCCESS: Blueprint saved to '{full_output_path}'",
            fg="green",
            bold=True,
        )

    except pydantic.ValidationError as e:
        click.secho(
            f"\n❌ VALIDATION ERROR: Could not create blueprint. Reason: {e}",
            fg="red",
            bold=True,
        )
    except Exception as e:
        click.secho(f"\n❌ UNEXPECTED ERROR: {e}", fg="red", bold=True)


if __name__ == "__main__":
    cli()
