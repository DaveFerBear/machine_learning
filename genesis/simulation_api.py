import threading
import numpy as np
import torch
from collections import deque
from typing import Optional


class SimulationController:
    """
    Controller for Genesis simulation with real-time execution and command queuing.
    """

    def __init__(self, scene, arm, dofs_idx, end_effector):
        """
        Initialize the simulation controller.

        Args:
            scene: Genesis scene object
            arm: Robot arm entity
            dofs_idx: List of DOF indices for the arm joints
            end_effector: End effector link object
        """
        self.scene = scene
        self.arm = arm
        self.dofs_idx = dofs_idx
        self.end_effector = end_effector

        # Command queue and synchronization
        self.command_queue = deque()
        self.queue_lock = threading.Lock()

        # Current state
        self.current_task = "Idle"
        self.is_executing = False
        self.current_path = None
        self.current_waypoint_idx = 0

        # Thread control
        self.running = False
        self.sim_thread = None

    def start(self):
        """Start the real-time simulation loop in a background thread."""
        if self.running:
            print("Simulation already running")
            return

        self.running = True
        self.sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.sim_thread.start()
        print("Simulation started")

    def stop(self):
        """Stop the simulation loop."""
        self.running = False
        if self.sim_thread:
            self.sim_thread.join()
        print("Simulation stopped")

    def move(self, x: float, y: float, z: float):
        """
        Queue a move command to the specified position.

        Args:
            x, y, z: Target position coordinates

        Returns:
            dict: Status information including queue length
        """
        target_pos = np.array([x, y, z], dtype=np.float32)

        with self.queue_lock:
            self.command_queue.append(target_pos)
            queue_length = len(self.command_queue)

        print(f"Queued move to ({x:.3f}, {y:.3f}, {z:.3f}). "
              f"Current task: {self.current_task}. Queue length: {queue_length}")

        return {
            "status": "queued",
            "position": [x, y, z],
            "queue_length": queue_length,
            "current_task": self.current_task
        }

    def _simulation_loop(self):
        """
        Main simulation loop running in background thread.
        Continuously steps the simulation and processes queued commands.
        """
        while self.running:
            # Always step the simulation for real-time execution
            self.scene.step()

            # If currently executing a path, continue executing waypoints
            if self.is_executing and self.current_path is not None:
                self._execute_waypoint()
            # Otherwise, check if there are queued commands to process
            elif not self.is_executing:
                self._process_next_command()

    def _process_next_command(self):
        """Process the next command from the queue if available."""
        target_pos = None

        with self.queue_lock:
            if self.command_queue:
                target_pos = self.command_queue.popleft()

        if target_pos is not None:
            # Update current task
            self.current_task = f"Moving to ({target_pos[0]:.3f}, {target_pos[1]:.3f}, {target_pos[2]:.3f})"
            print(f"\n=== Starting: {self.current_task} ===")

            # Compute IK
            qpos = self.arm.inverse_kinematics(
                link=self.end_effector,
                pos=target_pos,
            )

            # Convert to numpy if needed
            if isinstance(qpos, torch.Tensor):
                qpos = qpos.detach().cpu().numpy()
            else:
                qpos = np.asarray(qpos, dtype=np.float32)

            # Plan path from current position to target
            self.current_path = self.arm.plan_path(
                qpos_goal=qpos,
                num_waypoints=10,
            )

            # Start executing the path
            self.is_executing = True
            self.current_waypoint_idx = 0
        else:
            # No commands in queue, idle
            if self.current_task != "Idle":
                self.current_task = "Idle"

    def _execute_waypoint(self):
        """Execute one waypoint from the current path."""
        if self.current_waypoint_idx < len(self.current_path):
            waypoint = self.current_path[self.current_waypoint_idx]
            self.arm.control_dofs_position(waypoint[:len(self.dofs_idx)], self.dofs_idx)
            self.current_waypoint_idx += 1

            # Log progress periodically
            if self.current_waypoint_idx % 25 == 0:
                actual_pos = self.end_effector.get_pos()
                if isinstance(actual_pos, torch.Tensor):
                    actual_pos = actual_pos.detach().cpu().numpy()
                print(f"  Step {self.current_waypoint_idx:3d}/{len(self.current_path)}: "
                      f"Hand = ({actual_pos[0]:.3f}, {actual_pos[1]:.3f}, {actual_pos[2]:.3f})")
        else:
            # Path execution complete
            actual_pos = self.end_effector.get_pos()
            if isinstance(actual_pos, torch.Tensor):
                actual_pos = actual_pos.detach().cpu().numpy()
            print(f"  Reached: Hand = ({actual_pos[0]:.3f}, {actual_pos[1]:.3f}, {actual_pos[2]:.3f})")
            print(f"=== Completed: {self.current_task} ===\n")

            # Reset execution state
            self.is_executing = False
            self.current_path = None
            self.current_waypoint_idx = 0
            self.current_task = "Idle"

    def get_status(self):
        """
        Get current status of the controller.

        Returns:
            dict: Status information
        """
        with self.queue_lock:
            queue_length = len(self.command_queue)

        actual_pos = self.end_effector.get_pos()
        if isinstance(actual_pos, torch.Tensor):
            actual_pos = actual_pos.detach().cpu().numpy()

        return {
            "current_task": self.current_task,
            "queue_length": queue_length,
            "is_executing": self.is_executing,
            "current_position": actual_pos.tolist() if actual_pos is not None else None
        }
