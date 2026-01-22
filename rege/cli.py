"""
RE:GE CLI - Command Line Interface for the symbolic operating system.

Commands:
- invoke: Execute a ritual invocation
- status: Show system status
- fragments: Manage fragments
- checkpoint: Manage checkpoints
- recover: System recovery
- repl: Interactive REPL mode
"""

import sys
import json
from typing import Optional

try:
    import click
except ImportError:
    print("Click library required. Install with: pip install click")
    sys.exit(1)

from rege.core.models import Fragment, RecoveryTrigger
from rege.parser.invocation_parser import InvocationParser
from rege.parser.validator import InvocationValidator
from rege.routing.dispatcher import Dispatcher, get_dispatcher
from rege.routing.patchbay import get_patchbay_queue
from rege.organs.registry import register_default_organs, get_organ_registry
from rege.protocols.fuse01 import get_fusion_protocol
from rege.protocols.recovery import get_recovery_protocol
from rege.protocols.enforcement import get_law_enforcer
from rege.persistence.archive import get_archive_manager
from rege.persistence.checkpoint import get_checkpoint_manager


def init_system() -> Dispatcher:
    """Initialize the RE:GE system."""
    # Register all default organs
    registry = register_default_organs()

    # Get dispatcher and register organ handlers
    dispatcher = get_dispatcher()

    for organ in registry:
        dispatcher.register_handler(organ.name, organ)

    return dispatcher


@click.group()
@click.version_option(version="1.0.0", prog_name="rege")
def cli():
    """RE:GE - Recursive Engine: Generative Entity

    A symbolic operating system for myth, identity, ritual, and recursive systems.
    """
    pass


@cli.command()
@click.argument("invocation", required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="Read invocation from file")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def invoke(invocation: Optional[str], file: Optional[str], json_output: bool):
    """Execute a ritual invocation.

    Example:
        rege invoke '::CALL_ORGAN MIRROR_CABINET
        ::WITH "I cant finish anything"
        ::MODE emotional_reflection
        ::DEPTH full spiral
        ::EXPECT fragment_map'
    """
    dispatcher = init_system()

    if file:
        with open(file, 'r') as f:
            invocation = f.read()

    if not invocation:
        click.echo("Error: No invocation provided. Use --help for usage.", err=True)
        return

    try:
        result = dispatcher.dispatch(invocation)

        if json_output:
            click.echo(json.dumps(result.to_dict(), indent=2, default=str))
        else:
            click.echo(f"\n::INVOCATION RESULT::")
            click.echo(f"  Organ: {result.organ}")
            click.echo(f"  Status: {result.status}")
            click.echo(f"  Output Type: {result.output_type}")
            click.echo(f"  Execution Time: {result.execution_time_ms}ms")

            if result.output:
                click.echo(f"\n::OUTPUT::")
                if isinstance(result.output, dict):
                    for key, value in result.output.items():
                        click.echo(f"  {key}: {value}")
                else:
                    click.echo(f"  {result.output}")

            if result.errors:
                click.echo(f"\n::ERRORS::")
                for error in result.errors:
                    click.echo(f"  - {error}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def status(json_output: bool):
    """Show system status."""
    init_system()

    queue = get_patchbay_queue()
    registry = get_organ_registry()
    fusion = get_fusion_protocol()
    recovery = get_recovery_protocol()
    enforcer = get_law_enforcer()

    status_data = {
        "queue": queue.get_queue_state(),
        "organs": {
            "registered": registry.list_names(),
            "count": len(registry),
        },
        "fusions": {
            "active": len(fusion.get_active_fusions()),
            "total": len(fusion.get_all_fusions()),
        },
        "recovery": {
            "halted": recovery.is_halted(),
            "checkpoints": len(recovery.get_all_checkpoints()),
        },
        "laws": {
            "active": len(enforcer.get_active_laws()),
            "total": len(enforcer.get_all_laws()),
        },
    }

    if json_output:
        click.echo(json.dumps(status_data, indent=2))
    else:
        click.echo("\n::RE:GE SYSTEM STATUS::")

        click.echo("\n[QUEUE]")
        q = status_data["queue"]
        click.echo(f"  Size: {q['total_size']}/{q['max_size']}")
        click.echo(f"  Processed: {q['total_processed']}")
        click.echo(f"  Collisions: {q['collision_count']}")
        click.echo(f"  Deadlocks: {q['deadlock_count']}")
        click.echo(f"  Maintenance Mode: {q['maintenance_mode']}")

        click.echo("\n[ORGANS]")
        click.echo(f"  Registered: {status_data['organs']['count']}")
        for organ in status_data['organs']['registered'][:5]:
            click.echo(f"    - {organ}")
        if len(status_data['organs']['registered']) > 5:
            click.echo(f"    ... and {len(status_data['organs']['registered']) - 5} more")

        click.echo("\n[FUSIONS]")
        click.echo(f"  Active: {status_data['fusions']['active']}")
        click.echo(f"  Total: {status_data['fusions']['total']}")

        click.echo("\n[RECOVERY]")
        click.echo(f"  System Halted: {status_data['recovery']['halted']}")
        click.echo(f"  Checkpoints: {status_data['recovery']['checkpoints']}")

        click.echo("\n[LAWS]")
        click.echo(f"  Active: {status_data['laws']['active']}")
        click.echo(f"  Total: {status_data['laws']['total']}")


@cli.group()
def fragments():
    """Manage fragments."""
    pass


@fragments.command("list")
@click.option("--organ", "-o", help="Filter by organ")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_fragments(organ: Optional[str], json_output: bool):
    """List fragments from organs."""
    init_system()
    registry = get_organ_registry()

    all_fragments = []

    # Collect fragments from organs that have them
    for organ_handler in registry:
        if hasattr(organ_handler, 'get_fragments') or hasattr(organ_handler, '_fragments'):
            if organ and organ.upper() != organ_handler.name:
                continue

            if hasattr(organ_handler, 'get_fragments'):
                frags = organ_handler.get_fragments()
            elif hasattr(organ_handler, '_fragments'):
                frags = list(organ_handler._fragments.values())
            else:
                continue

            for frag in frags:
                if hasattr(frag, 'to_dict'):
                    all_fragments.append({
                        "source": organ_handler.name,
                        **frag.to_dict()
                    })

    if json_output:
        click.echo(json.dumps(all_fragments, indent=2, default=str))
    else:
        if not all_fragments:
            click.echo("No fragments found.")
            return

        click.echo(f"\n::FRAGMENTS ({len(all_fragments)})::")
        for frag in all_fragments:
            click.echo(f"\n  [{frag.get('source', 'UNKNOWN')}] {frag.get('name', frag.get('id', 'unnamed'))}")
            click.echo(f"    Charge: {frag.get('charge', 'N/A')}")
            if frag.get('status'):
                click.echo(f"    Status: {frag['status']}")


@fragments.command("create")
@click.option("--name", "-n", required=True, help="Fragment name")
@click.option("--charge", "-c", type=int, default=50, help="Charge level (0-100)")
@click.option("--tags", "-t", multiple=True, help="Tags (can specify multiple)")
def create_fragment(name: str, charge: int, tags: tuple):
    """Create a new fragment."""
    fragment = Fragment(
        id="",  # Will be auto-generated
        name=name,
        charge=charge,
        tags=list(tags) if tags else [],
    )

    click.echo(f"\n::FRAGMENT CREATED::")
    click.echo(f"  ID: {fragment.id}")
    click.echo(f"  Name: {fragment.name}")
    click.echo(f"  Charge: {fragment.charge}")
    click.echo(f"  Tags: {', '.join(fragment.tags) if fragment.tags else 'none'}")


@cli.group()
def checkpoint():
    """Manage checkpoints."""
    pass


@checkpoint.command("create")
@click.argument("name")
def create_checkpoint(name: str):
    """Create a checkpoint."""
    init_system()

    registry = get_organ_registry()
    queue = get_patchbay_queue()

    # Gather system state
    system_state = {
        "metrics": queue.get_queue_state(),
        "organs": {organ.name: "active" for organ in registry},
        "pending": [],
        "errors": [],
    }

    manager = get_checkpoint_manager()
    snapshot = manager.create_checkpoint(name, system_state)

    click.echo(f"\n::CHECKPOINT CREATED::")
    click.echo(f"  ID: {snapshot.snapshot_id}")
    click.echo(f"  Name: {name}")
    click.echo(f"  Timestamp: {snapshot.timestamp.isoformat()}")


@checkpoint.command("list")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_checkpoints(json_output: bool):
    """List all checkpoints."""
    manager = get_checkpoint_manager()
    checkpoints = manager.list_checkpoints()

    if json_output:
        click.echo(json.dumps(checkpoints, indent=2))
    else:
        if not checkpoints:
            click.echo("No checkpoints found.")
            return

        click.echo(f"\n::CHECKPOINTS ({len(checkpoints)})::")
        for cp in checkpoints:
            click.echo(f"\n  {cp['snapshot_id']}")
            click.echo(f"    Name: {cp.get('name', 'unnamed')}")
            click.echo(f"    Timestamp: {cp['timestamp']}")
            click.echo(f"    Trigger: {cp.get('trigger', 'manual')}")


@checkpoint.command("restore")
@click.argument("snapshot_id")
@click.option("--confirm", is_flag=True, help="Confirm restoration")
def restore_checkpoint(snapshot_id: str, confirm: bool):
    """Restore from a checkpoint."""
    if not confirm:
        click.echo("Use --confirm to execute restoration.", err=True)
        return

    recovery = get_recovery_protocol()

    # Load checkpoint into recovery system
    manager = get_checkpoint_manager()
    try:
        snapshot = manager.load_checkpoint(snapshot_id)
    except Exception as e:
        click.echo(f"Error loading checkpoint: {e}", err=True)
        return

    # Add to recovery checkpoints
    recovery.checkpoints[snapshot_id] = snapshot

    # Execute rollback
    result = recovery.full_rollback(snapshot_id, confirm=True)

    click.echo(f"\n::RESTORE RESULT::")
    click.echo(f"  Status: {result.get('status', 'unknown')}")
    if result.get('organs_restored'):
        click.echo(f"  Organs Restored: {len(result['organs_restored'])}")


@cli.group()
def recover():
    """System recovery operations."""
    pass


@recover.command("emergency-stop")
@click.argument("reason")
def emergency_stop(reason: str):
    """Execute emergency system halt."""
    recovery = get_recovery_protocol()
    result = recovery.emergency_stop(reason)

    click.echo(f"\n::EMERGENCY STOP EXECUTED::")
    click.echo(f"  Status: {result['status']}")
    click.echo(f"  Reason: {result['reason']}")
    click.echo(f"  Snapshot: {result['panic_snapshot']}")
    click.echo("\nManual intervention required to resume.")


@recover.command("resume")
@click.option("--confirm", is_flag=True, help="Confirm resume")
def resume_system(confirm: bool):
    """Resume from emergency halt."""
    recovery = get_recovery_protocol()
    result = recovery.resume_from_halt(confirm=confirm)

    click.echo(f"\n::RESUME RESULT::")
    click.echo(f"  Status: {result['status']}")
    if result.get('message'):
        click.echo(f"  Message: {result['message']}")


@cli.command()
def repl():
    """Start interactive REPL mode."""
    dispatcher = init_system()
    parser = InvocationParser()
    validator = InvocationValidator()

    click.echo("\n::RE:GE RITUAL CONSOLE::")
    click.echo("Enter invocations or commands. Type 'help' for assistance, 'exit' to quit.\n")

    while True:
        try:
            # Read potentially multiline input
            lines = []
            prompt = "rege> " if not lines else "...   "

            while True:
                try:
                    line = click.prompt(prompt, default="", show_default=False)
                except click.Abort:
                    click.echo("\nExiting...")
                    return

                if not line and lines:
                    break
                if line.lower() in ('exit', 'quit', 'q'):
                    click.echo("::CONSOLE CLOSED::")
                    return
                if line.lower() == 'help':
                    click.echo("\n::HELP::")
                    click.echo("  Enter a ritual invocation starting with ::CALL_ORGAN")
                    click.echo("  Commands: help, status, exit")
                    click.echo("\n  Example:")
                    click.echo("    ::CALL_ORGAN HEART_OF_CANON")
                    click.echo("    ::WITH 'test memory'")
                    click.echo("    ::MODE mythic")
                    click.echo("    ::DEPTH standard")
                    click.echo("    ::EXPECT pulse_check")
                    click.echo("\n  Press Enter on empty line to execute.\n")
                    break
                if line.lower() == 'status':
                    queue = get_patchbay_queue()
                    state = queue.get_queue_state()
                    click.echo(f"\n  Queue: {state['total_size']}/{state['max_size']}")
                    click.echo(f"  Processed: {state['total_processed']}\n")
                    break

                lines.append(line)
                prompt = "...   "

            if not lines:
                continue

            invocation_text = "\n".join(lines)

            # Check if it's an invocation
            if parser.is_valid_syntax(invocation_text):
                try:
                    result = dispatcher.dispatch(invocation_text)
                    click.echo(f"\n  [{result.status}] {result.organ}")
                    if result.output:
                        if isinstance(result.output, dict):
                            for k, v in list(result.output.items())[:5]:
                                click.echo(f"    {k}: {v}")
                        else:
                            click.echo(f"    {result.output}")
                    click.echo()
                except Exception as e:
                    click.echo(f"\n  [ERROR] {e}\n")
            else:
                click.echo(f"\n  [UNKNOWN] Command not recognized. Type 'help' for assistance.\n")

        except KeyboardInterrupt:
            click.echo("\n\n::CONSOLE CLOSED::")
            return
        except EOFError:
            click.echo("\n::CONSOLE CLOSED::")
            return


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
