import argparse
import numpy as np
import genesis as gs
import torch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu, logging_level="warning")

    ########################## create a scene ##########################
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(
            dt=0.01,
        ),
        viewer_options=gs.options.ViewerOptions(
            camera_pos=(0, -3.5, 2.5),
            camera_lookat=(0.0, 0.0, 0.5),
            camera_fov=30,
            max_FPS=60,
        ),
        vis_options = gs.options.VisOptions(
            show_world_frame = True,
            world_frame_size = 0.2, # length of the world frame in meter
            show_link_frame  = False,
            show_cameras     = False,
            # plane_reflection = False,
            # ambient_light    = (0.7, 0.7, 0.7),
        ),
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    plane = scene.add_entity(
        gs.morphs.Plane(),
        surface=gs.surfaces.Default(
            color=(0.8, 0.8, 0.8, 1.0),  # Light gray
        ),
    )
    
    # Add static R3 frame at origin (fixed = not affected by physics)
    r3_frame = scene.add_entity(
        morph=gs.morphs.Mesh(
            file="./scene-gen/parts/R3_frame/R3_frame.glb",
            scale=1.0,
            pos=(0.5, 0, 0.3),
            euler=(0, 0, 0),
            fixed=True,  # Makes it static/fixed
        ),
        surface=gs.surfaces.Default(color=(0.05, 0.05, 0.05, 1.0)),  # Black material
    )

    arm = scene.add_entity(
        gs.morphs.MJCF(
            file="./robots/dummy-6dof.xml",
             pos=(0.5, 0.0, 0.55),
            euler=(0, 0, 90),
        ),
    )

    jnt_names = [
        "SHOULDER_A", "SHOULDER_B", "SHOULDER_C",
        "ELBOW_A", "ELBOW_B", "WRIST_A",
    ]

    dofs_idx = [arm.get_joint(name).dof_idx_local for name in jnt_names]

    cube = scene.add_entity(
        gs.morphs.Box(
            size=(0.04, 0.04, 0.04),
            pos=(0.6, 0.0, 0.02),
        ),
    )

    ########################## build ##########################
    scene.build()

    # Add camera and attach to end effector (must be after scene.build())
    end_effector = arm.get_link("hand")
    ee_camera = scene.add_camera(
        res=(640, 480),
        pos=(0, 0, 0),
        lookat=(0, 0.1, 0),
        fov=60,
    )

    # Create offset transformation matrix (identity = no offset from link)
    offset_T = np.eye(4, dtype=np.float32)

    # Attach camera to end effector
    ee_camera.attach(end_effector, offset_T)
    print(f"Added camera to end effector: {ee_camera}")

    # Gains (PD in joint space, but targets come from IK)
    arm.set_dofs_kp(
        kp=np.array([200.0, 200.0, 150.0, 120.0, 120.0, 50.0]),
        dofs_idx_local=dofs_idx,
    )
    arm.set_dofs_kv(
        kv=np.array([20.0, 20.0, 15.0, 10.0, 10.0, 5.0]),
        dofs_idx_local=dofs_idx,
    )
    arm.set_dofs_force_range(
        lower=np.array([-50.0, -50.0, -30.0, -30.0, -20.0, -10.0]),
        upper=np.array([ 50.0,  50.0,  30.0,  30.0,  20.0,  10.0]),
        dofs_idx_local=dofs_idx,
    )

    # Set initial joint position (copy values from logged output during simulation)
    # Using joint positions from Cycle 3, Step 150 - a good middle configuration
    initial_joints = np.array([1.4604863, 0.7191452, -0.12146536, -0.41686273, 0.15724644, -0.98767394])

    if initial_joints is not None:
        print(f"\nSetting initial joint position: {initial_joints}")
        arm.set_dofs_position(initial_joints, dofs_idx)
        for _ in range(50):  # Let it settle
            scene.step()

    run_sim(scene, arm, dofs_idx)


