# The Render API – Render Docs
Source: https://docs.render.com/api

The Render API – Render Docs
Search
Ask AI
Sign In
Get Started
The Render API
Manage your Render infrastructure programmatically.
Open the API reference
Render provides a public REST API for managing your services and other resources programmatically.
The API supports almost all of the same functionality available in the
Render Dashboard
. It includes endpoints for managing:
Services and datastores
Deploys
Environment groups
Blueprints
Metrics and logs
Projects and environments
Custom domains
One-off jobs
Audit logs
Additional account settings
To request new API functionality, please
submit a feature request
.
Setup
1. Create an API key
All Render API requests require authentication via API key. You create and manage API keys from your
Account Settings page
in the Render Dashboard:
An API key is displayed in full only when it's created:
API keys are secret credentials!
Don't publicly post your API key, commit it to version control, or otherwise share it with anyone outside your organization. If you believe an API key has been compromised, revoke it in the Render Dashboard and create a new one.
2. Make your first request
To test your API key, let's make a quick
curl
request to list your services.
Run the following in your terminal after replacing
{{render_api_token_goes_here}}
with your API key:
If your API key is valid, this request to the
List services
endpoint returns a
200
response with your service details in a JSON array.
API reference
Open the API reference
for a comprehensive list of supported endpoints. The reference is interactive, and it provides example usage in multiple programming languages.
OpenAPI spec
The Render API is described by an OpenAPI 3.0 spec. The spec is available in JSON format at the following URL:
You can use this spec to generate custom clients and with other tooling.
Render's OpenAPI spec is subject to change.
The API itself will maintain backward compatibility, but details of the describing spec (such as names for endpoints and tags) might change over time. This might affect custom clients or other tools that rely on the spec.
Copy page
The Render API
Setup
1. Create an API key
2. Make your first request
API reference
OpenAPI spec
bash
Copy to clipboard
curl
--request
GET
\
--url
'https://api.render.com/v1/services?limit=20'
\
--header
'Accept: application/json'
\
--header
'Authorization: Bearer {{render_api_token_goes_here}}'
plaintext
Copy to clipboard
https://api-docs.render.com/openapi/render-public-api-1.json