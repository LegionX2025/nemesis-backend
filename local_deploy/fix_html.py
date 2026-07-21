import re

filepath = r'c:\Users\LEGIONX\Downloads\cases\local_deploy\frontend\nemesis_id_new.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Restore dynamic-data-tbody which was accidentally overwritten by multi_replace
# I will find the table headers for TX history and make sure the tbody is correct.

# 1. Fix TX History TBody
tx_table_pattern = re.compile(r'(<th>Risk & Alerts</th>\s*</tr>\s*</thead>\s*)<tbody>\s*<tr><td colspan="6"[^>]*>No dark web threat intelligence reports found\.</td></tr>\s*</tbody>', re.IGNORECASE)
content = tx_table_pattern.sub(r'\1<tbody class="dynamic-data-tbody">\n<tr><td colspan="6" class="text-center py-4 text-slate-500"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Fetching Live Data...</td></tr>\n</tbody>', content)

# 2. Fix Clustered Wallets TBody
cluster_pattern = re.compile(r'(<th>Chain</th>\s*</tr>\s*</thead>\s*)<tbody class="font-mono text-xs">\s*<tr><td colspan="5"[^>]*>No multi-chain asset flows detected\.</td></tr>\s*</tbody>', re.IGNORECASE)
content = cluster_pattern.sub(r'\1<tbody class="font-mono text-xs" id="clustered-wallets-tbody">\n<tr><td colspan="5" class="text-center py-4 text-slate-500">Awaiting graph clustering analysis.</td></tr>\n</tbody>', content)

# 3. Clean any remaining hardcoded mock rows that look like <tr><td>...</td></tr> inside tables that are NOT dynamic
mock_data_pattern = re.compile(r'<!-- MOCK DATA STRIPPED - WAITING FOR API FETCH -->\s*<tr><td colspan="\d+" class="text-center py-4 text-slate-600"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Fetching Live Data...</td></tr>')
content = mock_data_pattern.sub(r'<tr><td colspan="10" class="text-center py-4 text-slate-500">No data found in intelligence cache.</td></tr>', content)

# Remove all bg-slate-900, border-slate-700 to force enterprise theme
classes_to_remove = ['bg-slate-900', 'bg-slate-800', 'text-slate-100', 'text-slate-200', 'border-slate-800', 'border-slate-700']
for cls in classes_to_remove:
    content = re.sub(r'\b' + cls + r'\b', '', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("nemesis_id_new.html fixed!")
