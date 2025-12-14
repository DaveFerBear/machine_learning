import argparse
import numpy as np
import genesis as gs


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
    plane = scene.add_entity(
        gs.morphs.Plane(),
    )

    # Our simple 3-DOF primitive arm
    arm = scene.add_entity(
        gs.morphs.MJCF(
            file="./robots/dummy-3dof.xml",
            pos=(0.0, 0.0, 0.0),
            euler=(0, 0, 0),
        ),
    )

    # Optional cube to poke at / collide with
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

    # Positional gains (stiffness)
    arm.set_dofs_kp(
        kp=np.array([200.0, 200.0, 150.0]),
        dofs_idx_local=dofs_idx,
    )

    # Velocity gains (damping)
    arm.set_dofs_kv(
        kv=np.array([20.0, 20.0, 15.0]),
        dofs_idx_local=dofs_idx,
    )

    # Force limits (just some reasonable numbers)
    arm.set_dofs_force_range(
        lower=np.array([-50.0, -50.0, -30.0]),
        upper=np.array([50.0, 50.0, 30.0]),
        dofs_idx_local=dofs_idx,
    )

    run_sim(scene, arm, dofs_idx)


def run_sim(scene, arm, dofs_idx):
    """
    Simple demo: wave the 3 joints with sinusoids.
    This is just to verify the arm behaves and collisions look sane.
    """
    t = 0.0
    dt = scene.sim.dt

    # Get end-effector link if you want to inspect its pose later
    end_effector = arm.get_link("hand")

    for step in range(2000):
        # Time-varying joint targets (in *radians* since Genesis uses radians)
        # The MJCF used degrees for ranges, but control is in radians.
        q_des = np.array([
            0.5 * np.sin(0.5 * t),      # joint1
            0.5 * np.sin(0.7 * t + 1),  # joint2
            0.5 * np.sin(0.9 * t + 2),  # joint3
        ])

        arm.set_dofs_position(q_des, dofs_idx)
        scene.step()
        t += dt

        # If you want to query ee pose:
        # ee_pos = end_effector.get_com()   # or .get_pose(), depending on API version

    # Let it settle a bit at the end
    for _ in range(200):
        scene.step()


if __name__ == "__main__":
    main()
