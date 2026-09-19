import urllib.request, json
req = urllib.request.Request('https://integrate.api.nvidia.com/v1/models', headers={'Authorization': 'Bearer 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'})
res = urllib.request.urlopen(req)
data = json.loads(res.read())
print('\n'.join(m['id'] for m in data['data'] if 'vision' in m['id'].lower() or 'phi' in m['id'].lower() or 'llama' in m['id'].lower() or 'nemotron' in m['id'].lower()))
