#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deploy.py
Discord にゃんこエージェント - デプロイスクリプト

各種デプロイ方法を統合したスクリプト
- 通常デプロイ
- GCPデプロイ
- 個別デプロイ
"""

import os
import sys
import subprocess
import argparse
from typing import Optional, List, Dict
import yaml
import json
from pathlib import Path

class Deployer:
    """デプロイ管理クラス"""
    
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_dir = self.root_dir / 'config'
        self.docker_dir = self.config_dir / 'docker'
    
    def run_command(self, command: List[str], cwd: Optional[str] = None) -> bool:
        """コマンドを実行"""
        try:
            subprocess.run(command, check=True, cwd=cwd)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ コマンド実行エラー: {e}")
            return False
    
    def deploy_normal(self) -> bool:
        """通常デプロイを実行"""
        print("🚀 通常デプロイを開始...")
        
        # Dockerイメージのビルド
        if not self.run_command(['docker', 'build', '-t', 'nyanco-bot', '.'], str(self.root_dir)):
            return False
        
        # docker-composeで起動
        if not self.run_command(['docker-compose', 'up', '-d'], str(self.docker_dir)):
            return False
        
        print("✅ 通常デプロイ完了")
        return True
    
    def deploy_gcp(self) -> bool:
        """GCPデプロイを実行"""
        print("☁️ GCPデプロイを開始...")
        
        # Cloud Buildの設定を読み込み
        cloudbuild_path = self.docker_dir / 'cloudbuild.gcp-compose.yaml'
        if not cloudbuild_path.exists():
            print(f"❌ Cloud Build設定ファイルが見つかりません: {cloudbuild_path}")
            return False
        
        # Cloud Buildを実行
        if not self.run_command(['gcloud', 'builds', 'submit', '--config', str(cloudbuild_path)]):
            return False
        
        print("✅ GCPデプロイ完了")
        return True
    
    def deploy_separate(self) -> bool:
        """個別デプロイを実行"""
        print("🔧 個別デプロイを開始...")
        
        # 各コンポーネントのデプロイ
        components = ['bot', 'podcast', 'manager']
        for component in components:
            print(f"📦 {component}のデプロイ中...")
            
            # コンポーネント用のDockerfile
            dockerfile = self.docker_dir / f'Dockerfile.{component}'
            if not dockerfile.exists():
                print(f"❌ Dockerfileが見つかりません: {dockerfile}")
                continue
            
            # イメージのビルド
            if not self.run_command(['docker', 'build', '-t', f'nyanco-bot-{component}', '-f', str(dockerfile), '.']):
                continue
            
            # コンテナの起動
            if not self.run_command(['docker-compose', '-f', f'docker-compose.{component}.yml', 'up', '-d']):
                continue
            
            print(f"✅ {component}のデプロイ完了")
        
        print("✅ 個別デプロイ完了")
        return True
    
    def check_environment(self) -> bool:
        """環境チェック"""
        print("🔍 環境チェック中...")
        
        # 必要なファイルの存在確認
        required_files = [
            self.docker_dir / 'Dockerfile',
            self.docker_dir / 'docker-compose.yml',
            self.docker_dir / 'cloudbuild.gcp-compose.yaml'
        ]
        
        for file in required_files:
            if not file.exists():
                print(f"❌ 必要なファイルが見つかりません: {file}")
                return False
        
        # Dockerの確認
        if not self.run_command(['docker', '--version']):
            print("❌ Dockerがインストールされていません")
            return False
        
        # docker-composeの確認
        if not self.run_command(['docker-compose', '--version']):
            print("❌ docker-composeがインストールされていません")
            return False
        
        print("✅ 環境チェック完了")
        return True

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='Discord にゃんこエージェント デプロイスクリプト')
    parser.add_argument('--mode', choices=['normal', 'gcp', 'separate'], default='normal',
                      help='デプロイモードを指定')
    parser.add_argument('--check', action='store_true',
                      help='環境チェックのみ実行')
    
    args = parser.parse_args()
    
    deployer = Deployer()
    
    # 環境チェック
    if not deployer.check_environment():
        sys.exit(1)
    
    if args.check:
        sys.exit(0)
    
    # デプロイ実行
    success = False
    if args.mode == 'normal':
        success = deployer.deploy_normal()
    elif args.mode == 'gcp':
        success = deployer.deploy_gcp()
    elif args.mode == 'separate':
        success = deployer.deploy_separate()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()