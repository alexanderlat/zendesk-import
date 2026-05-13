import os
import sys
import requests

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ZENDESK_SUBDOMAIN = os.environ.get('ZENDESK_SUBDOMAIN')
ZENDESK_EMAIL = os.environ.get('ZENDESK_EMAIL')
ZENDESK_TOKEN = os.environ.get('ZENDESK_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

print(f'OPENAI_API_KEY aanwezig: {bool(OPENAI_API_KEY)}')
print(f'ZENDESK_SUBDOMAIN aanwezig: {bool(ZENDESK_SUBDOMAIN)}')
print(f'SUPABASE_URL aanwezig: {bool(SUPABASE_URL)}')

if not OPENAI_API_KEY:
    print('FOUT: OPENAI_API_KEY niet gevonden!')
    sys.exit(1)

print('Alle variabelen gevonden, script start...')
