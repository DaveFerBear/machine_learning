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
    plane = scene.add_entity(gs.morphs.Plane())
    
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
            pos=(0.5, 0.0, 0.6),
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
    # Adjusted first joint by +π to flip it forward into the box
    initial_joints = np.array([1.4604863, 0.7191452, -0.12146536, -0.41686273, 0.15724644, -0.98767394])

    if initial_joints is not None:
        print(f"\nSetting initial joint position: {initial_joints}")
        arm.set_dofs_position(initial_joints, dofs_idx)
        for _ in range(50):  # Let it settle
            scene.step()

    run_sim(scene, arm, dofs_idx)


def run_sim(scene, arm, dofs_idx):
    """
    Simple PD control alternating between two joint configurations
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

    # Define two joint configurations
    # Adjusted first joint by +π to flip it forward into the box
    joints_a = np.array([1.6719044, 0.23790327, -1.1429352, -0.9674109, -0.16906175, -1.2938077], dtype=np.float32)
    joints_b = np.array([1.7719044, 0.33790327, -1.0429352, -0.8674109, -0.06906175, -1.1938077], dtype=np.float32)  # Small variation

    print(f"Target joints A: {joints_a}")
    print(f"Target joints B: {joints_b}")
    print("\nStarting motion...")

    # Execute motion: alternate between two joint configurations
    for cycle in range(6):
        print(f"\nCycle {cycle + 1}: Moving to joints A")

        # Move to joints A
        for i in range(200):
            arm.control_dofs_position(joints_a, dofs_idx)
            scene.step()

            # Print actual position and joint angles periodically
            if i % 50 == 0:
                actual_pos = end_effector.get_pos()
                current_joints = arm.get_dofs_position(dofs_idx)
                if isinstance(current_joints, torch.Tensor):
                    current_joints = current_joints.detach().cpu().numpy()
                print(f"  Step {i}: Hand pos = {actual_pos}")
                print(f"           Joint pos = {current_joints}")

        # Settling time
        for i in range(100):
            scene.step()
            if i % 25 == 0:
                actual_pos = end_effector.get_pos()
                current_joints = arm.get_dofs_position(dofs_idx)
                if isinstance(current_joints, torch.Tensor):
                    current_joints = current_joints.detach().cpu().numpy()
                print(f"  Settling {i}: Hand = {actual_pos}, Joints = {current_joints}")

        print(f"\nCycle {cycle + 1}: Moving to joints B")

        # Move to joints B
        for i in range(200):
            arm.control_dofs_position(joints_b, dofs_idx)
            scene.step()

            # Print actual position and joint angles periodically
            if i % 50 == 0:
                actual_pos = end_effector.get_pos()
                current_joints = arm.get_dofs_position(dofs_idx)
                if isinstance(current_joints, torch.Tensor):
                    current_joints = current_joints.detach().cpu().numpy()
                print(f"  Step {i}: Hand pos = {actual_pos}")
                print(f"           Joint pos = {current_joints}")

        # Settling time
        for i in range(100):
            scene.step()
            if i % 25 == 0:
                actual_pos = end_effector.get_pos()
                current_joints = arm.get_dofs_position(dofs_idx)
                if isinstance(current_joints, torch.Tensor):
                    current_joints = current_joints.detach().cpu().numpy()
                print(f"  Settling {i}: Hand = {actual_pos}, Joints = {current_joints}")


if __name__ == "__main__":
    main()
