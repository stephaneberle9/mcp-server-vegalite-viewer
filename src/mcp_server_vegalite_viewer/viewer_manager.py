from fastapi import WebSocket
from typing import List

class ViewerManager:
    def __init__(self):
        self.active_viewer_connections: List[WebSocket] = []
        self.last_visualization = None

    async def connect(self, websocket: WebSocket):
        # Register new viewer client
        await websocket.accept()
        self.active_viewer_connections.append(websocket)

        # Sync new viewer client with latest visualization (if any)
        if self.last_visualization:
            await websocket.send_text(self.last_visualization)

    def disconnect(self, websocket: WebSocket):
        # Unregister viewer client
        if websocket in self.active_viewer_connections:
            self.active_viewer_connections.remove(websocket)

    async def broadcast_visualization(self, visualization: str):
        # Send new visualization to all connected viewer clients
        for connection in self.active_viewer_connections:
            await connection.send_text(visualization)

        # Update latest visualization
        self.last_visualization = visualization