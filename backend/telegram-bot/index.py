'''
Business: Telegram-бот для проверки сертификатов по ID и админ-панель для @skzry
Args: event - dict с httpMethod, body от Telegram webhook
      context - объект с атрибутами: request_id, function_name
Returns: HTTP response для Telegram API
'''

import json
import os
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.request
import urllib.parse

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_API_URL = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}'
ADMIN_USERNAME = 'skzry'

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url, cursor_factory=RealDictCursor)

def send_telegram_message(chat_id: int, text: str, parse_mode: str = 'HTML', reply_markup: Optional[Dict] = None):
    if not TELEGRAM_BOT_TOKEN:
        return {'ok': False, 'error': 'No token'}
    
    url = f'{TELEGRAM_API_URL}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    
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

def answer_callback_query(callback_query_id: str, text: str = ''):
    if not TELEGRAM_BOT_TOKEN:
        return {'ok': False}
    
    url = f'{TELEGRAM_API_URL}/answerCallbackQuery'
    data = {'callback_query_id': callback_query_id, 'text': text}
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return {'ok': False}

def edit_message_text(chat_id: int, message_id: int, text: str, parse_mode: str = 'HTML', reply_markup: Optional[Dict] = None):
    if not TELEGRAM_BOT_TOKEN:
        return {'ok': False}
    
    url = f'{TELEGRAM_API_URL}/editMessageText'
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': parse_mode
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return {'ok': False}

def search_certificate(cert_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, owner_name, certificate_url, status, valid_from, valid_until FROM certificates WHERE id = %s", (cert_id,))
    cert = cur.fetchone()
    cur.close()
    conn.close()
    return dict(cert) if cert else None

def get_all_certificates() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, owner_name, certificate_url, status, valid_from, valid_until FROM certificates ORDER BY created_at DESC")
    certs = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(c) for c in certs]

