'''
Business: Telegram-бот для проверки сертификатов по ID через команду /start
Args: event - dict с httpMethod, body от Telegram webhook
      context - объект с атрибутами: request_id, function_name
Returns: HTTP response для Telegram API
'''

import json
import os
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.request
import urllib.parse

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def send_telegram_message(chat_id: int, text: str, parse_mode: str = 'HTML'):
    if not TELEGRAM_BOT_TOKEN:
        return {'ok': False, 'error': 'No token'}
    
    url = f'{TELEGRAM_API_URL}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def search_certificate(cert_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, owner_name, certificate_url, status FROM certificates WHERE id = %s", (cert_id,))
    cert = cur.fetchone()
    cur.close()
    conn.close()
    return dict(cert) if cert else None

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    
    if method == 'POST':
        try:
            body_str = event.get('body', '{}')
            update = json.loads(body_str)
            
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '').strip()
            
            if not chat_id:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            if text.startswith('/start'):
                welcome_text = (
                    "🔐 <b>Добро пожаловать в систему верификации сертификатов!</b>\n\n"
                    "Отправьте мне ID сертификата для проверки.\n"
                    "Например: <code>CERT-</code>"
                )
                send_telegram_message(chat_id, welcome_text)
            
            elif text:
                cert = search_certificate(text.upper())
                
                if cert:
                    status_emoji = "✅" if cert.get('status') == 'valid' else "❌"
                    status_text = "Действительно" if cert.get('status') == 'valid' else "Недействительно"
                    
                    result_text = (
                        f"{status_emoji} <b>ID {cert['id']} найден!</b>\n\n"
                        f"👤 <b>Принадлежит:</b> {cert['owner_name']}\n"
                        f"📋 <b>Статус:</b> {status_text}\n\n"
                        f"🔗 <b>Ссылка на просмотр:</b>\n{cert['certificate_url']}"
                    )
                    send_telegram_message(chat_id, result_text)
                else:
                    error_text = f"❌ <b>Сертификат с ID {text.upper()} не найден</b>"
                    send_telegram_message(chat_id, error_text)
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
            
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'error': str(e)}),
                'isBase64Encoded': False
            }
    
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }