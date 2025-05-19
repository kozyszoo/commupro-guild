import { Client, GatewayIntentBits, Partials } from 'discord.js';
import { handleNewMember } from '../../handlers/welcome';
import { updateUserActivity } from '../firebase/database';

export const initializeBot = (token: string): Client => {
  // Discordクライアントの初期化
  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.GuildMembers,
      GatewayIntentBits.MessageContent
    ],
    partials: [Partials.Message, Partials.Channel, Partials.GuildMember]
  });

  // ボットの起動
  client.once('ready', () => {
    console.log(`${client.user?.username}が起動しました！`);
  });

  // 新規メンバー参加時のイベント
  client.on('guildMemberAdd', async (member) => {
    await handleNewMember(member);
  });

  // メッセージ受信時の処理
  client.on('messageCreate', async (message) => {
    if (message.author.bot) return;

    // ユーザーの最終アクティブ時間を更新
    try {
      await updateUserActivity(message.author.id);
    } catch (error) {
      console.error('アクティビティ更新中にエラーが発生しました:', error);
    }

    // ここに他のメッセージ処理ロジックを実装
  });

  // 開発トークンの場合は実際にログインしない
  if (token !== 'development_token') {
    // ボットのログイン
    client.login(token).catch(error => {
      console.error('Discordボットのログインに失敗しました:', error);
    });
  } else {
    console.log('開発モードで実行中のため、Discordへの接続はスキップします。');
  }
  
  return client;
}; 