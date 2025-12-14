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
        show_viewer=args.vis,
    )

    ########################## entities ##########################
    plane = scene.add_entity(gs.morphs.Plane())

    # Simple 3-DOF primitive arm
    arm = scene.add_entity(
        gs.morphs.MJCF(
            file="./robots/dummy-3dof.xml",
            pos=(0.0, 0.0, 0.0),
            euler=(0, 0, 0),
        ),
    )

    cube = scene.add_entity(
        gs.morphs.Box(
            size=(0.04, 0.04, 0.04),
            pos=(0.6, 0.0, 0.02),
        ),
    )

    ########################## build ##########################
    scene.build()

    # 3 joints only
    jnt_names = ["joint1", "joint2", "joint3"]
    dofs_idx = [arm.get_joint(name).dof_idx_local for name in jnt_names]

    # Gains (PD in joint space, but targets come from IK)
    arm.set_dofs_kp(
        kp=np.array([200.0, 200.0, 150.0]),
        dofs_idx_local=dofs_idx,
    )
    arm.set_dofs_kv(
        kv=np.array([20.0, 20.0, 15.0]),
        dofs_idx_local=dofs_idx,
    )
    arm.set_dofs_force_range(
        lower=np.array([-50.0, -50.0, -30.0]),
        upper=np.array([50.0, 50.0, 30.0]),
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
        radius = 0.4
        center_x = 0.5
        center_y = 0.0
        z_const = 0.0

        x = center_x + radius * 0.3 * np.cos(0.5 * t)
        y = center_y + radius * 0.3 * np.sin(0.5 * t)
        z = z_const

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
