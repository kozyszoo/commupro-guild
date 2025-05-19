import dotenv from 'dotenv';
import { initializeBot } from './services/discord/bot';

// 環境変数の読み込み
dotenv.config();

// 開発環境用のデフォルトトークン
const DISCORD_TOKEN = process.env.DISCORD_TOKEN || 'development_token';

// ボットを初期化するが、開発環境では実際にログインはしない
const client = initializeBot(DISCORD_TOKEN);

console.log('Discordにゃんこエージェントの初期化が完了しました。');
console.log('実際に使用するには、.envファイルにDISCORD_TOKENとFIREBASE_SERVICE_ACCOUNTを設定してください。'); 