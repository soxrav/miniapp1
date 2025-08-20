import socket
import threading
import json
import time
from datetime import datetime
import os
import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock


class PhoneChatServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.clients = {}
        self.messages = []
        self.running = False
        self.server_socket = None

    def get_local_ip(self):
        """Получаем IP адрес телефона в локальной сети"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "192.168.43.1"  # Стандартный для hotspot

    def handle_client(self, client_socket, address):
        print(f"Подключение от {address}")
        username = f"User{address[1]}"
        self.clients[address] = {'socket': client_socket, 'username': username}

        try:
            while self.running:
                try:
                    data = client_socket.recv(1024).decode('utf-8')
                    if not data:
                        break

                    message = json.loads(data)
                    if message['type'] == 'message':
                        msg_text = f"{username}: {message['text']}"
                        self.messages.append(msg_text)
                        self.broadcast_message(msg_text, exclude=address)

                except Exception as e:
                    print(f"Ошибка: {e}")
                    break

        except Exception as e:
            print(f"Ошибка с клиентом {address}: {e}")
        finally:
            if address in self.clients:
                del self.clients[address]
            client_socket.close()
            print(f"Отключение от {address}")

    def broadcast_message(self, message, exclude=None):
        """Отправляем сообщение всем клиентам"""
        for addr, client in list(self.clients.items()):
            if addr != exclude:
                try:
                    msg_data = json.dumps({
                        'type': 'message',
                        'text': message,
                        'timestamp': time.time()
                    })
                    client['socket'].send(msg_data.encode('utf-8'))
                except:
                    del self.clients[addr]

    def start_server(self):
        """Запускаем сервер"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            print(f"Сервер запущен на {self.get_local_ip()}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address),
                        daemon=True
                    )
                    client_thread.start()
                except:
                    break

        except Exception as e:
            print(f"Ошибка сервера: {e}")
        finally:
            self.stop_server()

    def stop_server(self):
        """Останавливаем сервер"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client in self.clients.values():
            client['socket'].close()
        self.clients.clear()


class PhoneChatClient:
    def __init__(self, server_ip, port=8888):
        self.server_ip = server_ip
        self.port = port
        self.socket = None
        self.running = False
        self.username = f"User{os.getpid()}"

    def connect(self):
        """Подключаемся к серверу"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.port))
            self.running = True
            return True
        except Exception as e:
            print(f"Ошибка подключения: {e}")
            return False

    def send_message(self, text):
        """Отправляем сообщение на сервер"""
        try:
            message = {
                'type': 'message',
                'text': text,
                'username': self.username
            }
            self.socket.send(json.dumps(message).encode('utf-8'))
            return True
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return False

    def receive_messages(self, callback):
        """Получаем сообщения от сервера"""
        while self.running:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if data:
                    message = json.loads(data)
                    callback(message['text'])
            except:
                break

    def disconnect(self):
        """Отключаемся от сервера"""
        self.running = False
        if self.socket:
            self.socket.close()


class ChatApp(App):
    def build(self):
        self.is_server = False
        self.server = None
        self.client = None
        self.messages = []

        # Основной layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Кнопки выбора режима
        mode_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        self.server_btn = Button(text='Создать сервер', on_press=self.start_server_mode)
        self.client_btn = Button(text='Подключиться', on_press=self.start_client_mode)
        mode_layout.add_widget(self.server_btn)
        mode_layout.add_widget(self.client_btn)

        # Поле для IP
        self.ip_input = TextInput(
            text='192.168.43.1',
            size_hint_y=0.1,
            hint_text='IP адрес сервера'
        )

        # Поле сообщений
        self.chat_scroll = ScrollView(size_hint_y=0.6)
        self.chat_label = Label(
            text='Добро пожаловать в локальный чат!\n',
            size_hint_y=None,
            text_size=(Window.width - 20, None)
        )
        self.chat_label.bind(texture_size=self.chat_label.setter('size'))
        self.chat_scroll.add_widget(self.chat_label)

        # Поле ввода сообщения
        self.message_input = TextInput(
            size_hint_y=0.1,
            hint_text='Введите сообщение...',
            multiline=False
        )
        self.message_input.bind(on_text_validate=self.send_message)

        # Кнопка отправки
        self.send_btn = Button(
            text='Отправить',
            size_hint_y=0.1,
            on_press=self.send_message
        )

        layout.add_widget(mode_layout)
        layout.add_widget(self.ip_input)
        layout.add_widget(self.chat_scroll)
        layout.add_widget(self.message_input)
        layout.add_widget(self.send_btn)

        return layout

    def start_server_mode(self, instance):
        """Запускаем сервер на телефоне"""
        if self.is_server:
            return

        self.is_server = True
        self.server = PhoneChatServer()
        server_thread = threading.Thread(target=self.server.start_server, daemon=True)
        server_thread.start()

        self.add_message("Вы создали сервер чата!")
        self.add_message(f"Ваш IP: {self.server.get_local_ip()}")
        self.add_message("Другие могут подключиться к вам")

    def start_client_mode(self, instance):
        """Подключаемся к серверу"""
        if self.client:
            return

        server_ip = self.ip_input.text
        self.client = PhoneChatClient(server_ip)

        if self.client.connect():
            self.add_message(f"Подключились к серверу {server_ip}")

            # Запускаем получение сообщений
            receive_thread = threading.Thread(
                target=self.client.receive_messages,
                args=(self.add_message,),
                daemon=True
            )
            receive_thread.start()
        else:
            self.add_message("Ошибка подключения к серверу")

    def send_message(self, instance):
        """Отправляем сообщение"""
        text = self.message_input.text.strip()
        if not text:
            return

        if self.client and self.client.running:
            if self.client.send_message(text):
                self.add_message(f"Вы: {text}")
                self.message_input.text = ''
        elif self.is_server:
            self.add_message(f"Вы: {text}")
            if self.server:
                self.server.broadcast_message(f"Вы: {text}")
            self.message_input.text = ''
        else:
            self.add_message("Сначала подключитесь к серверу")

    def add_message(self, message):
        """Добавляем сообщение в чат"""
        Clock.schedule_once(lambda dt: self._add_message_threadsafe(message), 0)

    def _add_message_threadsafe(self, message):
        """Безопасное добавление сообщения из другого потока"""
        timestamp = datetime.now().strftime("%H:%M")
        formatted_msg = f"[{timestamp}] {message}\n"
        self.messages.append(formatted_msg)
        self.chat_label.text = ''.join(self.messages[-20:])  # Последние 20 сообщений
        self.chat_scroll.scroll_to(self.chat_label)

    def on_stop(self):
        """При закрытии приложения"""
        if self.server:
            self.server.stop_server()
        if self.client:
            self.client.disconnect()


if __name__ == "__main__":
    # Для работы на Android через Termux
    try:
        ChatApp().run()
    except Exception as e:
        print(f"Ошибка: {e}")
        input("Нажмите Enter для выхода...")