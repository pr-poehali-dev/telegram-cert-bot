'''
Business: API для управления сертификатами и интеграции с Telegram-ботом
Args: event - dict с httpMethod, body, queryStringParameters
      context - объект с атрибутами: request_id, function_name
Returns: HTTP response dict с данными сертификатов
'''

import json
import os
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'GET')
    
    # Handle CORS OPTIONS
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Admin-Token',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    }
    
    # GET /certificates?id=CERT-XXX - поиск по ID
    if method == 'GET':
        params = event.get('queryStringParameters') or {}
        cert_id = params.get('id', '').strip()
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        if cert_id:
            cur.execute("SELECT id, owner_name, certificate_url, status, valid_from, valid_until, created_at FROM certificates WHERE id = %s", (cert_id,))
            cert = cur.fetchone()
            cur.close()
            conn.close()
            
            if cert:
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        'found': True,
                        'certificate': dict(cert)
                    }, default=str),
                    'isBase64Encoded': False
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': headers,
                    'body': json.dumps({'found': False, 'message': 'Сертификат не найден'}),
                    'isBase64Encoded': False
                }
        else:
            # Получить все сертификаты
            cur.execute("SELECT id, owner_name, certificate_url, status, valid_from, valid_until, created_at FROM certificates ORDER BY created_at DESC")
            certs = cur.fetchall()
            cur.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'certificates': [dict(c) for c in certs]}, default=str),
                'isBase64Encoded': False
            }
    
    # POST /certificates - добавить новый сертификат
    if method == 'POST':
        request_headers = event.get('headers', {})
        admin_token = request_headers.get('X-Admin-Token') or request_headers.get('x-admin-token')
        
        # Проверка прав админа (для простоты проверяем username)
        if admin_token != 'skzry':
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'error': 'Доступ запрещен'}),
                'isBase64Encoded': False
            }
        
        body_data = json.loads(event.get('body', '{}'))
        cert_id = body_data.get('id', '').strip()
        owner_name = body_data.get('owner_name', '').strip()
        certificate_url = body_data.get('certificate_url', '').strip()
        status = body_data.get('status', 'valid')
        valid_from = body_data.get('valid_from')
        valid_until = body_data.get('valid_until')
        
        if not cert_id or not owner_name or not certificate_url:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Заполните все поля'}),
                'isBase64Encoded': False
            }
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO certificates (id, owner_name, certificate_url, status, valid_from, valid_until) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING RETURNING id",
            (cert_id, owner_name, certificate_url, status, valid_from, valid_until)
        )
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if result:
            return {
                'statusCode': 201,
                'headers': headers,
                'body': json.dumps({'success': True, 'message': 'Сертификат добавлен'}),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 409,
                'headers': headers,
                'body': json.dumps({'error': 'Сертификат с таким ID уже существует'}),
                'isBase64Encoded': False
            }
    
    # DELETE /certificates?id=CERT-XXX - удалить сертификат
    if method == 'DELETE':
        request_headers = event.get('headers', {})
        admin_token = request_headers.get('X-Admin-Token') or request_headers.get('x-admin-token')
        
        if admin_token != 'skzry':
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'error': 'Доступ запрещен'}),
                'isBase64Encoded': False
            }
        
        params = event.get('queryStringParameters') or {}
        cert_id = params.get('id', '').strip()
        
        if not cert_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'ID не указан'}),
                'isBase64Encoded': False
            }
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM certificates WHERE id = %s RETURNING id", (cert_id,))
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if result:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True, 'message': 'Сертификат удален'}),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Сертификат не найден'}),
                'isBase64Encoded': False
            }
    
    # PUT /certificates - обновить сертификат
    if method == 'PUT':
        request_headers = event.get('headers', {})
        admin_token = request_headers.get('X-Admin-Token') or request_headers.get('x-admin-token')
        
        if admin_token != 'skzry':
            return {
                'statusCode': 403,
                'headers': headers,
                'body': json.dumps({'error': 'Доступ запрещен'}),
                'isBase64Encoded': False
            }
        
        body_data = json.loads(event.get('body', '{}'))
        cert_id = body_data.get('id', '').strip()
        
        if not cert_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'ID не указан'}),
                'isBase64Encoded': False
            }
        
        # Собираем поля для обновления
        update_fields = []
        update_values = []
        
        if 'status' in body_data and body_data['status'] in ['valid', 'invalid']:
            update_fields.append('status = %s')
            update_values.append(body_data['status'])
        
        if 'owner_name' in body_data:
            update_fields.append('owner_name = %s')
            update_values.append(body_data['owner_name'].strip())
        
        if 'certificate_url' in body_data:
            update_fields.append('certificate_url = %s')
            update_values.append(body_data['certificate_url'].strip())
        
        if 'valid_from' in body_data:
            update_fields.append('valid_from = %s')
            update_values.append(body_data['valid_from'])
        
        if 'valid_until' in body_data:
            update_fields.append('valid_until = %s')
            update_values.append(body_data['valid_until'])
        
        if not update_fields:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Нет полей для обновления'}),
                'isBase64Encoded': False
            }
        
        update_values.append(cert_id)
        
        conn = get_db_connection()
        cur = conn.cursor()
        query = f"UPDATE certificates SET {', '.join(update_fields)} WHERE id = %s RETURNING id"
        cur.execute(query, update_values)
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        
        if result:
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'success': True, 'message': 'Сертификат обновлен'}),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Сертификат не найден'}),
                'isBase64Encoded': False
            }
    
    return {
        'statusCode': 405,
        'headers': headers,
        'body': json.dumps({'error': 'Метод не поддерживается'}),
        'isBase64Encoded': False
    }