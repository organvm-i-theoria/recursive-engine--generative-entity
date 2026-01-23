"""
RE:GE CLI - Command Line Interface for the symbolic operating system.

Commands:
- invoke: Execute a ritual invocation
- status: Show system status
- fragments: Manage fragments
- checkpoint: Manage checkpoints
- recover: System recovery
- repl: Interactive REPL mode
- laws: Manage system laws
- fusion: Manage fragment fusions
- depth: View depth tracking
- queue: Manage the Soul Patchbay queue
- batch: Execute multiple invocations from file
"""

import sys
import json
from typing import Optional, List

try:
    import click
except ImportError:
    print("Click library required. Install with: pip install click")
    sys.exit(1)

from rege.core.models import Fragment, RecoveryTrigger
from rege.core.constants import DepthLimits
from rege.parser.invocation_parser import InvocationParser
from rege.parser.validator import InvocationValidator
from rege.routing.dispatcher import Dispatcher, get_dispatcher
from rege.routing.patchbay import get_patchbay_queue
from rege.routing.depth_tracker import get_depth_tracker
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
    """Start interactive REPL mode with enhanced commands."""
    dispatcher = init_system()
    parser = InvocationParser()
    validator = InvocationValidator()
    registry = get_organ_registry()

    # Session state
    session = {
        "last_result": None,
        "history": [],
        "vars": {
            "CHARGE": 50,  # Default charge for invocations
            "DEPTH": "standard",  # Default depth level
        },
    }

    click.echo("\n::RE:GE RITUAL CONSOLE::")
    click.echo("Enter invocations or commands. Type ':help' for assistance, 'exit' to quit.\n")

    def show_help():
        """Show REPL help."""
        click.echo("\n::HELP::")
        click.echo("  INVOCATIONS:")
        click.echo("    Enter a ritual invocation starting with ::CALL_ORGAN")
        click.echo("    Press Enter on empty line to execute.\n")
        click.echo("  COMMANDS (prefix with ':'):")
        click.echo("    :help          Show this help")
        click.echo("    :status        Show queue status")
        click.echo("    :organs        List all organs")
        click.echo("    :modes <organ> List modes for an organ")
        click.echo("    :last          Show last result")
        click.echo("    :vars          Show session variables")
        click.echo("    :set <var> <val> Set a session variable")
        click.echo("    :history       Show command history")
        click.echo("    :clear         Clear screen")
        click.echo("    :load <file>   Execute invocations from file")
        click.echo("    :export <file> Export session results to file")
        click.echo("    exit, quit, q  Exit the REPL\n")
        click.echo("  EXAMPLE:")
        click.echo("    ::CALL_ORGAN HEART_OF_CANON")
        click.echo("    ::WITH 'test memory'")
        click.echo("    ::MODE mythic")
        click.echo("    ::DEPTH standard")
        click.echo("    ::EXPECT pulse_check\n")
        click.echo("  SESSION VARIABLES:")
        click.echo("    $CHARGE - Default charge level (0-100)")
        click.echo("    $DEPTH  - Default depth (light, standard, full spiral)\n")

    def handle_command(cmd: str) -> bool:
        """Handle REPL commands. Returns True if command was handled."""
        parts = cmd.split(maxsplit=2)
        command = parts[0].lower()

        if command in (':help', 'help'):
            show_help()
            return True

        elif command in (':status', 'status'):
            queue = get_patchbay_queue()
            state = queue.get_queue_state()
            click.echo(f"\n  Queue: {state['total_size']}/{state['max_size']}")
            click.echo(f"  Processed: {state['total_processed']}")
            click.echo(f"  Collisions: {state['collision_count']}")
            click.echo(f"  Maintenance: {state['maintenance_mode']}\n")
            return True

        elif command == ':organs':
            click.echo("\n  ::AVAILABLE ORGANS::")
            for organ in registry:
                click.echo(f"    - {organ.name}")
            click.echo()
            return True

        elif command == ':modes':
            if len(parts) < 2:
                click.echo("  Usage: :modes <organ_name>")
                return True
            organ_name = parts[1].upper()
            for organ in registry:
                if organ.name == organ_name:
                    modes = organ.get_valid_modes()
                    click.echo(f"\n  ::MODES FOR {organ_name}::")
                    for mode in modes:
                        click.echo(f"    - {mode}")
                    click.echo()
                    return True
            click.echo(f"  Organ not found: {organ_name}")
            return True

        elif command == ':last':
            if session["last_result"]:
                click.echo("\n  ::LAST RESULT::")
                result = session["last_result"]
                click.echo(f"    Organ: {result.organ}")
                click.echo(f"    Status: {result.status}")
                if result.output:
                    if isinstance(result.output, dict):
                        for k, v in list(result.output.items())[:10]:
                            click.echo(f"    {k}: {v}")
                    else:
                        click.echo(f"    {result.output}")
                click.echo()
            else:
                click.echo("  No previous result.")
            return True

        elif command == ':vars':
            click.echo("\n  ::SESSION VARIABLES::")
            for name, value in session["vars"].items():
                click.echo(f"    ${name} = {value}")
            click.echo()
            return True

        elif command == ':set':
            if len(parts) < 3:
                click.echo("  Usage: :set <variable> <value>")
                return True
            var_name = parts[1].upper().replace("$", "")
            value = parts[2]
            if var_name == "CHARGE":
                try:
                    session["vars"]["CHARGE"] = int(value)
                    click.echo(f"  Set $CHARGE = {value}")
                except ValueError:
                    click.echo("  Invalid charge value (must be integer 0-100)")
            elif var_name == "DEPTH":
                if value.lower() in ("light", "standard", "full spiral"):
                    session["vars"]["DEPTH"] = value.lower()
                    click.echo(f"  Set $DEPTH = {value}")
                else:
                    click.echo("  Invalid depth (use: light, standard, full spiral)")
            else:
                session["vars"][var_name] = value
                click.echo(f"  Set ${var_name} = {value}")
            return True

        elif command == ':history':
            if session["history"]:
                click.echo("\n  ::COMMAND HISTORY::")
                for i, hist in enumerate(session["history"][-20:], 1):
                    preview = hist[:50] + "..." if len(hist) > 50 else hist
                    preview = preview.replace("\n", " ")
                    click.echo(f"    {i}. {preview}")
                click.echo()
            else:
                click.echo("  No history.")
            return True

        elif command == ':clear':
            click.clear()
            click.echo("\n::RE:GE RITUAL CONSOLE::\n")
            return True

        elif command == ':load':
            if len(parts) < 2:
                click.echo("  Usage: :load <filename>")
                return True
            filename = parts[1]
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                # Execute each invocation (separated by blank lines)
                invocations = [inv.strip() for inv in content.split('\n\n') if inv.strip() and not inv.strip().startswith('#')]
                click.echo(f"  Loading {len(invocations)} invocations from {filename}...")
                for inv in invocations:
                    if parser.is_valid_syntax(inv):
                        try:
                            result = dispatcher.dispatch(inv)
                            session["last_result"] = result
                            click.echo(f"    [{result.status}] {result.organ}")
                        except Exception as e:
                            click.echo(f"    [ERROR] {e}")
            except FileNotFoundError:
                click.echo(f"  File not found: {filename}")
            except Exception as e:
                click.echo(f"  Error loading file: {e}")
            return True

        elif command == ':export':
            if len(parts) < 2:
                click.echo("  Usage: :export <filename>")
                return True
            filename = parts[1]
            try:
                export_data = {
                    "session_vars": session["vars"],
                    "history": session["history"],
                    "last_result": session["last_result"].to_dict() if session["last_result"] else None,
                }
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
                click.echo(f"  Exported session to {filename}")
            except Exception as e:
                click.echo(f"  Error exporting: {e}")
            return True

        return False

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

                # Check for exit commands
                if line.lower() in ('exit', 'quit', 'q'):
                    click.echo("::CONSOLE CLOSED::")
                    return

                # Check for REPL commands (start with :)
                if line.startswith(':') or (not lines and line.lower() in ('help', 'status')):
                    if handle_command(line):
                        break

                # Empty line with content executes
                if not line and lines:
                    break

                # Skip empty line without content
                if not line:
                    break

                lines.append(line)
                prompt = "...   "

            if not lines:
                continue

            invocation_text = "\n".join(lines)

            # Add to history
            session["history"].append(invocation_text)

            # Check if it's an invocation
            if parser.is_valid_syntax(invocation_text):
                try:
                    result = dispatcher.dispatch(invocation_text)
                    session["last_result"] = result
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
                # Try as a command without colon prefix
                if not handle_command(invocation_text):
                    click.echo(f"\n  [UNKNOWN] Command not recognized. Type ':help' for assistance.\n")

        except KeyboardInterrupt:
            click.echo("\n\n::CONSOLE CLOSED::")
            return
        except EOFError:
            click.echo("\n::CONSOLE CLOSED::")
            return


