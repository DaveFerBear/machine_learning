import argparse
import numpy as np
import genesis as gs
import torch


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--vis", action="store_true", default=False)
    args = parser.parse_args()

    ########################## init ##########################
    gs.init(backend=gs.gpu)

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
            euler=(0, 0, -90),
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


    run_sim(scene, arm, dofs_idx)


def run_sim(scene, arm, dofs_idx):
    """
    Task-space control:
    - Define a desired end-effector point p_des(t) in (x, y, z).
    - Use IK to get q_des.
    - Use joint-space PD to track q_des.
    """

    t = 0.0
    dt = scene.sim.dt

    # End-effector link (defined in XML as <body name="hand">)
    end_effector = arm.get_link("hand")

    for step in range(2000):
        # -----------------------------
        # 1) Define p_des(t) in task space
        # -----------------------------

        # Box center and half-extents
        x_center, y_center, z_center = 0.5, 0.3, 0.3
        x_amp = 0.2   # half of 1.0  -> x in [0.0, 1.0]
        y_amp = 0.2   # half of 0.6  -> y in [-0.3, 0.3]
        z_amp = 0.2   # half of 0.6  -> z in [0.0, 0.6]

        # Smooth 3D Lissajous-style motion inside the box
        x = x_center + x_amp * np.sin(0.4 * t)
        y = y_center + y_amp * np.sin(0.7 * t + 0.8)
        z = z_center + z_amp * np.sin(0.9 * t + 1.6)

        p_des = np.array([x, y, z], dtype=np.float32)

        # -----------------------------
        # 2) Run IK: (p_des) -> q_des
        # -----------------------------
        q_des = arm.inverse_kinematics(
            link=end_effector,
            pos=p_des,
            # quat=None  # if needed
        )

        # If Genesis returns a torch tensor on GPU/MPS, move to CPU numpy
        if isinstance(q_des, torch.Tensor):
            q_des = q_des.detach().cpu().numpy()
        else:
            q_des = np.asarray(q_des, dtype=np.float32)

        # -----------------------------
        # 3) Joint-space PD tracking
        # -----------------------------
        arm.set_dofs_position(q_des, dofs_idx)

        scene.step()
        t += dt


if __name__ == "__main__":
    main()
