'''
Business: Настройка webhook для Telegram-бота
Args: event - dict с httpMethod
      context - объект с атрибутами: request_id
Returns: HTTP response со статусом настройки webhook
'''

import json
import os
from typing import Dict, Any
import urllib.request

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
WEBHOOK_URL = 'https://functions.poehali.dev/5c3b7278-e9ff-4484-9925-98c58472a712'

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
    
    if not TELEGRAM_BOT_TOKEN:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN не настроен'}),
            'isBase64Encoded': False
        }
    
    try:
        if method == 'GET':
            info_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo'
            with urllib.request.urlopen(info_url) as response:
                webhook_info = json.loads(response.read().decode('utf-8'))
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(webhook_info, ensure_ascii=False),
                'isBase64Encoded': False
            }
        
        elif method == 'POST':
            set_url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook'
            data = json.dumps({'url': WEBHOOK_URL}).encode('utf-8')
            
            req = urllib.request.Request(
                set_url,
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(result, ensure_ascii=False),
                'isBase64Encoded': False
            }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)}, ensure_ascii=False),
            'isBase64Encoded': False
        }
    
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }
