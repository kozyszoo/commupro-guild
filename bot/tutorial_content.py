#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Discord にゃんこエージェント - チュートリアルコンテンツ定義
運用者向けの実用的なDiscordサーバー活用ガイド
"""

from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class TutorialContent:
    """チュートリアルコンテンツの詳細定義"""
    step_number: int
    title: str
    description: str
    detailed_guide: str
    action_items: List[str]
    tips: List[str]
    emoji: str
    estimated_time: str
    difficulty_level: str

class AdvancedTutorialManager:
    """高度なチュートリアル管理システム"""
    
    def __init__(self):
        self.tutorial_contents = self._initialize_tutorial_contents()
        
    def _initialize_tutorial_contents(self) -> List[TutorialContent]:
        """詳細なチュートリアルコンテンツを初期化"""
        return [
            TutorialContent(
                step_number=1,
                title="🎉 ウェルカム・オリエンテーション",
                description="Discordサーバーの全体像を把握し、コミュニティの雰囲気を理解しましょう",
                detailed_guide="""
**Discordサーバーへようこそ！**

このサーバーは、技術者やクリエイターが集まって知識共有と相互支援を行うコミュニティですにゃ〜

**サーバーの構成:**
• 📢 アナウンス系チャンネル - 重要なお知らせ
• 💬 雑談系チャンネル - 日常的なコミュニケーション  
• 🛠 技術系チャンネル - プログラミングや技術的な話題
• 🎨 クリエイティブ系チャンネル - 作品共有や創作活動
• 🎯 プロジェクト系チャンネル - 共同作業や企画

**このサーバーの特徴:**
✨ 初心者歓迎の雰囲気
✨ 建設的なフィードバック文化
✨ 多様な専門知識を持つメンバー
✨ 定期的なイベントや勉強会
                """,
                action_items=[
                    "サーバーの説明を読んで、どんなコミュニティか理解する",
                    "各チャンネルの説明を確認する",
                    "自己紹介チャンネルで簡単な挨拶をする"
                ],
                tips=[
                    "自己紹介では、あなたの興味や得意分野を書くと交流しやすくなりますにゃ〜",
                    "まずは ROM（見るだけ）から始めても大丈夫ですにゃ！",
                    "不明な略語や用語があったら遠慮なく質問してくださいにゃ"
                ],
                emoji="👋",
                estimated_time="5-10分",
                difficulty_level="初心者"
            ),
            
            TutorialContent(
                step_number=2,
                title="📋 コミュニティガイドライン",
                description="サーバーのルールを理解し、みんなが快適に過ごせる環境づくりに参加しましょう",
                detailed_guide="""
**コミュニティの基本ルール**

**🤝 尊重と配慮**
• 他のメンバーを尊重し、建設的なコミュニケーションを心がける
• 異なる意見や経験レベルを受け入れる
• 誹謗中傷、ハラスメントは厳禁

**💬 コミュニケーションのマナー**
• 適切なチャンネルで発言する
• スパムや連投を避ける
• 個人情報や機密情報の共有に注意

**🔧 技術的なやり取り**
• 質問する時は具体的に（環境、エラーメッセージなど）
• コードは適切にフォーマットして共有
• 解決した問題は他の人のために経緯を残す

**🎯 建設的な参加**
• 「ググレカス」ではなく、学習をサポートする姿勢
• 初心者の質問も歓迎し、丁寧に回答
• 知識の共有と相互学習を大切にする
                """,
                action_items=[
                    "#rules チャンネルを熟読する",
                    "ルールに同意の「✅」リアクションを押す",
                    "不明な点があれば質問する"
                ],
                tips=[
                    "ルールは「禁止事項」ではなく「良いコミュニティのガイドライン」として捉えてくださいにゃ",
                    "困った時は遠慮なくモデレーターに相談してくださいにゃ〜",
                    "他の人の良いやり取りを観察して、文化を学ぶのも大切ですにゃ！"
                ],
                emoji="📜",
                estimated_time="10-15分",
                difficulty_level="初心者"
            ),
            
            TutorialContent(
                step_number=3,
                title="🎭 ロール選択とカスタマイズ",
                description="あなたの興味や専門分野に応じてロールを選択し、関連するチャンネルにアクセスしましょう",
                detailed_guide="""
