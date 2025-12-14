import argparse
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from simulation_setup import setup_scene
from simulation_api import SimulationController


# Request model for move endpoint
class MoveRequest(BaseModel):
    x: float
    y: float
    z: float


# Global controller instance
controller = None


# Create FastAPI app
app = FastAPI(title="Genesis Simulation Server")


@app.post("/move")
async def move(request: MoveRequest):
    """
    Queue a move command to the specified position.

    Args:
        request: MoveRequest with x, y, z coordinates

    Returns:
        Status information including queue length
    """
    result = controller.move(request.x, request.y, request.z)
    return result


@app.get("/status")
async def get_status():
    """
    Get current status of the simulation.

    Returns:
        Current task, queue length, and position information
    """
    return controller.get_status()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Genesis Simulation Server",
        "endpoints": {
            "POST /move": "Queue a move command (body: {x, y, z})",
            "GET /status": "Get current simulation status",
        }
    }


def main():
    global controller

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Genesis Simulation HTTP Server")
    parser.add_argument("-v", "--vis", action="store_true", default=False,
                        help="Show visualization window")
    parser.add_argument("--host", type=str, default="0.0.0.0",
                        help="Host to bind the server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port to bind the server to (default: 8000)")
    args = parser.parse_args()

    # Initialize scene
    print("Initializing Genesis scene...")
    scene, arm, dofs_idx, end_effector = setup_scene(show_viewer=args.vis)
    print("Scene initialized successfully")

    # Create and start simulation controller
    print("Starting simulation controller...")
    controller = SimulationController(scene, arm, dofs_idx, end_effector)
    controller.start()
    print("Simulation controller started")

    # Start FastAPI server
    print(f"\nStarting HTTP server on {args.host}:{args.port}")
    print(f"Visualization: {'Enabled' if args.vis else 'Disabled'}")
    print("\nAPI Endpoints:")
    print(f"  POST http://{args.host}:{args.port}/move")
    print(f"  GET  http://{args.host}:{args.port}/status")
    print("\nExample curl command:")
    print(f"  curl -X POST http://{args.host}:{args.port}/move -H 'Content-Type: application/json' -d '{{\"x\": 0.4, \"y\": 0.2, \"z\": 0.3}}'")
    print("\nPress Ctrl+C to stop the server\n")

    try:
        uvicorn.run(app, host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\nShutting down...")
        controller.stop()


if __name__ == "__main__":
    main()
