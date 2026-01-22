"""
RE:GE Code Forge - Symbol-to-code translation engine.

Based on: RE-GE_ORG_BODY_06_CODE_FORGE.md

The Code Forge governs:
- Symbol-to-code translation
- Multiple translation modes (FUNC, CLASS, WAVE, TREE, SIM)
- Code generation in Python, Max/MSP, JSON
"""

from typing import List, Dict, Any
import json

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch


class CodeForge(OrganHandler):
    """
    The Code Forge - Symbol-to-code translation engine.

    Modes:
    - func_mode: Translate to Python functions
    - class_mode: Translate to Python classes
    - wave_mode: Translate to waveform/LFO specs
    - tree_mode: Translate to flowcharts/decision trees
    - sim_mode: Translate to simulation specs
    - default: Auto-detect best mode
    """

    @property
    def name(self) -> str:
        return "CODE_FORGE"

    @property
    def description(self) -> str:
        return "Symbol-to-code translation engine for Python, Max/MSP, and JSON"

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Code Forge."""
        mode = invocation.mode.lower()

        if mode == "func_mode":
            return self._func_mode(invocation, patch)
        elif mode == "class_mode":
            return self._class_mode(invocation, patch)
        elif mode == "wave_mode":
            return self._wave_mode(invocation, patch)
        elif mode == "tree_mode":
            return self._tree_mode(invocation, patch)
        elif mode == "sim_mode":
            return self._sim_mode(invocation, patch)
        else:
            return self._default_mode(invocation, patch)

    def _func_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Translate to Python function."""
        func_name = self._symbol_to_func_name(invocation.symbol)
        code = self._generate_function(func_name, invocation.symbol, invocation.charge)

        return {
            "output_type": ".py",
            "mode": "func_mode",
            "function_name": func_name,
            "code": code,
            "charge_embedded": invocation.charge,
        }

    def _class_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Translate to Python class."""
        class_name = self._symbol_to_class_name(invocation.symbol)
        code = self._generate_class(class_name, invocation.symbol, invocation.charge)

        return {
            "output_type": ".py",
            "mode": "class_mode",
            "class_name": class_name,
            "code": code,
            "archetype_basis": invocation.symbol,
        }

    def _wave_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Translate to waveform/LFO specification."""
        wave_spec = self._generate_wave_spec(invocation.symbol, invocation.charge)

        return {
            "output_type": ".maxpat",
            "mode": "wave_mode",
            "wave_spec": wave_spec,
            "frequency_basis": invocation.charge / 10,  # Charge determines base frequency
        }

    def _tree_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Translate to flowchart/decision tree."""
        tree = self._generate_decision_tree(invocation.symbol)

        return {
            "output_type": ".json",
            "mode": "tree_mode",
            "decision_tree": tree,
            "branch_count": len(tree.get("branches", [])),
        }

    def _sim_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Translate to simulation specification."""
        sim = self._generate_simulation(invocation.symbol, invocation.charge)

        return {
            "output_type": ".json",
            "mode": "sim_mode",
            "simulation": sim,
            "complexity": "high" if invocation.charge >= 71 else "standard",
        }

    def _default_mode(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Auto-detect best mode based on content."""
        symbol = invocation.symbol.lower()

        # Detect best mode
        if "function" in symbol or "do" in symbol or "action" in symbol:
            return self._func_mode(invocation, patch)
        elif "type" in symbol or "kind" in symbol or "archetype" in symbol:
            return self._class_mode(invocation, patch)
        elif "feel" in symbol or "emotion" in symbol or "wave" in symbol:
            return self._wave_mode(invocation, patch)
        elif "if" in symbol or "decision" in symbol or "choice" in symbol:
            return self._tree_mode(invocation, patch)
        else:
            # Default to JSON representation
            return {
                "output_type": ".json",
                "mode": "auto_json",
                "symbol_data": {
                    "content": invocation.symbol,
                    "charge": invocation.charge,
                    "flags": invocation.flags,
                    "depth": invocation.depth.value,
                },
            }

    def _symbol_to_func_name(self, symbol: str) -> str:
        """Convert symbol to valid function name."""
        words = symbol.split()[:4]
        name = "_".join(w.lower() for w in words if w.isalnum())
        return f"process_{name}" if name else "process_symbol"

    def _symbol_to_class_name(self, symbol: str) -> str:
        """Convert symbol to valid class name."""
        words = symbol.split()[:3]
        name = "".join(w.capitalize() for w in words if w.isalnum())
        return name if name else "SymbolicEntity"

    def _generate_function(self, func_name: str, symbol: str, charge: int) -> str:
        """Generate Python function code."""
        return f'''def {func_name}(input_data, charge={charge}):
    """
    Generated from symbol: {symbol[:50]}...
    Charge level: {charge}
    """
    # Process input based on symbolic meaning
    if charge >= 86:
        return {{"status": "critical", "action": "escalate"}}
    elif charge >= 71:
        return {{"status": "intense", "action": "process_deeply"}}
    else:
        return {{"status": "standard", "action": "process"}}
'''

    def _generate_class(self, class_name: str, symbol: str, charge: int) -> str:
        """Generate Python class code."""
        return f'''class {class_name}:
    """
    Archetype generated from: {symbol[:50]}...
    Base charge: {charge}
    """

    def __init__(self, charge={charge}):
        self.charge = charge
        self.status = "active"

    def process(self, input_data):
        """Process input through this archetype."""
        return {{
            "archetype": "{class_name}",
            "charge": self.charge,
            "processed": True
        }}

    def get_tier(self):
        if self.charge >= 86:
            return "CRITICAL"
        elif self.charge >= 71:
            return "INTENSE"
        elif self.charge >= 51:
            return "ACTIVE"
        elif self.charge >= 26:
            return "PROCESSING"
        return "LATENT"
'''

    def _generate_wave_spec(self, symbol: str, charge: int) -> Dict[str, Any]:
        """Generate waveform specification."""
        # Map charge to wave parameters
        frequency = charge / 10  # 0-10 Hz
        amplitude = min(1.0, charge / 100)

        return {
            "type": "lfo",
            "waveform": "sine" if charge < 50 else "triangle" if charge < 75 else "saw",
            "frequency": frequency,
            "amplitude": amplitude,
            "phase": 0,
            "modulation_targets": ["filter_cutoff", "volume"],
            "symbol_source": symbol[:30],
        }

    def _generate_decision_tree(self, symbol: str) -> Dict[str, Any]:
        """Generate decision tree from symbol."""
        return {
            "root": {
                "question": f"Regarding: {symbol[:50]}",
                "condition": "charge_level",
            },
            "branches": [
                {
                    "condition": "charge >= 86",
                    "action": "escalate_to_ritual_court",
                    "label": "CRITICAL",
                },
                {
                    "condition": "charge >= 71",
                    "action": "deep_processing",
                    "label": "INTENSE",
                },
                {
                    "condition": "charge >= 51",
                    "action": "standard_processing",
                    "label": "ACTIVE",
                },
                {
                    "condition": "default",
                    "action": "archive_and_monitor",
                    "label": "BACKGROUND",
                },
            ],
        }

    def _generate_simulation(self, symbol: str, charge: int) -> Dict[str, Any]:
        """Generate simulation specification."""
        return {
            "name": f"Sim_{self._symbol_to_func_name(symbol)}",
            "type": "myth_simulation",
            "parameters": {
                "initial_charge": charge,
                "decay_rate": 0.05 if charge >= 51 else 0.1,
                "interaction_probability": charge / 100,
            },
            "agents": [
                {"type": "symbol", "properties": {"content": symbol[:30]}},
                {"type": "observer", "properties": {"charge_threshold": 50}},
            ],
            "rules": [
                "charge decays over time unless reinforced",
                "high charge triggers ritual events",
                "critical charge spawns new symbols",
            ],
        }

    def get_valid_modes(self) -> List[str]:
        return ["func_mode", "class_mode", "wave_mode", "tree_mode", "sim_mode", "default"]

    def get_output_types(self) -> List[str]:
        return [".py", ".maxpat", ".json", ".glyph", ".ritual_code"]