def run_sim(scene, arm, dofs_idx):
    """
    Motion planning between two target positions:
    - Define two target end-effector positions
    - Use IK to get joint positions
    - Use motion planner to generate smooth trajectories
    - Execute waypoints with PD control
    """

    # End-effector link (defined in XML as <body name="hand">)
    end_effector = arm.get_link("hand")

    # Log initial joint configuration
    initial_joints = arm.get_dofs_position(dofs_idx)
    if isinstance(initial_joints, torch.Tensor):
        initial_joints = initial_joints.detach().cpu().numpy()
    initial_pos = end_effector.get_pos()
    print(f"\n=== Initial Configuration ===")
    print(f"Joint positions: {initial_joints}")
    print(f"Hand position: {initial_pos}")
    print(f"=============================\n")

    # Define array of target positions to visit in sequence
    target_positions = np.array([
        [0.4, 0.2, 0.3],
        [0.4, 0.4, 0.3],
        [0.6, 0.4, 0.35],
        [0.6, 0.2, 0.35],
    ], dtype=np.float32)

    print("\n=== Computing IK for all targets ===")
    target_joint_positions = []

    for i, target_pos in enumerate(target_positions):
        print(f"Target {i}: {target_pos}")
        qpos = arm.inverse_kinematics(
            link=end_effector,
            pos=target_pos,
        )

        # Convert to numpy if needed
        if isinstance(qpos, torch.Tensor):
            qpos = qpos.detach().cpu().numpy()
        else:
            qpos = np.asarray(qpos, dtype=np.float32)

        target_joint_positions.append(qpos)

    print("IK computation complete\n")

    # Plan all paths between consecutive targets
    print("\n=== Planning all paths ===")
    planned_paths = []

    # Plan from initial position to first target
    print(f"Planning path: initial -> target 0")
    path = arm.plan_path(
        qpos_goal=target_joint_positions[0],
        num_waypoints=100,
    )
    planned_paths.append(path)

    # Plan paths between consecutive targets
    for i in range(len(target_joint_positions)):
        next_idx = (i + 1) % len(target_joint_positions)
        print(f"Planning path: target {i} -> target {next_idx}")

        # Set arm to current target position to plan from there
        arm.set_dofs_position(target_joint_positions[i], dofs_idx)
        scene.step()

        path = arm.plan_path(
            qpos_goal=target_joint_positions[next_idx],
            num_waypoints=100,
        )
        planned_paths.append(path)

    print("Path planning complete\n")

    # Reset to initial position
    arm.set_dofs_position(initial_joints, dofs_idx)
    for _ in range(50):
        scene.step()

    # Execute motion using pre-planned paths
    num_cycles = 10
    for cycle in range(num_cycles):
        print(f"\n{'='*50}")
        print(f"Cycle {cycle + 1}/{num_cycles}")
        print(f"{'='*50}")

        # First cycle uses path from initial to target 0, others start from target 3->0
        if cycle == 0:
            path_indices = range(len(planned_paths))
        else:
            path_indices = range(1, len(planned_paths))

        for path_idx in path_indices:
            # Destination target index (wraps around for last path which goes back to target 0)
            target_idx = path_idx % len(target_positions)
            print(f"\nMoving to target {target_idx}: {target_positions[target_idx]}")

            path = planned_paths[path_idx]

            # Execute path
            for i, waypoint in enumerate(path):
                arm.control_dofs_position(waypoint[:len(dofs_idx)], dofs_idx)
                scene.step()

                # Print progress periodically
                if i % 25 == 0:
                    actual_pos = end_effector.get_pos()
                    if isinstance(actual_pos, torch.Tensor):
                        actual_pos = actual_pos.detach().cpu().numpy()
                    print(f"  Step {i:3d}: Hand = {actual_pos}")

            # Settling time
            for i in range(50):
                scene.step()

            # Print final position
            actual_pos = end_effector.get_pos()
            if isinstance(actual_pos, torch.Tensor):
                actual_pos = actual_pos.detach().cpu().numpy()
            print(f"  Reached: Hand = {actual_pos}")


if __name__ == "__main__":
    main()
