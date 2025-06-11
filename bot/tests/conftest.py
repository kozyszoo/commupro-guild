#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest設定とフィクスチャ
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch
import asyncio

# テスト用にsrcパスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_env_vars():
    """テスト用環境変数のモック"""
    test_env = {
        'DISCORD_BOT_TOKEN_MIYA': 'test_token_miya',
        'DISCORD_BOT_TOKEN_EVE': 'test_token_eve',
        'GCP_PROJECT_ID': 'test-project',
        'GCP_LOCATION': 'us-central1',
        'FIREBASE_SERVICE_ACCOUNT': '{"type":"service_account","project_id":"test"}',
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env

@pytest.fixture
def mock_firebase():
    """Firebase Admin SDKのモック"""
    with patch('firebase_admin.initialize_app') as mock_init, \
         patch('firebase_admin.firestore.client') as mock_client:
        
        # モッククライアントの設定
        mock_db = Mock()
        mock_client.return_value = mock_db
        
        yield {
            'init': mock_init,
            'client': mock_client,
            'db': mock_db
        }

@pytest.fixture
def mock_vertex_ai():
    """Vertex AIのモック"""
    with patch('google.cloud.aiplatform.init') as mock_init, \
         patch('vertexai.generative_models.GenerativeModel') as mock_model:
        
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.text = "テスト応答です。"
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        yield {
            'init': mock_init,
            'model': mock_model,
            'response': mock_response
        }

@pytest.fixture
def mock_discord():
    """Discord.pyのモック"""
    with patch('discord.Client') as mock_client, \
         patch('discord.Intents') as mock_intents:
        
        # モッククライアントの設定
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        yield {
            'client': mock_client,
            'intents': mock_intents,
            'instance': mock_client_instance
        }

@pytest.fixture
def sample_firestore_data():
    """テスト用のFirestoreデータサンプル"""
    return {
        'users': [
            {
                'id': 'user1',
                'username': 'testuser1',
                'guild_id': 'guild1',
                'joined_at': '2024-01-01T00:00:00Z'
            },
            {
                'id': 'user2',
                'username': 'testuser2',
                'guild_id': 'guild1',
                'joined_at': '2024-01-02T00:00:00Z'
            }
        ],
        'guilds': [
            {
                'id': 'guild1',
                'name': 'Test Guild',
                'member_count': 100
            }
        ],
        'topics': [
            {
                'id': 'topic1',
                'title': 'Test Topic',
                'guild_id': 'guild1',
                'created_at': '2024-01-01T00:00:00Z'
            }
        ]
    }

@pytest.fixture(autouse=True)
def setup_test_environment(mock_env_vars):
    """各テストの前に自動的に実行される環境設定"""
    # テスト用ディレクトリの作成
    os.makedirs('test_output', exist_ok=True)
    
    yield
    
    # クリーンアップ（必要に応じて）
    pass