**ロールシステムの活用方法**

**🏷️ 専門分野別ロール**
• 🖥️ フロントエンド開発者
• ⚙️ バックエンド開発者  
• 📱 モバイルアプリ開発者
• 🤖 AI/機械学習エンジニア
• 🎨 UI/UXデザイナー
• 📊 データサイエンティスト
• 🔒 セキュリティエンジニア

**📚 学習段階別ロール**
• 🌱 プログラミング初心者
• 🌿 中級者
• 🌳 上級者/メンター

**🎯 関心分野別ロール**
• 💼 起業/ビジネス
• 🎮 ゲーム開発
• 🌐 Web開発
• 📚 技術書籍
• 🎤 登壇/発表

**ロールの利点:**
✨ 専門チャンネルへのアクセス
✨ 関連する通知の受信
✨ 同じ興味を持つ人との出会い
✨ プロジェクトマッチング機能
                """,
                action_items=[
                    "#role-selection チャンネルに移動する",
                    "自分に合ったロールを3-5個選択する",
                    "新しくアクセスできるチャンネルを確認する"
                ],
                tips=[
                    "複数のロールを選択しても大丈夫ですにゃ〜",
                    "後からロールは変更・追加できますにゃ！",
                    "興味がある分野のロールも選んでおくと学習機会が増えますにゃ"
                ],
                emoji="🏷️",
                estimated_time="5-10分",
                difficulty_level="初心者"
            ),
            
            TutorialContent(
                step_number=4,
                title="💬 効果的なコミュニケーション",
                description="Discordの機能を活用して、効果的にコミュニケーションを取る方法を学びましょう",
                detailed_guide="""
**Discord機能の効果的な使い方**

