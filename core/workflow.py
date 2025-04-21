"""Workflow processing module implementation."""

from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic, Union
from .config.config_loader import ConfigLoader
import logging
import time
import uuid
from .context import Context

# Type definitions
T = TypeVar("T")
StepResult = Dict[str, Any]


class WorkflowStep:
    """A single step in a workflow."""

    def __init__(self, step_id: str, config_section: str = None):
        """Initialize a workflow step.

        Args:
            step_id: Unique identifier for this step
            config_section: Configuration section for this step
        """
        self._id = step_id
        self._logger = logging.getLogger(f"core.workflow.step.{step_id}")
        self._config_loader = ConfigLoader()

        # Load step-specific configuration
        self._config_section = config_section or f"workflow.steps.{step_id}"
        self.reload_config()

        self._logger.debug(f"Initialized workflow step: {step_id}")

    def get_id(self) -> str:
        """Get the step ID."""
        return self._id

    def reload_config(self) -> None:
        """Reload configuration from the config loader."""
        self._config = self._load_config()
        self._logger.debug(f"Reloaded configuration for step: {self._id}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for this step."""
        try:
            return self._config_loader.get_config(self._config_section)
        except Exception as e:
            self._logger.warning(
                f"Failed to load config for section {self._config_section}: {e}"
            )
            return {}

    def execute(self, context: Context) -> StepResult:
        """Execute this workflow step.

        Args:
            context: The context for this execution

        Returns:
            Step execution result
        """
        start_time = time.time()
        self._logger.info(f"Executing step: {self._id}")

        try:
            # Check if step is enabled
            if not self._config.get("enabled", True):
                self._logger.warning(f"Step {self._id} is disabled")
                return {"status": "skipped", "reason": "step_disabled"}

            # Execute step implementation
            result = self._execute(context)

            # Record execution in context
            context.set(
                f"step_result.{self._id}",
                {"status": result.get("status", "unknown"),
                 "timestamp": time.time()},
            )

            return result
        except Exception as e:
            self._logger.error(f"Error executing step {self._id}: {e}")

            # Record error in context
            context.set(
                f"step_result.{self._id}",
                {"status": "error", "error": str(e), "timestamp": time.time()},
            )

            return {"status": "error", "error": str(e)}
        finally:
            elapsed = time.time() - start_time
            self._logger.info(f"Step {self._id} executed in {elapsed:.3f}s")

    def _execute(self, context: Context) -> StepResult:
        """Implementation of step execution logic (to be overridden)."""
        raise NotImplementedError(
            "WorkflowStep subclasses must implement _execute()")

    def validate(self, context: Context) -> bool:
        """Validate if this step can be executed with the given context."""
        # Default implementation always validates
        return True


class Workflow:
    """A workflow composed of multiple steps."""

    def __init__(self, workflow_id: str, config_section: str = None):
        """Initialize a workflow.

        Args:
            workflow_id: Unique identifier for this workflow
            config_section: Configuration section for this workflow
        """
        self._id = workflow_id
        self._logger = logging.getLogger(f"core.workflow.{workflow_id}")
        self._config_loader = ConfigLoader()

        # Load workflow-specific configuration
        self._config_section = config_section or f"workflows.{workflow_id}"
        self.reload_config()

        # Initialize steps collection
        self._steps: Dict[str, WorkflowStep] = {}
        self._step_order: List[str] = []

        self._logger.debug(f"Initialized workflow: {workflow_id}")

    def get_id(self) -> str:
        """Get the workflow ID."""
        return self._id

    def reload_config(self) -> None:
        """Reload configuration from the config loader."""
        self._config = self._load_config()

        # Load step order from configuration
        self._step_order = self._config.get("step_order", [])

        self._logger.debug(f"Reloaded configuration for workflow: {self._id}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration for this workflow."""
        try:
            return self._config_loader.get_config(self._config_section)
        except Exception as e:
            self._logger.warning(
                f"Failed to load config for section {self._config_section}: {e}"
            )
            return {"step_order": []}

    def add_step(self, step: WorkflowStep, position: Optional[int] = None) -> None:
        """Add a step to this workflow.

        Args:
            step: The workflow step to add
            position: Optional position in the execution order
        """
        step_id = step.get_id()
        self._steps[step_id] = step

        # Add to step order if not already present
        if step_id not in self._step_order:
            if position is not None and 0 <= position <= len(self._step_order):
                self._step_order.insert(position, step_id)
            else:
                self._step_order.append(step_id)

        self._logger.debug(f"Added step {step_id} to workflow {self._id}")

    def remove_step(self, step_id: str) -> bool:
        """Remove a step from this workflow."""
        if step_id in self._steps:
            del self._steps[step_id]

            # Remove from step order
            if step_id in self._step_order:
                self._step_order.remove(step_id)

            self._logger.debug(
                f"Removed step {step_id} from workflow {self._id}")
            return True

        return False

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        return self._steps.get(step_id)

    def get_steps(self) -> List[WorkflowStep]:
        """Get all steps in execution order."""
        return [
            self._steps[step_id]
            for step_id in self._step_order
            if step_id in self._steps
        ]

    def execute(self, context: Context) -> Dict[str, Any]:
        """Execute the workflow with the given context.

        Args:
            context: The context for this workflow execution

        Returns:
            Workflow execution result
        """
        workflow_execution_id = str(uuid.uuid4())
        start_time = time.time()

        self._logger.info(
            f"Executing workflow {self._id} (execution_id={workflow_execution_id})"
        )

        # Initialize workflow execution in context
        context.set(
            "workflow",
            {
                "id": self._id,
                "execution_id": workflow_execution_id,
                "start_time": start_time,
                "steps": {},
            },
        )

        results = {}
        success = True

        # Execute steps in order
        for step_id in self._step_order:
            if step_id not in self._steps:
                self._logger.warning(
                    f"Step {step_id} not found in workflow {self._id}")
                continue

            step = self._steps[step_id]

            # Skip step if validation fails
            if not step.validate(context):
                self._logger.warning(
                    f"Step {step_id} validation failed, skipping")
                results[step_id] = {"status": "skipped",
                                    "reason": "validation_failed"}
                continue

            # Execute the step
            step_result = step.execute(context)
            results[step_id] = step_result

            # Update workflow execution in context
            workflow_data = context.get("workflow", {})
            if "steps" not in workflow_data:
                workflow_data["steps"] = {}

            workflow_data["steps"][step_id] = {
                "status": step_result.get("status"),
                "timestamp": time.time(),
            }
            context.set("workflow", workflow_data)

            # Break workflow if step failed and abort_on_error is true
            if step_result.get("status") == "error" and self._config.get(
                "abort_on_error", True
            ):
                self._logger.warning(
                    f"Aborting workflow {self._id} due to step {step_id} error"
                )
                success = False
                break

        # Finalize workflow execution in context
        end_time = time.time()
        workflow_data = context.get("workflow", {})
        workflow_data.update(
            {
                "end_time": end_time,
                "duration": end_time - start_time,
                "success": success,
            }
        )
        context.set("workflow", workflow_data)

        self._logger.info(
            f"Workflow {self._id} completed in {end_time - start_time:.3f}s (success={success})"
        )

        return {
            "workflow_id": self._id,
            "execution_id": workflow_execution_id,
            "success": success,
            "duration": end_time - start_time,
            "results": results,
        }