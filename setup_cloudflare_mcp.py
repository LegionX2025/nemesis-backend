import os
import json

def update_mcp_config(config_path):
    print(f"Updating {config_path}...")
    
    # Cloudflare and Render MCP Servers
    cloudflare_mcps = {
        "cloudflare": { "url": "https://mcp.cloudflare.com/mcp" },
        "cloudflare-docs": { "url": "https://docs.mcp.cloudflare.com/mcp" },
        "cloudflare-bindings": { "url": "https://bindings.mcp.cloudflare.com/mcp" },
        "cloudflare-builds": { "url": "https://builds.mcp.cloudflare.com/mcp" },
        "cloudflare-observability": { "url": "https://observability.mcp.cloudflare.com/mcp" },
        "render": { 
            "url": "https://mcp.render.com/mcp",
            "env": { "RENDER_API_KEY": "rnd_T0wEMkwXw02mqv0ZyMzeGZvks3Ax" }
        }
    }

    config_dir = os.path.dirname(config_path)
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)

    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"  -> Could not parse existing JSON: {e}")

    # Ensure mcpServers key exists
    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    # Merge in Cloudflare servers
    for key, value in cloudflare_mcps.items():
        config_data["mcpServers"][key] = value
        print(f"  -> Added {key}")

    # Write back
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
    print(f"  -> Saved {config_path}\n")


def main():
    # Target IDEs
    targets = [
        ".vscode/mcp.json",       # GitHub Copilot
        ".cursor/mcp.json",       # Cursor
        ".windsurf/mcp.json"      # Windsurf (fallback local config)
    ]

    for t in targets:
        # We will create it in the user's home directory IDE settings if needed, 
        # but placing it in the workspace folder also works for Cursor/VSCode workspace settings.
        workspace_path = os.path.join(os.getcwd(), t)
        update_mcp_config(workspace_path)
        
    print("✅ Successfully injected Cloudflare MCP servers into IDE configurations!")

if __name__ == "__main__":
    main()
