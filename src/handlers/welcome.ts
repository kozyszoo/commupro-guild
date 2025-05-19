import { Client, TextChannel, GuildMember } from 'discord.js';
import { db } from '../config/firebase';

// キャラクター設定
const characters = {
  tora: {
    name: 'トラにゃん',
    personality: '元気で明るい性格',
    greeting: 'やぁ！{username}さん、ようこそだにゃん！わたしはトラにゃんだよ！'
  },
  kuro: {
    name: 'クロにゃん',
    personality: '冷静で物知り',
    greeting: 'こんにちは、{username}さん。このサーバーへようこそ。私はクロにゃんです。'
  }
};

export const handleNewMember = async (member: GuildMember): Promise<void> => {
  try {
    // ユーザー情報をFirestoreに保存
    await db.collection('users').doc(member.id).set({
      id: member.id,
      username: member.user.username,
      joinedAt: new Date(),
      lastActive: new Date(),
      interests: [],
      engagementScore: 0
    });

    // 歓迎メッセージの送信
    const welcomeChannel = member.guild.channels.cache.find(
      channel => channel.name === 'welcome' || channel.name === '挨拶'
    ) as TextChannel;

    if (welcomeChannel) {
      const toraMessage = characters.tora.greeting.replace('{username}', member.user.username);
      const kuroMessage = characters.kuro.greeting.replace('{username}', member.user.username);
      
      await welcomeChannel.send(`${toraMessage}`);
      
      // 少し間を置いて2匹目のキャラクターが応答
      setTimeout(async () => {
        await welcomeChannel.send(`${kuroMessage}`);
        
        // 自己紹介を促すメッセージ
        setTimeout(async () => {
          await welcomeChannel.send(`${characters.tora.name}: ${member.user.username}さん、簡単な自己紹介をしてもらえると嬉しいにゃん！趣味や興味あることを教えてほしいにゃ～`);
        }, 3000);
      }, 2000);
    }
  } catch (error) {
    console.error('新規メンバー歓迎処理でエラーが発生しました:', error);
  }
}; 