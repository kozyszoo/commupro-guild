import dotenv from 'dotenv';
import { initializeBot } from './services/discord/bot';

// 環境変数の読み込み
dotenv.config();

const DISCORD_TOKEN = process.env.DISCORD_TOKEN;

if (!DISCORD_TOKEN) {
  console.error('DISCORD_TOKENが設定されていません。.envファイルを確認してください。');
  process.exit(1);
}

// Discordボットの初期化と起動
initializeBot(DISCORD_TOKEN); 