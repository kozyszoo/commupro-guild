import { db } from '../../config/firebase';
import { User } from '../../models/user';

export const saveUser = async (user: User): Promise<void> => {
  try {
    await db.collection('users').doc(user.id).set(user);
  } catch (error) {
    console.error('ユーザー保存中にエラーが発生しました:', error);
    throw error;
  }
};

export const getUser = async (userId: string): Promise<User | null> => {
  try {
    const userDoc = await db.collection('users').doc(userId).get();
    if (!userDoc.exists) {
      return null;
    }
    return userDoc.data() as User;
  } catch (error) {
    console.error('ユーザー取得中にエラーが発生しました:', error);
    throw error;
  }
};

export const updateUserActivity = async (userId: string): Promise<void> => {
  try {
    await db.collection('users').doc(userId).update({
      lastActive: new Date()
    });
  } catch (error) {
    console.error('ユーザー活動更新中にエラーが発生しました:', error);
    throw error;
  }
}; 