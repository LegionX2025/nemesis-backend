from js import Response

async def on_fetch(request, env):
    # Example showing access to environment variables and bindings
    backend_url = env.BACKEND_API_URL
    
    return Response.new(f"Nemesis Python Worker Active! Backend set to: {backend_url}")
