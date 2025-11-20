#!/usr/bin/env python3
"""
Test direct WebSocket connection to backend.
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection directly to backend."""
    session_id = "test-123"
    
    # Test direct connection with query parameter
    uri = f"ws://13.58.115.166:8000/ws?session_id={session_id}"
    print(f"Testing: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("[OK] WebSocket connected!")
            
            # Wait for connection ready message
            message = await websocket.recv()
            data = json.loads(message)
            print(f"[MSG] Received: {data}")
            
            if data.get('type') == 'connection_ready':
                print("[OK] Connection ready message received!")
            else:
                print(f"[WARN] Unexpected message type: {data.get('type')}")
                
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test path parameter version
    uri2 = f"ws://13.58.115.166:8000/ws/{session_id}"
    print(f"\nTesting path parameter: {uri2}")
    
    try:
        async with websockets.connect(uri2) as websocket:
            print("[OK] WebSocket connected (path parameter)!")
            
            message = await websocket.recv()
            data = json.loads(message)
            print(f"[MSG] Received: {data}")
            
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

    # Test ALB WebSocket (wss)
    alb_uri = f"wss://api.gauntlet3.com/ws/{session_id}"
    print(f"\nTesting ALB WebSocket: {alb_uri}")
    
    try:
        async with websockets.connect(alb_uri) as websocket:
            print("[OK] ALB WebSocket connected!")
            
            # Send registration message
            await websocket.send(json.dumps({
                "type": "register",
                "sessionID": session_id
            }))
            
            message = await websocket.recv()
            data = json.loads(message)
            print(f"[MSG] Received: {data}")
    except Exception as e:
        print(f"[ERROR] ALB connection failed: {e}")

    # (Optional) Keep API Gateway test for debugging
    gateway_uri = "wss://927uc04ep5.execute-api.us-east-2.amazonaws.com/prod"
    print(f"\nTesting legacy API Gateway WebSocket: {gateway_uri}")
    try:
        async with websockets.connect(gateway_uri) as websocket:
            print("[OK] API Gateway WebSocket connected!")
    except Exception as e:
        print(f"[ERROR] API Gateway connection failed (expected): {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())

