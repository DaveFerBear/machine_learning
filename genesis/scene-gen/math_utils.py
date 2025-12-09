import numpy as np

def random_rotation():
    """Generate random Euler angles for initial rotation."""
    return (np.random.uniform(0, 360), np.random.uniform(0, 360), np.random.uniform(0, 360))


def euler_to_quat(euler):
    """Convert Euler angles (degrees) to quaternion [w, x, y, z]."""
    # Convert to radians
    roll, pitch, yaw = np.radians(euler)

    # Convert to quaternion
    cy = np.cos(yaw * 0.5)
    sy = np.sin(yaw * 0.5)
    cp = np.cos(pitch * 0.5)
    sp = np.sin(pitch * 0.5)
    cr = np.cos(roll * 0.5)
    sr = np.sin(roll * 0.5)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return np.array([w, x, y, z])


def random_position(x_range=(0, 1), y_range=(0, 0.6), z_range=(0.15, 0.4)):
    """Generate random position within specified ranges."""
    return (
        np.random.uniform(*x_range),
        np.random.uniform(*y_range),
        np.random.uniform(*z_range)
    )


def random_camera_config():
    """Generate random camera configuration."""
    resolutions = [(1024, 540), (2048, 1080), (3840, 2160)]
    fov_options = [80, 85, 90, 95, 100]
    fov = np.random.choice(fov_options)
    res = resolutions[np.random.randint(0, len(resolutions))]
    return {"fov": fov, "res": res}


def get_entity_bbox(entity, position):
    """
    Get axis-aligned bounding box for an entity.

    Args:
        entity: Genesis entity object
        position: [x, y, z] position of entity (used as fallback)

    Returns:
        tuple: (bbox_min, bbox_max) as lists [x, y, z]
    """
    if hasattr(entity, 'geoms') and len(entity.geoms) > 0:
        geom = entity.geoms[0]
        # Get AABB: returns [[x_min, y_min, z_min], [x_max, y_max, z_max]]
        aabb = geom.get_AABB()

        # Convert to list (handle both numpy arrays and torch tensors)
        if hasattr(aabb, 'cpu'):
            # PyTorch tensor - convert to numpy then list
            aabb_np = aabb.cpu().numpy()
            bbox_min = aabb_np[0].tolist()
            bbox_max = aabb_np[1].tolist()
        else:
            # NumPy array or already a list
            bbox_min = aabb[0].tolist() if hasattr(aabb[0], 'tolist') else list(aabb[0])
            bbox_max = aabb[1].tolist() if hasattr(aabb[1], 'tolist') else list(aabb[1])
    else:
        # Fallback for entities without geoms
        bbox_size = 0.05
        bbox_min = [position[0] - bbox_size, position[1] - bbox_size, position[2] - bbox_size]
        bbox_max = [position[0] + bbox_size, position[1] + bbox_size, position[2] + bbox_size]

    return bbox_min, bbox_max