**💬 基本的なメッセージング**
• `@username` でメンションして注意を引く
• `**太字**` や `*斜体*` で強調
• ``` でコードブロックを作成
• `インラインコード` で短いコードを表示

**🎯 チャンネルの使い分け**
• #general - 雑談、軽い質問
• #tech-discussion - 技術的な議論
• #help-wanted - 具体的な技術サポートが必要な時
• #showcase - 作品や成果物の共有
• #job-board - 求人情報や案件共有

**📎 ファイル共有のベストプラクティス**
• スクリーンショットで視覚的に説明
• コードはGitHubのGistやPastebinを活用
• 大きなファイルはGoogle DriveやDropboxで共有

**🧵 スレッド機能の活用**
• 長い議論はスレッドで行い、メインチャンネルを整理
• 質問への回答もスレッドで詳しく説明

**👍 リアクションの効果的な使用**
• ✅ 解決済み・理解した
• ❤️ 感謝・応援
• 🤔 質問・疑問
• 👀 確認中・見ています
                """,
                action_items=[
                    "#general チャンネルで簡単な質問や雑談をしてみる",
                    "他の人のメッセージにリアクションをつけてみる",
                    "コードブロック機能を試してみる"
                ],
                tips=[
                    "最初は短いメッセージから始めて、徐々に慣れていけば大丈夫ですにゃ〜",
                    "他の人のやり取りを見て、良いコミュニケーションパターンを学ぶのも効果的ですにゃ",
                    "分からないことは遠慮なく質問してくださいにゃ！みんな親切ですにゃ〜"
                ],
                emoji="🗣️",
                estimated_time="15-20分",
                difficulty_level="初心者"
            ),
            
            TutorialContent(
                step_number=5,
                title="🔔 通知と設定の最適化",
                description="Discordの通知設定を調整して、重要な情報を見逃さずに快適に利用しましょう",
                detailed_guide="""
**通知設定の最適化戦略**

**🔔 サーバー全体の通知設定**
1. サーバー名を右クリック
2. 「通知設定」を選択
3. おすすめ設定：
   • 全てのメッセージ: OFF（雑談が多いため）
   • @everyone/@here のみ: ON
   • @ロール: ON（重要なお知らせ用）

**📢 チャンネル別の個別設定**
• #announcements - 全てのメッセージ通知 ON
• #important-updates - 全てのメッセージ通知 ON  
• #general - メンション時のみ
• #tech-discussion - メンション時のみ
• #random - 通知 OFF

**🎯 キーワード通知の設定**
1. ユーザー設定 → 通知
2. 「ユーザー設定」→「通知」
3. あなたの技術スタック（例：Python, React, Docker）を設定

**📱 モバイル通知の調整**
• 重要なチャンネルのみプッシュ通知
• 勤務時間外の通知制限
• サウンドとバイブレーションの設定

**⏰ おやすみモード機能**
• 集中したい時間帯の通知をブロック
• 緊急時のみの通知設定
                """,
                action_items=[
                    "サーバーの通知設定を調整する",
                    "重要なチャンネルの個別通知設定を行う",
                    "キーワード通知を設定する"
                ],
                tips=[
                    "最初は控えめに設定して、必要に応じて増やすのがコツですにゃ〜",
                    "通知が多すぎて疲れた場合は、いつでも調整してくださいにゃ",
                    "モバイルとデスクトップで別々に設定できますにゃ！"
                ],
                emoji="🔔",
                estimated_time="10-15分",
                difficulty_level="中級者"
            ),
            
            TutorialContent(
                step_number=6,
                title="🚀 高度な機能とサポート",
                description="ボット機能、イベント参加、困った時のサポート体制について学びましょう",
                detailed_guide="""
**サーバーの高度な機能活用**

**🤖 ボット機能の活用**
• @みやにゃん - 技術サポートとチュートリアル
• @イヴにゃん - データ分析とレポート
• その他の便利ボット機能

**📅 イベントとコミュニティ活動**
• 毎週の技術勉強会
• 月例LT（ライトニングトーク）
• ハッカソンやコンテスト
• 読書会や輪読会
• ペアプログラミングセッション

**🎯 プロジェクトマッチング**
• #project-matching でチームメンバー募集
• スキルとプロジェクトの適切なマッチング
• メンタリング関係の構築

**💼 キャリアサポート**
• #job-board での求人情報共有
• 履歴書・ポートフォリオレビュー
• 面接対策やキャリア相談

**🆘 困った時のサポート体制**
• @みやにゃん ヘルプ - 基本的なサポート
• @Moderator - ルールや人間関係の問題
• #help-wanted - 技術的な質問
• DM - プライベートな相談

**🔧 カスタマイズとパーソナライゼーション**
• プロフィールの最適化
• ステータスメッセージの活用
• 個人用チャンネルの作成申請
                """,
                action_items=[
                    "ボット機能を実際に試してみる",
                    "今後のイベントスケジュールを確認する",
                    "サポートが必要な時の連絡方法を覚える"
                ],
                tips=[
                    "いきなり全機能を使おうとしなくても大丈夫ですにゃ〜",
                    "イベントは見学からでも参加OKですにゃ！",
                    "困ったことがあったら、1人で悩まずにサポートを求めてくださいにゃ",
                    "このコミュニティは「一緒に成長する」ことを大切にしていますにゃ〜"
                ],
                emoji="🚀",
                estimated_time="20-30分",
                difficulty_level="中級者"
            )
        ]
    
    def get_tutorial_step(self, step_number: int) -> Optional[TutorialContent]:
        """指定されたステップのチュートリアルコンテンツを取得"""
        for content in self.tutorial_contents:
            if content.step_number == step_number:
                return content
        return None
    
    def get_all_steps(self) -> List[TutorialContent]:
        """全てのチュートリアルステップを取得"""
        return self.tutorial_contents
    
    def get_total_steps(self) -> int:
        """総ステップ数を取得"""
        return len(self.tutorial_contents)
    
    def format_step_for_discord(self, step_number: int) -> Dict[str, str]:
        """DiscordのEmbed形式用にフォーマットされたステップを取得"""
        content = self.get_tutorial_step(step_number)
        if not content:
            return {}
        
        return {
            'title': f"{content.emoji} {content.title} (ステップ {step_number}/{self.get_total_steps()})",
            'description': content.description,
            'detailed_guide': content.detailed_guide,
            'action_items': '\n'.join([f"• {item}" for item in content.action_items]),
            'tips': '\n'.join([f"💡 {tip}" for tip in content.tips]),
            'footer': f"所要時間: {content.estimated_time} | 難易度: {content.difficulty_level}"
        } 