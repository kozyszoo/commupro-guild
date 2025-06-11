import discord
from discord.ext import commands
import openai
import asyncio
import json
from datetime import datetime
import random

# Botの設定
intents = discord.Intents.default()
# intents.message_content = True  # メッセージ内容の取得（特権インテント）
# intents.members = True  # メンバーリストの取得（特権インテント）
# intents.presences = True  # オンライン状態の取得（特権インテント）
intents.guilds = True  # サーバー情報の取得（通常インテント）

# または、すべてのインテントを有効にする場合:
# intents = discord.Intents.all()

bot = commands.Bot(command_prefix='!', intents=intents)

# OpenAI APIクライアントの設定
openai.api_key = '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'

# ロール別の属性定義
ROLE_ATTRIBUTES = {
    'Admin': {
        'personality': '責任感が強く、サーバーの運営に情熱を注ぐリーダー',
        'tone': '敬意を払いつつも親しみやすい',
        'interests': ['サーバー管理', 'コミュニティ運営', '技術的な話題'],
        'greeting_style': '感謝と敬意を込めた丁寧な挨拶'
    },
    'Moderator': {
        'personality': '公平で冷静、コミュニティの平和を守る存在',
        'tone': '信頼できる先輩のような親しみやすさ',
        'interests': ['コミュニティの健全性', 'ルール遵守', 'メンバーサポート'],
        'greeting_style': '頼れる存在としての温かい挨拶'
    },
    'VIP': {
        'personality': 'サーバーに長く貢献している特別なメンバー',
        'tone': '特別感を演出しつつフレンドリー',
        'interests': ['長期的なコミュニティ参加', '特別なイベント', '深い議論'],
        'greeting_style': '特別感のある歓迎メッセージ'
    },
    'Member': {
        'personality': 'サーバーの中心的な参加者で活動的',
        'tone': '親しみやすく気軽な',
        'interests': ['日常的な交流', '趣味の共有', 'カジュアルな会話'],
        'greeting_style': '気軽で親しみやすい挨拶'
    },
    'New': {
        'personality': 'サーバーに慣れていない新しいメンバー',
        'tone': '優しく導くような',
        'interests': ['サーバーのルール学習', '新しい出会い', '質問'],
        'greeting_style': '歓迎と案内を含む親切な挨拶'
    },
    'default': {
        'personality': '一般的なサーバーメンバー',
        'tone': 'フレンドリーで親しみやすい',
        'interests': ['一般的な交流', '雑談'],
        'greeting_style': '標準的な友好的挨拶'
    }
}

# 文脈情報を格納する辞書
context_data = {
    'server_events': [],
    'recent_topics': [],
    'time_of_day': '',
    'channel_activity': {}
}

def get_highest_priority_role(member):
    """メンバーの最も優先度の高いロールを取得"""
    try:
        role_priority = {
            'Admin': 100,
            'Moderator': 80,
            'VIP': 60,
            'Member': 40,
            'New': 20
        }
        
        highest_role = None
        highest_priority = -1
        
        for role in member.roles:
            if role.name in role_priority:
                if role_priority[role.name] > highest_priority:
                    highest_priority = role_priority[role.name]
                    highest_role = role.name
        
        return highest_role
    except Exception as e:
        print(f"ロール取得エラー: {e}")
        return 'default'  # エラー時はデフォルトロールを返す

def get_time_context():
    """現在の時間に基づく文脈を取得"""
    now = datetime.now()
    hour = now.hour
    
    if 5 <= hour < 12:
        return "朝"
    elif 12 <= hour < 17:
        return "午後"
    elif 17 <= hour < 21:
        return "夕方"
    else:
        return "夜"

async def get_channel_activity(channel):
    """チャンネルの最近の活動を分析"""
    try:
        messages = []
        async for message in channel.history(limit=10):
            if not message.author.bot:
                messages.append(message.content[:100])  # 最初の100文字のみ
        return messages
    except:
        return []

