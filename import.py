import os
import requests
from openai import OpenAI

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
ZENDESK_SUBDOMAIN = os.environ.get('ZENDESK_SUBDOMAIN')
ZENDESK_EMAIL = os.environ.get('ZENDESK_EMAIL')
ZENDESK_TOKEN = os.environ.get('ZENDESK_TOKEN_IMPORT')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(tekst):
    response = openai_client.embeddings.create(
        input=tekst[:8000],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def sla_op_in_supabase(zendesk_id, subject, vraag, antwoord, embedding):
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    data = {
        'zendesk_id': str(zendesk_id),
        'subject': subject,
        'vraag': vraag,
        'antwoord': antwoord,
        'embedding': embedding
    }
    response = requests.post(
        f'{SUPABASE_URL}/rest/v1/tickets',
        headers=headers,
        json=data
    )
    if response.status_code != 201:
        print(f'Supabase fout: {response.status_code} - {response.text}', flush=True)
    return response.status_code

def get_agent_ids():
    auth_string = f'{ZENDESK_EMAIL}/token'
    auth = (auth_string, ZENDESK_TOKEN)
    agent_ids = []
    for role in ['agent', 'admin']:
        url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/users.json?role={role}&per_page=100'
        while url:
            response = requests.get(url, auth=auth)
            data = response.json()
            agent_ids += [user['id'] for user in data.get('users', [])]
            url = data.get('next_page')
    print(f'Gevonden agents + admins: {len(agent_ids)}', flush=True)
    return agent_ids

def importeer_tickets():
    auth = (f'{ZENDESK_EMAIL}/token', ZENDESK_TOKEN)
    agent_ids = get_agent_ids()
    print(f'Gevonden agents: {len(agent_ids)}', flush=True)
    url = f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/incremental/tickets.json?start_time=1704067200'
    totaal = 0
    opgeslagen = 0
    while url:
        response = requests.get(url, auth=auth)
        data = response.json()
        tickets = data.get('tickets', [])
        print(f'Pagina opgehaald: {len(tickets)} tickets', flush=True)
        for ticket in tickets:
            if ticket.get('status') != 'pending':
                continue
            totaal += 1
            ticket_id = ticket['id']
            subject = ticket.get('subject', '')
            comments_response = requests.get(
                f'https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}/comments.json',
                auth=auth
            )
            comments = comments_response.json().get('comments', [])
            publieke_comments = [c for c in comments if c.get('public')]
            if len(publieke_comments) < 2:
                continue
            klant_bericht = publieke_comments[0].get('body', '') or ''
            agent_antwoord = None
            for comment in publieke_comments[1:]:
                if comment.get('author_id') in agent_ids:
                    agent_antwoord = comment.get('body', '') or ''
                    break
            if not agent_antwoord:
                continue
            tekst_voor_embedding = f'Onderwerp: {subject}\nVraag: {klant_bericht[:500]}'
            embedding = get_embedding(tekst_voor_embedding)
            status = sla_op_in_supabase(
                ticket_id, subject,
                klant_bericht[:1000],
                agent_antwoord[:1000],
                embedding
            )
            if status == 201:
                opgeslagen += 1
                print(f'Opgeslagen: ticket {ticket_id} ({opgeslagen} totaal)', flush=True)
            else:
                print(f'Fout bij opslaan ticket {ticket_id}: status {status}', flush=True)
        if data.get('end_of_stream'):
            print(f'Klaar! {totaal} tickets verwerkt, {opgeslagen} opgeslagen.', flush=True)
            break
        url = data.get('next_page')
        print(f'Volgende pagina... ({totaal} verwerkt, {opgeslagen} opgeslagen)', flush=True)

importeer_tickets()