def update_certificate_status(cert_id: str, status: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE certificates SET status = %s WHERE id = %s RETURNING id", (status, cert_id))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result is not None

def delete_certificate(cert_id: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM certificates WHERE id = %s RETURNING id", (cert_id,))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result is not None

def is_admin(username: str) -> bool:
    return username == ADMIN_USERNAME

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
            
            # Обработка callback запросов (нажатия на кнопки)
            if 'callback_query' in update:
                callback = update['callback_query']
                chat_id = callback['message']['chat']['id']
                message_id = callback['message']['message_id']
                callback_data = callback.get('data', '')
                callback_id = callback['id']
                username = callback['from'].get('username', '')
                
                if not is_admin(username):
                    answer_callback_query(callback_id, 'Доступ запрещен')
                    return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
                
                # Главное меню админки
                if callback_data == 'admin_menu':
                    certs = get_all_certificates()
                    menu_text = f"🔧 <b>Админ-панель</b>\n\nВсего сертификатов: {len(certs)}"
                    keyboard = {
                        'inline_keyboard': [
                            [{'text': '📋 Список сертификатов', 'callback_data': 'list_certs'}],
                            [{'text': '🔄 Обновить', 'callback_data': 'admin_menu'}]
                        ]
                    }
                    edit_message_text(chat_id, message_id, menu_text, reply_markup=keyboard)
                    answer_callback_query(callback_id)
                
                # Список сертификатов
                elif callback_data == 'list_certs':
                    certs = get_all_certificates()
                    if not certs:
                        text = "📋 <b>Список сертификатов</b>\n\nСертификаты отсутствуют"
                        keyboard = {'inline_keyboard': [[{'text': '« Назад', 'callback_data': 'admin_menu'}]]}
                        edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                    else:
                        buttons = []
                        for cert in certs[:10]:
                            status_emoji = "✅" if cert['status'] == 'valid' else "❌"
                            buttons.append([{'text': f"{status_emoji} {cert['id']}", 'callback_data': f"cert_{cert['id']}"}])
                        buttons.append([{'text': '« Назад', 'callback_data': 'admin_menu'}])
                        
                        text = f"📋 <b>Список сертификатов</b>\n\nВсего: {len(certs)}\nПоказано: {min(len(certs), 10)}"
                        keyboard = {'inline_keyboard': buttons}
                        edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                    answer_callback_query(callback_id)
                
                # Детали конкретного сертификата
                elif callback_data.startswith('cert_'):
                    cert_id = callback_data.replace('cert_', '')
                    cert = search_certificate(cert_id)
                    
                    if cert:
                        status_emoji = "✅" if cert['status'] == 'valid' else "❌"
                        status_text = "Действительно" if cert['status'] == 'valid' else "Недействительно"
                        
                        date_info = ""
                        if cert.get('valid_from') or cert.get('valid_until'):
                            date_info += "\n"
                            if cert.get('valid_from'):
                                date_info += f"📅 <b>Действителен с:</b> {cert['valid_from']}\n"
                            if cert.get('valid_until'):
                                date_info += f"📅 <b>Действителен до:</b> {cert['valid_until']}\n"
                        
                        text = (
                            f"{status_emoji} <b>Сертификат {cert['id']}</b>\n\n"
                            f"👤 <b>Владелец:</b> {cert['owner_name']}\n"
                            f"📋 <b>Статус:</b> {status_text}{date_info}"
                            f"🔗 <b>Ссылка:</b> {cert['certificate_url']}"
                        )
                        
                        # Кнопка изменения статуса
                        new_status = 'invalid' if cert['status'] == 'valid' else 'valid'
                        status_btn_text = '❌ Сделать недействительным' if cert['status'] == 'valid' else '✅ Сделать действительным'
                        
                        keyboard = {
                            'inline_keyboard': [
                                [{'text': status_btn_text, 'callback_data': f"status_{cert_id}_{new_status}"}],
                                [{'text': '🗑 Удалить', 'callback_data': f"delete_{cert_id}"}],
                                [{'text': '« Назад к списку', 'callback_data': 'list_certs'}]
                            ]
                        }
                        edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                    answer_callback_query(callback_id)
                
                # Изменение статуса
                elif callback_data.startswith('status_'):
                    parts = callback_data.split('_')
                    cert_id = parts[1]
                    new_status = parts[2]
                    
                    if update_certificate_status(cert_id, new_status):
                        answer_callback_query(callback_id, '✅ Статус обновлен')
                        # Обновляем сообщение
                        cert = search_certificate(cert_id)
                        status_emoji = "✅" if cert['status'] == 'valid' else "❌"
                        status_text = "Действительно" if cert['status'] == 'valid' else "Недействительно"
                        
                        date_info = ""
                        if cert.get('valid_from') or cert.get('valid_until'):
                            date_info += "\n"
                            if cert.get('valid_from'):
                                date_info += f"📅 <b>Действителен с:</b> {cert['valid_from']}\n"
                            if cert.get('valid_until'):
                                date_info += f"📅 <b>Действителен до:</b> {cert['valid_until']}\n"
                        
                        text = (
                            f"{status_emoji} <b>Сертификат {cert['id']}</b>\n\n"
                            f"👤 <b>Владелец:</b> {cert['owner_name']}\n"
                            f"📋 <b>Статус:</b> {status_text}{date_info}"
                            f"🔗 <b>Ссылка:</b> {cert['certificate_url']}"
                        )
                        
                        new_status_toggle = 'invalid' if cert['status'] == 'valid' else 'valid'
                        status_btn_text = '❌ Сделать недействительным' if cert['status'] == 'valid' else '✅ Сделать действительным'
                        
                        keyboard = {
                            'inline_keyboard': [
                                [{'text': status_btn_text, 'callback_data': f"status_{cert_id}_{new_status_toggle}"}],
                                [{'text': '🗑 Удалить', 'callback_data': f"delete_{cert_id}"}],
                                [{'text': '« Назад к списку', 'callback_data': 'list_certs'}]
                            ]
                        }
                        edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                    else:
                        answer_callback_query(callback_id, '❌ Ошибка обновления')
                
                # Удаление сертификата
                elif callback_data.startswith('delete_'):
                    cert_id = callback_data.replace('delete_', '')
                    if delete_certificate(cert_id):
                        answer_callback_query(callback_id, '✅ Сертификат удален')
                        text = f"✅ <b>Сертификат {cert_id} удален</b>"
                        keyboard = {'inline_keyboard': [[{'text': '« К списку', 'callback_data': 'list_certs'}]]}
                        edit_message_text(chat_id, message_id, text, reply_markup=keyboard)
                    else:
                        answer_callback_query(callback_id, '❌ Ошибка удаления')
                
                return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
            
            # Обработка текстовых сообщений
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '').strip()
            username = message.get('from', {}).get('username', '')
            
            if not chat_id:
                return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
            
            # Команда /start
            if text.startswith('/start'):
                welcome_text = (
                    "🔐 <b>Добро пожаловать в систему верификации сертификатов!</b>\n\n"
                    "Отправьте мне ID сертификата для проверки.\n"
                    "Например: <code>CERT-</code>"
                )
                send_telegram_message(chat_id, welcome_text)
            
            # Команда /admin
            elif text.startswith('/admin'):
                if not is_admin(username):
                    send_telegram_message(chat_id, "❌ <b>Доступ запрещен</b>\n\nАдмин-панель доступна только для @skzry")
                else:
                    certs = get_all_certificates()
                    menu_text = f"🔧 <b>Админ-панель</b>\n\nВсего сертификатов: {len(certs)}"
                    keyboard = {
                        'inline_keyboard': [
                            [{'text': '📋 Список сертификатов', 'callback_data': 'list_certs'}],
                            [{'text': '🔄 Обновить', 'callback_data': 'admin_menu'}]
                        ]
                    }
                    send_telegram_message(chat_id, menu_text, reply_markup=keyboard)
            
            # Поиск по ID
            elif text:
                cert = search_certificate(text.upper())
                
                if cert:
                    status_emoji = "✅" if cert.get('status') == 'valid' else "❌"
                    status_text = "Действительно" if cert.get('status') == 'valid' else "Недействительно"
                    
                    date_info = ""
                    if cert.get('valid_from') or cert.get('valid_until'):
                        date_info += "\n"
                        if cert.get('valid_from'):
                            date_info += f"📅 <b>Действителен с:</b> {cert['valid_from']}\n"
                        if cert.get('valid_until'):
                            date_info += f"📅 <b>Действителен до:</b> {cert['valid_until']}\n"
                    
                    result_text = (
                        f"{status_emoji} <b>ID {cert['id']} найден!</b>\n\n"
                        f"👤 <b>Принадлежит:</b> {cert['owner_name']}\n"
                        f"📋 <b>Статус:</b> {status_text}{date_info}\n"
                        f"🔗 <b>Ссылка на просмотр:</b>\n{cert['certificate_url']}"
                    )
                    send_telegram_message(chat_id, result_text)
                else:
                    error_text = f"❌ <b>Сертификат с ID {text.upper()} не найден</b>"
                    send_telegram_message(chat_id, error_text)
            
            return {'statusCode': 200, 'headers': headers, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
            
        except Exception as e:
            return {'statusCode': 500, 'headers': headers, 'body': json.dumps({'error': str(e)}), 'isBase64Encoded': False}
    
    return {'statusCode': 405, 'headers': headers, 'body': json.dumps({'error': 'Method not allowed'}), 'isBase64Encoded': False}