async def generate_dynamic_greeting(member, channel=None, context_info=None):
    """ChatGPT APIを使用して動的な挨拶メッセージを生成"""
    
    role_name = get_highest_priority_role(member)
    if not role_name:
        role_name = 'default'
    
    attributes = ROLE_ATTRIBUTES[role_name]
    time_context = get_time_context()
    
    # 文脈情報を収集
    channel_activity = []
    if channel:
        channel_activity = await get_channel_activity(channel)
    
    # プロンプトを構築
    prompt = f"""
あなたはDiscordサーバーのフレンドリーなボットです。以下の情報に基づいて、{member.display_name}さんに対する自然で親しみやすい挨拶メッセージを生成してください。

**メンバー情報:**
- 名前: {member.display_name}
- ロール: {role_name}
- 属性: {attributes['personality']}
- 話し方のトーン: {attributes['tone']}
- 興味関心: {', '.join(attributes['interests'])}

**現在の状況:**
- 時間帯: {time_context}
- チャンネル: {channel.name if channel else '不明'}

**最近のチャンネル活動:**
{chr(10).join(channel_activity[-3:]) if channel_activity else '静かなチャンネルです'}

**要求事項:**
1. 50文字程度の自然な日本語で
2. 毎回異なる表現を使用
3. ロールの特性を反映
4. 時間帯や状況を考慮
5. 親しみやすく自然な口調で
6. 絵文字を1-2個使用

例外的に、メッセージは必ず{member.mention}で始めてください。
"""

    try:
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは創造的で親しみやすいDiscordボットです。毎回異なる自然な挨拶を生成します。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=1.0,  # 最大の創造性
                top_p=0.9,
                frequency_penalty=0.5,  # 繰り返しを避ける
                presence_penalty=0.3
            )
        )
        
        message = response.choices[0].message.content.strip()
        
        # メンションが含まれていない場合は追加
        if not message.startswith(member.mention):
            message = f"{member.mention} {message}"
            
        return message
        
    except Exception as e:
        # API呼び出しが失敗した場合のフォールバック
        fallback_messages = [
            f"{member.mention} こんにちは！今日も一日よろしくお願いします✨",
            f"{member.mention} お疲れ様です！何か楽しいことはありましたか？😊",
            f"{member.mention} いらっしゃいませ！今日はどんな一日でしたか？🌟"
        ]
        return random.choice(fallback_messages)

@bot.event
async def on_ready():
    print(f'{bot.user} としてログインしました！')
    print('ChatGPT API連携機能が有効です。')

@bot.command(name='greet')
async def greet_member(ctx, member: discord.Member = None):
    """指定されたメンバーまたは自分に動的な挨拶をする"""
    if member is None:
        member = ctx.author
    
    # "生成中..." メッセージを表示
    thinking_msg = await ctx.send("💭 メッセージを生成中...")
    
    try:
        # 動的メッセージを生成
        message = await generate_dynamic_greeting(member, ctx.channel)
        
        # 生成されたメッセージで更新
        await thinking_msg.edit(content=message)
        
    except Exception as e:
        await thinking_msg.edit(content=f"エラーが発生しました: {e}")

@bot.command(name='massgreet')
@commands.has_permissions(administrator=True)
async def mass_greet(ctx, role_name: str = None):
    """指定されたロールの全メンバーに動的な挨拶を送信"""
    try:
        if role_name:
            role = discord.utils.get(ctx.guild.roles, name=role_name)
            if not role:
                await ctx.send(f"ロール '{role_name}' が見つかりません。")
                return
            members = role.members
        else:
            # インテントの制限がある場合は代替方法
            try:
                members = [m for m in ctx.guild.members if not m.bot]
            except Exception:
                await ctx.send("⚠️ メンバーリスト取得に失敗しました。Discord Developer Portalで「SERVER MEMBERS INTENT」を有効にしてください。")
                await ctx.send("現在のチャンネルにいるメンバーのみ挨拶します。")
                # 現在のチャンネルにいるメンバーのみを対象にする
                members = [ctx.author]
                
        await ctx.send(f"🤖 {len(members)}人のメンバーに動的な挨拶を生成中...")
        
        for i, member in enumerate(members):
            try:
                message = await generate_dynamic_greeting(member, ctx.channel)
                await ctx.send(message)
                
                # API制限を避けるため少し待機
                if i % 5 == 4:  # 5人ごとに少し長めの待機
                    await asyncio.sleep(2)
                else:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                await ctx.send(f"{member.mention} へのメッセージ生成に失敗: {e}")
    except Exception as e:
        await ctx.send(f"⚠️ エラーが発生しました: {e}")
        await ctx.send("Discord Developer Portalで必要な特権インテントを有効にしてください。")

@bot.command(name='setcontext')
async def set_context(ctx, *, context_info: str):
    """サーバーの文脈情報を設定"""
    context_data['server_events'].append({
        'info': context_info,
        'timestamp': datetime.now(),
        'set_by': ctx.author.display_name
    })
    
    # 古い情報を削除（最新5件のみ保持）
    if len(context_data['server_events']) > 5:
        context_data['server_events'] = context_data['server_events'][-5:]
    
    await ctx.send(f"✅ 文脈情報を設定しました: {context_info}")