# =============================================================================
# Laws Command Group
# =============================================================================

@cli.group()
def laws():
    """Manage system laws."""
    pass


@laws.command("list")
@click.option("--active-only", "-a", is_flag=True, help="Show only active laws")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_laws(active_only: bool, json_output: bool):
    """List all laws with their status."""
    init_system()
    enforcer = get_law_enforcer()

    if active_only:
        laws_list = enforcer.get_active_laws()
    else:
        laws_list = enforcer.get_all_laws()

    if json_output:
        click.echo(json.dumps(laws_list, indent=2, default=str))
    else:
        if not laws_list:
            click.echo("No laws found.")
            return

        click.echo(f"\n::LAWS ({len(laws_list)})::")
        for law in laws_list:
            status = "ACTIVE" if law.get("active", True) else "INACTIVE"
            click.echo(f"\n  [{status}] {law.get('id', 'UNKNOWN')}")
            click.echo(f"    Name: {law.get('name', 'unnamed')}")
            if law.get('description'):
                desc = law['description'][:80] + "..." if len(law.get('description', '')) > 80 else law.get('description', '')
                click.echo(f"    Description: {desc}")


@laws.command("show")
@click.argument("law_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def show_law(law_id: str, json_output: bool):
    """Show details of a specific law."""
    init_system()
    enforcer = get_law_enforcer()

    law = enforcer.get_law(law_id)
    if not law:
        click.echo(f"Law not found: {law_id}", err=True)
        return

    if json_output:
        click.echo(json.dumps(law, indent=2, default=str))
    else:
        click.echo(f"\n::LAW DETAILS::")
        click.echo(f"  ID: {law.get('id', law_id)}")
        click.echo(f"  Name: {law.get('name', 'unnamed')}")
        click.echo(f"  Active: {law.get('active', True)}")
        if law.get('description'):
            click.echo(f"  Description: {law['description']}")
        if law.get('created_at'):
            click.echo(f"  Created: {law['created_at']}")


@laws.command("activate")
@click.argument("law_id")
def activate_law(law_id: str):
    """Activate a law."""
    init_system()
    enforcer = get_law_enforcer()

    result = enforcer.activate_law(law_id)
    if result.get("status") == "activated":
        click.echo(f"\n::LAW ACTIVATED::")
        click.echo(f"  Law: {law_id}")
    else:
        click.echo(f"Failed to activate law: {result.get('reason', 'unknown')}", err=True)


@laws.command("deactivate")
@click.argument("law_id")
def deactivate_law(law_id: str):
    """Deactivate a law."""
    init_system()
    enforcer = get_law_enforcer()

    result = enforcer.deactivate_law(law_id)
    if result.get("status") == "deactivated":
        click.echo(f"\n::LAW DEACTIVATED::")
        click.echo(f"  Law: {law_id}")
    else:
        click.echo(f"Failed to deactivate law: {result.get('reason', 'unknown')}", err=True)


@laws.command("violations")
@click.option("--limit", "-l", type=int, default=20, help="Maximum violations to show")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_violations(limit: int, json_output: bool):
    """Show law violation log."""
    init_system()
    enforcer = get_law_enforcer()

    violations = enforcer.get_violation_log()[:limit]

    if json_output:
        click.echo(json.dumps(violations, indent=2, default=str))
    else:
        if not violations:
            click.echo("No violations recorded.")
            return

        click.echo(f"\n::VIOLATIONS ({len(violations)})::")
        for v in violations:
            click.echo(f"\n  [{v.get('timestamp', 'unknown')}] {v.get('law_id', 'UNKNOWN')}")
            click.echo(f"    Operation: {v.get('operation', 'unknown')}")
            if v.get('message'):
                click.echo(f"    Message: {v['message']}")


# =============================================================================
# Fusion Command Group
# =============================================================================

@cli.group()
def fusion():
    """Manage fragment fusions."""
    pass


@fusion.command("list")
@click.option("--active-only", "-a", is_flag=True, help="Show only active fusions")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_fusions(active_only: bool, json_output: bool):
    """List all fusions."""
    init_system()
    protocol = get_fusion_protocol()

    if active_only:
        fusions = protocol.get_active_fusions()
    else:
        fusions = protocol.get_all_fusions()

    if json_output:
        fusions_data = [f.to_dict() if hasattr(f, 'to_dict') else f for f in fusions]
        click.echo(json.dumps(fusions_data, indent=2, default=str))
    else:
        if not fusions:
            click.echo("No fusions found.")
            return

        click.echo(f"\n::FUSIONS ({len(fusions)})::")
        for f in fusions:
            fused_id = f.fused_id if hasattr(f, 'fused_id') else f.get('fused_id', 'UNKNOWN')
            status = f.status if hasattr(f, 'status') else f.get('status', 'unknown')
            charge = f.charge if hasattr(f, 'charge') else f.get('charge', 'N/A')
            click.echo(f"\n  [{status}] {fused_id}")
            click.echo(f"    Charge: {charge}")
            if hasattr(f, 'source_fragments'):
                click.echo(f"    Sources: {len(f.source_fragments)} fragments")


@fusion.command("show")
@click.argument("fusion_id")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def show_fusion(fusion_id: str, json_output: bool):
    """Show details of a specific fusion."""
    init_system()
    protocol = get_fusion_protocol()

    fused = protocol.get_fusion(fusion_id)
    if not fused:
        click.echo(f"Fusion not found: {fusion_id}", err=True)
        return

    if json_output:
        data = fused.to_dict() if hasattr(fused, 'to_dict') else fused
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(f"\n::FUSION DETAILS::")
        click.echo(f"  ID: {fused.fused_id if hasattr(fused, 'fused_id') else fusion_id}")
        click.echo(f"  Status: {fused.status if hasattr(fused, 'status') else 'unknown'}")
        click.echo(f"  Charge: {fused.charge if hasattr(fused, 'charge') else 'N/A'}")
        click.echo(f"  Output Route: {fused.output_route if hasattr(fused, 'output_route') else 'unknown'}")
        if hasattr(fused, 'rollback_available'):
            click.echo(f"  Rollback Available: {fused.rollback_available}")
        if hasattr(fused, 'source_fragments'):
            click.echo(f"\n  Source Fragments ({len(fused.source_fragments)}):")
            for sf in fused.source_fragments[:5]:
                name = sf.name if hasattr(sf, 'name') else sf.get('name', 'unnamed')
                click.echo(f"    - {name}")


@fusion.command("rollback")
@click.argument("fusion_id")
@click.option("--confirm", is_flag=True, help="Confirm rollback")
def rollback_fusion(fusion_id: str, confirm: bool):
    """Rollback a fusion."""
    if not confirm:
        click.echo("Use --confirm to execute rollback.", err=True)
        return

    init_system()
    protocol = get_fusion_protocol()

    result = protocol.rollback(fusion_id)
    if result.get("status") == "rolled_back":
        click.echo(f"\n::FUSION ROLLED BACK::")
        click.echo(f"  Fusion ID: {fusion_id}")
        click.echo(f"  Restored Fragments: {result.get('restored_count', 0)}")
    else:
        click.echo(f"Rollback failed: {result.get('reason', 'unknown')}", err=True)


@fusion.command("eligible")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def list_eligible(json_output: bool):
    """Show fusion-eligible fragments."""
    init_system()
    protocol = get_fusion_protocol()

    eligible = protocol.get_eligible_fragments()

    if json_output:
        eligible_data = [f.to_dict() if hasattr(f, 'to_dict') else f for f in eligible]
        click.echo(json.dumps(eligible_data, indent=2, default=str))
    else:
        if not eligible:
            click.echo("No fusion-eligible fragments found.")
            return

        click.echo(f"\n::FUSION-ELIGIBLE FRAGMENTS ({len(eligible)})::")
        for frag in eligible:
            name = frag.name if hasattr(frag, 'name') else frag.get('name', 'unnamed')
            charge = frag.charge if hasattr(frag, 'charge') else frag.get('charge', 'N/A')
            click.echo(f"  - {name} (charge: {charge})")


# =============================================================================
# Depth Command Group
# =============================================================================

@cli.group()
def depth():
    """View depth tracking information."""
    pass


@depth.command("status")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def depth_status(json_output: bool):
    """Show current depth tracking status."""
    init_system()
    tracker = get_depth_tracker()

    status_data = {
        "current_depth": tracker.current_depth,
        "max_depth_reached": tracker.max_depth_reached,
        "depth_exhaustions": tracker.depth_exhaustions,
        "limits": {
            "standard": DepthLimits.STANDARD,
            "extended": DepthLimits.EXTENDED,
            "emergency": DepthLimits.EMERGENCY,
            "absolute": DepthLimits.ABSOLUTE,
        }
    }

    if json_output:
        click.echo(json.dumps(status_data, indent=2))
    else:
        click.echo(f"\n::DEPTH TRACKING STATUS::")
        click.echo(f"  Current Depth: {status_data['current_depth']}")
        click.echo(f"  Max Depth Reached: {status_data['max_depth_reached']}")
        click.echo(f"  Exhaustion Count: {status_data['depth_exhaustions']}")
        click.echo(f"\n  Limits:")
        click.echo(f"    Standard: {DepthLimits.STANDARD}")
        click.echo(f"    Extended (LAW_LOOP+): {DepthLimits.EXTENDED}")
        click.echo(f"    Emergency: {DepthLimits.EMERGENCY}")
        click.echo(f"    Absolute: {DepthLimits.ABSOLUTE}")


@depth.command("limits")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def depth_limits(json_output: bool):
    """Show all depth limits."""
    limits_data = {
        "standard": {
            "value": DepthLimits.STANDARD,
            "description": "Normal routing operations",
        },
        "extended": {
            "value": DepthLimits.EXTENDED,
            "description": "With LAW_LOOP+ flag present",
        },
        "emergency": {
            "value": DepthLimits.EMERGENCY,
            "description": "RITUAL_COURT override",
        },
        "absolute": {
            "value": DepthLimits.ABSOLUTE,
            "description": "System hard limit (panic stop)",
        },
    }

    if json_output:
        click.echo(json.dumps(limits_data, indent=2))
    else:
        click.echo(f"\n::DEPTH LIMITS::")
        for name, info in limits_data.items():
            click.echo(f"\n  {name.upper()}: {info['value']}")
            click.echo(f"    {info['description']}")


@depth.command("log")
@click.option("--limit", "-l", type=int, default=20, help="Maximum entries to show")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def depth_log(limit: int, json_output: bool):
    """Show depth exhaustion log."""
    init_system()
    tracker = get_depth_tracker()

    log_entries = tracker.get_exhaustion_log()[:limit]

    if json_output:
        click.echo(json.dumps(log_entries, indent=2, default=str))
    else:
        if not log_entries:
            click.echo("No depth exhaustion events recorded.")
            return

        click.echo(f"\n::DEPTH EXHAUSTION LOG ({len(log_entries)})::")
        for entry in log_entries:
            click.echo(f"\n  [{entry.get('timestamp', 'unknown')}]")
            click.echo(f"    Depth: {entry.get('depth', 'N/A')}")
            click.echo(f"    Limit: {entry.get('limit', 'N/A')}")
            click.echo(f"    Action: {entry.get('action', 'unknown')}")


@depth.command("clear-log")
@click.option("--confirm", is_flag=True, help="Confirm clear")
def clear_depth_log(confirm: bool):
    """Clear the depth exhaustion log."""
    if not confirm:
        click.echo("Use --confirm to clear the log.", err=True)
        return

    init_system()
    tracker = get_depth_tracker()
    tracker.clear_exhaustion_log()

    click.echo("\n::DEPTH LOG CLEARED::")


# =============================================================================
# Queue Command Group
# =============================================================================

@cli.group()
def queue():
    """Manage the Soul Patchbay queue."""
    pass


@queue.command("list")
@click.option("--priority", "-p", type=click.Choice(["critical", "high", "standard", "background"]),
              help="Filter by priority")
@click.option("--limit", "-l", type=int, default=20, help="Maximum items to show")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def queue_list(priority: Optional[str], limit: int, json_output: bool):
    """List queue contents."""
    init_system()
    patchbay = get_patchbay_queue()

    patches = patchbay.peek_all()[:limit]

    # Filter by priority if specified
    if priority:
        from rege.core.constants import Priority
        priority_map = {
            "critical": Priority.CRITICAL,
            "high": Priority.HIGH,
            "standard": Priority.STANDARD,
            "background": Priority.BACKGROUND,
        }
        target_priority = priority_map.get(priority)
        patches = [p for p in patches if p.priority == target_priority]

    if json_output:
        patches_data = [p.to_dict() for p in patches]
        click.echo(json.dumps(patches_data, indent=2, default=str))
    else:
        if not patches:
            click.echo("Queue is empty." if not priority else f"No {priority} priority patches found.")
            return

        click.echo(f"\n::QUEUE CONTENTS ({len(patches)})::")
        for p in patches:
            priority_name = ["CRITICAL", "HIGH", "STANDARD", "BACKGROUND"][p.priority]
            click.echo(f"\n  [{priority_name}] {p.patch_id}")
            click.echo(f"    {p.input_node} → {p.output_node}")
            click.echo(f"    Charge: {p.charge} | Status: {p.status}")


@queue.command("stats")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def queue_stats(json_output: bool):
    """Show queue statistics."""
    init_system()
    patchbay = get_patchbay_queue()

    state = patchbay.get_queue_state()

    if json_output:
        click.echo(json.dumps(state, indent=2))
    else:
        click.echo(f"\n::QUEUE STATISTICS::")
        click.echo(f"  Size: {state['total_size']}/{state['max_size']}")
        click.echo(f"  Total Processed: {state['total_processed']}")
        click.echo(f"  Collisions: {state['collision_count']}")
        click.echo(f"  Deadlocks: {state['deadlock_count']}")
        click.echo(f"  Maintenance Mode: {state['maintenance_mode']}")
        click.echo(f"\n  Priority Distribution:")
        for priority, count in state.get('priority_distribution', {}).items():
            click.echo(f"    {priority}: {count}")


@queue.command("clear")
@click.option("--confirm", is_flag=True, help="Confirm clear")
def queue_clear(confirm: bool):
    """Clear the queue (with confirmation)."""
    if not confirm:
        click.echo("Use --confirm to clear the queue.", err=True)
        return

    init_system()
    patchbay = get_patchbay_queue()

    cleared = patchbay.clear()

    click.echo(f"\n::QUEUE CLEARED::")
    click.echo(f"  Patches Removed: {cleared}")


@queue.command("process")
@click.argument("count", type=int, default=1)
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def queue_process(count: int, json_output: bool):
    """Process n items from the queue."""
    init_system()
    patchbay = get_patchbay_queue()

    results = []
    for _ in range(count):
        patch = patchbay.dequeue()
        if patch:
            results.append({
                "patch_id": patch.patch_id,
                "route": f"{patch.input_node} → {patch.output_node}",
                "status": "dequeued",
            })
        else:
            break

    if json_output:
        click.echo(json.dumps(results, indent=2))
    else:
        if not results:
            click.echo("Queue is empty - nothing to process.")
            return

        click.echo(f"\n::PROCESSED ({len(results)} patches)::")
        for r in results:
            click.echo(f"  - {r['patch_id']}: {r['route']}")


# =============================================================================
# Batch Command
# =============================================================================

@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--continue-on-error", "-c", is_flag=True, help="Continue on error")
@click.option("--dry-run", "-d", is_flag=True, help="Show what would execute without running")
@click.option("--json-output", "-j", is_flag=True, help="Output results as JSON")
def batch(file: str, continue_on_error: bool, dry_run: bool, json_output: bool):
    """Execute multiple invocations from a file.

    Each invocation should be separated by a blank line.
    Lines starting with # are treated as comments.

    Example file:
        # This is a comment
        ::CALL_ORGAN HEART_OF_CANON
        ::WITH 'test memory'
        ::MODE mythic
        ::DEPTH standard
        ::EXPECT pulse_check

        # Another invocation
        ::CALL_ORGAN MIRROR_CABINET
        ::WITH 'reflection'
        ::MODE emotional_reflection
        ::DEPTH light
        ::EXPECT fragment_map
    """
    dispatcher = init_system()

    # Read and parse file
    with open(file, 'r') as f:
        content = f.read()

    # Split into invocations (separated by blank lines)
    invocations = []
    current_lines = []

    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue  # Skip comments
        if not stripped:
            if current_lines:
                invocations.append('\n'.join(current_lines))
                current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        invocations.append('\n'.join(current_lines))

    if dry_run:
        click.echo(f"\n::DRY RUN - {len(invocations)} invocations found::")
        for i, inv in enumerate(invocations, 1):
            lines = inv.strip().split('\n')
            organ = "unknown"
            for l in lines:
                if "::CALL_ORGAN" in l:
                    organ = l.replace("::CALL_ORGAN", "").strip()
                    break
            click.echo(f"  {i}. {organ}")
        return

    # Execute invocations
    results = []
    success_count = 0
    fail_count = 0

    for i, invocation in enumerate(invocations, 1):
        try:
            result = dispatcher.dispatch(invocation)
            results.append({
                "index": i,
                "organ": result.organ,
                "status": result.status,
                "success": result.status == "success",
            })
            if result.status == "success":
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            results.append({
                "index": i,
                "organ": "unknown",
                "status": "error",
                "error": str(e),
                "success": False,
            })
            fail_count += 1
            if not continue_on_error:
                break

    if json_output:
        output = {
            "total": len(invocations),
            "executed": len(results),
            "success": success_count,
            "failed": fail_count,
            "results": results,
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"\n::BATCH EXECUTION COMPLETE::")
        click.echo(f"  Total: {len(invocations)}")
        click.echo(f"  Executed: {len(results)}")
        click.echo(f"  Success: {success_count}")
        click.echo(f"  Failed: {fail_count}")

        if fail_count > 0:
            click.echo(f"\n  Failures:")
            for r in results:
                if not r.get('success'):
                    error = r.get('error', 'unknown error')
                    click.echo(f"    #{r['index']}: {error[:50]}")


# =============================================================================
# Bridge Command Group
# =============================================================================

@cli.group()
def bridge():
    """Manage external bridges (Obsidian, Git, Max/MSP)."""
    pass


@bridge.command("list")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def bridge_list(json_output: bool):
    """List available bridge types."""
    from rege.bridges import get_bridge_registry

    registry = get_bridge_registry()
    types = registry.list_types()
    active = registry.list_active()

    if json_output:
        click.echo(json.dumps({
            "available_types": types,
            "active_instances": active,
        }, indent=2))
    else:
        click.echo("\n::AVAILABLE BRIDGE TYPES::")
        for t in types:
            click.echo(f"  - {t}")

        if active:
            click.echo(f"\n::ACTIVE BRIDGES ({len(active)})::")
            for name in active:
                b = registry.get_bridge(name)
                status = b.current_status.value if b else "unknown"
                click.echo(f"  - {name} [{status}]")
        else:
            click.echo("\n  No active bridges.")


@bridge.command("connect")
@click.argument("bridge_type")
@click.option("--name", "-n", help="Instance name (defaults to type)")
@click.option("--path", "-p", help="Path for file-based bridges (Obsidian vault, Git repo)")
@click.option("--host", "-h", help="Host for network bridges (Max/MSP)")
@click.option("--port", type=int, help="Port for network bridges (Max/MSP)")
def bridge_connect(bridge_type: str, name: Optional[str], path: Optional[str],
                   host: Optional[str], port: Optional[int]):
    """Connect to an external bridge."""
    from rege.bridges import get_bridge_registry

    registry = get_bridge_registry()

    if not registry.has_type(bridge_type):
        click.echo(f"Unknown bridge type: {bridge_type}", err=True)
        click.echo(f"Available types: {', '.join(registry.list_types())}")
        return

    # Build config
    config = {}
    if path:
        if bridge_type == "obsidian":
            config["vault_path"] = path
        elif bridge_type == "git":
            config["repo_path"] = path
    if host:
        config["host"] = host
    if port:
        config["port"] = port

    # Create and connect
    instance_name = name or bridge_type
    bridge = registry.create_bridge(bridge_type, instance_name=instance_name, config=config)

    if bridge:
        result = bridge.connect()
        if result:
            click.echo(f"\n::BRIDGE CONNECTED::")
            click.echo(f"  Type: {bridge_type}")
            click.echo(f"  Name: {instance_name}")
            click.echo(f"  Status: {bridge.current_status.value}")
        else:
            click.echo(f"Connection failed: {bridge.last_error}", err=True)
    else:
        click.echo(f"Failed to create bridge", err=True)


@bridge.command("disconnect")
@click.argument("name")
def bridge_disconnect(name: str):
    """Disconnect from a bridge."""
    from rege.bridges import get_bridge_registry

    registry = get_bridge_registry()
    bridge = registry.get_bridge(name)

    if not bridge:
        click.echo(f"Bridge not found: {name}", err=True)
        return

    if bridge.disconnect():
        click.echo(f"\n::BRIDGE DISCONNECTED::")
        click.echo(f"  Name: {name}")
    else:
        click.echo(f"Disconnection failed: {bridge.last_error}", err=True)


@bridge.command("status")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def bridge_status(json_output: bool):
    """Show status of all bridges."""
    from rege.bridges import get_bridge_registry

    registry = get_bridge_registry()
    statuses = registry.get_all_status()

    if json_output:
        click.echo(json.dumps(statuses, indent=2, default=str))
    else:
        if not statuses:
            click.echo("No active bridges.")
            return

        click.echo(f"\n::BRIDGE STATUS ({len(statuses)})::")
        for name, status in statuses.items():
            click.echo(f"\n  [{status['status'].upper()}] {name}")
            if status.get("connected_at"):
                click.echo(f"    Connected: {status['connected_at']}")
            if status.get("last_error"):
                click.echo(f"    Error: {status['last_error']}")
            click.echo(f"    Operations: {status['operations_count']}")


@bridge.command("config")
@click.argument("bridge_type")
@click.option("--set", "set_values", multiple=True, help="Set config value (key=value)")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def bridge_config(bridge_type: str, set_values: tuple, json_output: bool):
    """Show or set bridge configuration."""
    from rege.bridges import get_bridge_config

    config = get_bridge_config()
    bridge_cfg = config.get_bridge_config(bridge_type)

    if set_values:
        # Set configuration values
        if not bridge_cfg:
            config.set_bridge_config(bridge_type, bridge_type)
            bridge_cfg = config.get_bridge_config(bridge_type)

        for kv in set_values:
            if "=" in kv:
                key, value = kv.split("=", 1)
                bridge_cfg.config[key] = value

        config.save()
        click.echo(f"Configuration updated for {bridge_type}")
        return

    if not bridge_cfg:
        click.echo(f"No configuration for bridge type: {bridge_type}", err=True)
        return

    if json_output:
        click.echo(json.dumps({
            "type": bridge_cfg.bridge_type,
            "name": bridge_cfg.name,
            "enabled": bridge_cfg.enabled,
            "auto_connect": bridge_cfg.auto_connect,
            "config": bridge_cfg.config,
        }, indent=2))
    else:
        click.echo(f"\n::BRIDGE CONFIG: {bridge_type}::")
        click.echo(f"  Enabled: {bridge_cfg.enabled}")
        click.echo(f"  Auto-connect: {bridge_cfg.auto_connect}")
        click.echo(f"  Config:")
        for key, value in bridge_cfg.config.items():
            click.echo(f"    {key}: {value}")


# =============================================================================
# Export/Import Commands for Bridges
# =============================================================================

@cli.command("export")
@click.argument("target", type=click.Choice(["obsidian"]))
@click.option("--fragment", "-f", help="Export specific fragment by ID")
@click.option("--all", "export_all", is_flag=True, help="Export all fragments")
def export_command(target: str, fragment: Optional[str], export_all: bool):
    """Export data to external bridge."""
    from rege.bridges import get_bridge_registry

    registry = get_bridge_registry()
    bridge = registry.get_bridge(target)

    if not bridge:
        click.echo(f"Bridge not connected: {target}", err=True)
        click.echo(f"Connect first with: rege bridge connect {target}")
        return

    if not bridge.is_connected:
        click.echo(f"Bridge not connected. Run: rege bridge connect {target}", err=True)
        return

    if fragment:
        # Export single fragment
        result = bridge.send({"fragment": {"id": fragment, "name": fragment}})
    elif export_all:
        # Export all (would need fragment registry)
        click.echo("Export all: Not implemented yet")
        return
    else:
        click.echo("Specify --fragment <id> or --all", err=True)
        return

    if result.get("status") == "exported":
        click.echo(f"\n::EXPORTED::")
        click.echo(f"  Target: {target}")
        if result.get("file"):
            click.echo(f"  File: {result['file']}")
    else:
        click.echo(f"Export failed: {result.get('error', 'unknown')}", err=True)


@cli.command("import")
@click.argument("source", type=click.Choice(["obsidian"]))
@click.option("--file", "-f", help="Import specific file")
@click.option("--dry-run", "-d", is_flag=True, help="Show what would be imported")
def import_command(source: str, file: Optional[str], dry_run: bool):
    """Import data from external bridge."""
    from rege.bridges import get_bridge_registry

    registry = get_bridge_registry()
    bridge = registry.get_bridge(source)

    if not bridge:
        click.echo(f"Bridge not connected: {source}", err=True)
        return

    if not bridge.is_connected:
        click.echo(f"Bridge not connected. Run: rege bridge connect {source}", err=True)
        return

    result = bridge.receive()

    if result and result.get("fragments"):
        fragments = result["fragments"]
        click.echo(f"\n::{'WOULD IMPORT' if dry_run else 'IMPORTED'} ({len(fragments)} items)::")
        for frag in fragments[:10]:
            click.echo(f"  - {frag.get('name', frag.get('id', 'unknown'))}")
        if len(fragments) > 10:
            click.echo(f"  ... and {len(fragments) - 10} more")
    else:
        click.echo("No data to import.")


# =============================================================================
# Chain Command Group (Workflow Orchestration)
# =============================================================================

@cli.group()
def chain():
    """Manage ritual chains (workflow orchestration)."""
    pass


@chain.command("list")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def chain_list(json_output: bool):
    """List all registered ritual chains."""
    from rege.orchestration import get_chain_registry
    from rege.orchestration.builtin_chains import register_builtin_chains

    # Register built-in chains if not already done
    registry = get_chain_registry()
    if registry.count() == 0:
        register_builtin_chains()

    chains = registry.list_chains()

    if json_output:
        chain_data = []
        for name in chains:
            c = registry.get(name)
            if c:
                chain_data.append({
                    "name": c.name,
                    "description": c.description,
                    "phases": len(c.phases),
                    "tags": c.tags,
                })
        click.echo(json.dumps(chain_data, indent=2))
    else:
        if not chains:
            click.echo("No chains registered.")
            return

        click.echo(f"\n::RITUAL CHAINS ({len(chains)})::")
        for name in chains:
            c = registry.get(name)
            if c:
                click.echo(f"\n  {c.name}")
                if c.description:
                    click.echo(f"    {c.description[:60]}")
                click.echo(f"    Phases: {len(c.phases)}")


@chain.command("show")
@click.argument("name")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def chain_show(name: str, json_output: bool):
    """Show details of a ritual chain."""
    from rege.orchestration import get_chain_registry
    from rege.orchestration.builtin_chains import register_builtin_chains

    registry = get_chain_registry()
    if registry.count() == 0:
        register_builtin_chains()

    chain = registry.get(name)
    if not chain:
        click.echo(f"Chain not found: {name}", err=True)
        return

    if json_output:
        click.echo(json.dumps(chain.to_dict(), indent=2, default=str))
    else:
        click.echo(f"\n::RITUAL CHAIN: {chain.name}::")
        if chain.description:
            click.echo(f"  Description: {chain.description}")
        click.echo(f"  Version: {chain.version}")
        click.echo(f"  Tags: {', '.join(chain.tags) if chain.tags else 'none'}")
        click.echo(f"  Entry Phase: {chain.entry_phase or chain.phases[0].name if chain.phases else 'none'}")

        click.echo(f"\n  Phases ({len(chain.phases)}):")
        for i, phase in enumerate(chain.phases, 1):
            click.echo(f"    {i}. {phase.name}")
            click.echo(f"       Organ: {phase.organ} | Mode: {phase.mode}")
            if phase.branches:
                click.echo(f"       Branches: {len(phase.branches)}")

        validation = chain.validate()
        if not validation["valid"]:
            click.echo(f"\n  Validation Errors:")
            for err in validation["errors"]:
                click.echo(f"    - {err}")


@chain.command("run")
@click.argument("name")
@click.option("--context", "-c", help="Initial context as JSON")
@click.option("--dry-run", "-d", is_flag=True, help="Show planned execution without running")
@click.option("--step", "-s", is_flag=True, help="Execute one phase at a time")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def chain_run(name: str, context: Optional[str], dry_run: bool, step: bool, json_output: bool):
    """Execute a ritual chain."""
    from rege.orchestration import get_chain_registry, RitualChainOrchestrator
    from rege.orchestration.builtin_chains import register_builtin_chains

    registry = get_chain_registry()
    if registry.count() == 0:
        register_builtin_chains()

    # Parse context if provided
    ctx = {}
    if context:
        try:
            ctx = json.loads(context)
        except json.JSONDecodeError:
            click.echo("Invalid JSON context", err=True)
            return

    orchestrator = RitualChainOrchestrator(registry=registry)

    if dry_run:
        result = orchestrator.dry_run(name, ctx)
        if json_output:
            click.echo(json.dumps(result, indent=2))
        else:
            if "error" in result:
                click.echo(f"Error: {result['error']}", err=True)
                return
            click.echo(f"\n::DRY RUN: {name}::")
            click.echo(f"  Planned phases: {result['phase_count']}")
            for p in result["planned_phases"]:
                status = "EXECUTE" if p["would_execute"] else "SKIP"
                click.echo(f"    [{status}] {p['name']} ({p['organ']}:{p['mode']})")
        return

    try:
        execution = orchestrator.execute_chain(name, context=ctx, step_mode=step)

        if json_output:
            click.echo(json.dumps(execution.to_dict(), indent=2, default=str))
        else:
            click.echo(f"\n::CHAIN EXECUTION: {name}::")
            click.echo(f"  Execution ID: {execution.execution_id}")
            click.echo(f"  Status: {execution.status.value}")
            click.echo(f"  Duration: {execution.get_duration_ms()}ms")

            click.echo(f"\n  Phase Results ({len(execution.phase_results)}):")
            for result in execution.phase_results:
                status_icon = "✓" if result.status.value == "completed" else "✗"
                click.echo(f"    {status_icon} {result.phase_name}: {result.status.value}")

            if execution.escalations:
                click.echo(f"\n  Escalations: {', '.join(execution.escalations)}")

            if execution.error:
                click.echo(f"\n  Error: {execution.error}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)


@chain.command("history")
@click.option("--chain-name", "-c", help="Filter by chain name")
@click.option("--limit", "-l", default=10, help="Maximum results")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def chain_history(chain_name: Optional[str], limit: int, json_output: bool):
    """Show chain execution history."""
    from rege.orchestration import get_chain_registry

    registry = get_chain_registry()
    executions = registry.get_executions(chain_name=chain_name, limit=limit)

    if json_output:
        click.echo(json.dumps([e.to_dict() for e in executions], indent=2, default=str))
    else:
        if not executions:
            click.echo("No execution history.")
            return

        click.echo(f"\n::EXECUTION HISTORY ({len(executions)})::")
        for e in executions:
            click.echo(f"\n  [{e.status.value}] {e.chain_name}")
            click.echo(f"    ID: {e.execution_id}")
            click.echo(f"    Started: {e.started_at[:19]}")
            click.echo(f"    Phases: {len(e.phase_results)}")
            if e.error:
                click.echo(f"    Error: {e.error[:40]}...")


@chain.command("stats")
@click.option("--chain-name", "-c", help="Filter by chain name")
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def chain_stats(chain_name: Optional[str], json_output: bool):
    """Show chain execution statistics."""
    from rege.orchestration import get_chain_registry

    registry = get_chain_registry()
    stats = registry.get_execution_stats(chain_name=chain_name)

    if json_output:
        click.echo(json.dumps(stats, indent=2))
    else:
        click.echo(f"\n::EXECUTION STATISTICS::")
        if chain_name:
            click.echo(f"  Chain: {chain_name}")
        click.echo(f"  Total Executions: {stats['total']}")
        click.echo(f"  Completed: {stats['completed']}")
        click.echo(f"  Failed: {stats['failed']}")
        click.echo(f"  Running: {stats.get('running', 0)}")
        click.echo(f"  Avg Duration: {stats['avg_duration_ms']}ms")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