@bot.command(name='viewcontext')
async def view_context(ctx):
    """現在の文脈情報を表示"""
    embed = discord.Embed(title="🌟 現在の文脈情報", color=0x00ff00)
    
    if context_data['server_events']:
        events = "\n".join([
            f"• {event['info']} (設定者: {event['set_by']})"
            for event in context_data['server_events'][-3:]
        ])
        embed.add_field(name="最近のイベント", value=events, inline=False)
    
    embed.add_field(name="現在の時間帯", value=get_time_context(), inline=True)
    embed.add_field(name="チャンネル", value=ctx.channel.name, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='roleattributes')
async def show_role_attributes(ctx, role_name: str = None):
    """ロールの属性情報を表示"""
    if role_name and role_name in ROLE_ATTRIBUTES:
        attrs = ROLE_ATTRIBUTES[role_name]
        embed = discord.Embed(title=f"🎭 {role_name}ロールの属性", color=0x0099ff)
        embed.add_field(name="性格", value=attrs['personality'], inline=False)
        embed.add_field(name="話し方", value=attrs['tone'], inline=False)
        embed.add_field(name="興味関心", value=", ".join(attrs['interests']), inline=False)
        embed.add_field(name="挨拶スタイル", value=attrs['greeting_style'], inline=False)
    else:
        embed = discord.Embed(title="🎭 利用可能なロール", color=0x0099ff)
        roles = ", ".join(ROLE_ATTRIBUTES.keys())
        embed.add_field(name="ロール一覧", value=roles, inline=False)
    
    await ctx.send(embed=embed)

# エラーハンドリング
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ 指定されたメンバーが見つかりません。")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ このコマンドを実行する権限がありません。")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ そのコマンドは存在しません。`!help`で利用可能なコマンドを確認してください。")
    elif "missing access" in str(error).lower() or "privileged intent" in str(error).lower():
        await ctx.send("⚠️ 特権インテントが必要です。Discord Developer Portalで以下を有効にしてください：")
        await ctx.send("- MESSAGE CONTENT INTENT")
        await ctx.send("- SERVER MEMBERS INTENT")
        await ctx.send("詳細は https://discord.com/developers/applications/ で設定できます。")
    else:
        await ctx.send(f"⚠️ エラーが発生しました: {error}")

# 使用方法とセットアップガイド
if __name__ == '__main__':
    print("=== Discord ChatGPT連携Bot セットアップガイド ===")
    print()
    print("1. 必要なライブラリをインストール:")
    print("   pip install discord.py openai")
    print()
    print("2. APIキーの設定:")
    print("   - OpenAI API Key を取得")
    print("   - Discord Bot Token を取得")
    print()
    print("3. Discord Developer Portalでの設定:")
    print("   - https://discord.com/developers/applications/ にアクセス")
    print("   - ボットアプリケーションの「Bot」タブを開く")
    print("   - 「Privileged Gateway Intents」セクションで以下を有効にする:")
    print("     * SERVER MEMBERS INTENT")
    print("     * MESSAGE CONTENT INTENT")
    print("     * PRESENCE INTENT（必要な場合）")
    print()
    print("4. 設定箇所:")
    print("   - openai.api_key = 'YOUR_OPENAI_API_KEY_HERE'")
    print("   - TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE'")
    print()
    print("5. 利用可能なコマンド:")
    print("   !greet [@メンバー] - 動的な挨拶生成")
    print("   !massgreet [ロール名] - 一括挨拶")
    print("   !setcontext <情報> - 文脈情報設定")
    print("   !viewcontext - 文脈情報表示")
    print("   !roleattributes [ロール名] - ロール属性表示")
    print()
    print("⚠️ 注意:")
    print("- OpenAI APIの使用料金が発生します")
    print("- 完全な機能を使用するには特権インテントの有効化が必要です")
    print("- 現在の設定：MESSAGE CONTENTとMEMBERSインテントは無効化されています")
    print("- この状態では基本的な機能のみ使用可能です")
    
    # 実行時はこの行のコメントを解除
    TOKEN = 'MTM3NDAyMTIwNjI2ODk2ODk2MA.GbVlUq.elC555wWgszKMoD_PoiGJUUicxWKu0oGKdTA6s'
    bot.run(TOKEN)