const admin = require('firebase-admin');

// Initialize Firebase Admin with emulator settings
if (!admin.apps.length) {
  // Check if we're using the emulator
  if (process.env.FIRESTORE_EMULATOR_HOST) {
    admin.initializeApp({
      projectId: 'demo-project'
    });
  } else {
    admin.initializeApp();
  }
}

const db = admin.firestore();

// Sample analytics data based on the structure found in the codebase
const analyticsData = {
  "analytics_20241220": {
    id: "analytics_20241220",
    guildId: "987654321098765432",
    date: "2024-12-20",
    timestamp: admin.firestore.FieldValue.serverTimestamp(),
    activeUsers: 45,
    messageCount: 178,
    newMembers: 2,
    reengagements: 3,
    topTopics: [
      { topic: "React", count: 42 },
      { topic: "TypeScript", count: 31 },
      { topic: "フロントエンド", count: 28 },
      { topic: "JavaScript", count: 25 },
      { topic: "CSS", count: 19 }
    ],
    channelActivity: {
      "general": 58,
      "frontend-dev": 45,
      "tech-talk": 42,
      "typescript-advanced": 23,
      "css-tips": 10
    },
    hourlyActivity: {
      "9": 12,
      "10": 18,
      "11": 22,
      "12": 15,
      "13": 8,
      "14": 20,
      "15": 25,
      "16": 28,
      "17": 15,
      "18": 10,
      "19": 5
    },
    topUsers: [
      { userId: "user123", messageCount: 25 },
      { userId: "user456", messageCount: 18 },
      { userId: "user789", messageCount: 15 }
    ],
    reactions: {
      total: 89,
      types: {
        "👍": 32,
        "❤️": 18,
        "🎉": 15,
        "🚀": 12,
        "👀": 7,
        "🤔": 5
      }
    }
  },
  "analytics_20241221": {
    id: "analytics_20241221",
    guildId: "987654321098765432",
    date: "2024-12-21",
    timestamp: admin.firestore.FieldValue.serverTimestamp(),
    activeUsers: 38,
    messageCount: 142,
    newMembers: 0,
    reengagements: 1,
    topTopics: [
      { topic: "DevOps", count: 32 },
      { topic: "Kubernetes", count: 25 },
      { topic: "Node.js", count: 21 },
      { topic: "バックエンド", count: 18 },
      { topic: "GraphQL", count: 14 }
    ],
    channelActivity: {
      "general": 48,
      "devops": 38,
      "backend-dev": 32,
      "tech-talk": 24,
      "random": 0
    },
    hourlyActivity: {
      "10": 15,
      "11": 20,
      "12": 12,
      "13": 8,
      "14": 18,
      "15": 22,
      "16": 25,
      "17": 12,
      "18": 8,
      "19": 2
    },
    topUsers: [
      { userId: "user321", messageCount: 20 },
      { userId: "user654", messageCount: 16 },
      { userId: "user987", messageCount: 12 }
    ],
    reactions: {
      total: 65,
      types: {
        "👍": 28,
        "🔥": 12,
        "💯": 10,
        "🎯": 8,
        "✅": 7
      }
    }
  },
  "analytics_20241222": {
    id: "analytics_20241222",
    guildId: "987654321098765432",
    date: "2024-12-22",
    timestamp: admin.firestore.FieldValue.serverTimestamp(),
    activeUsers: 34,
    messageCount: 127,
    newMembers: 2,
    reengagements: 1,
    topTopics: [
      { topic: "React", count: 28 },
      { topic: "デザイン", count: 15 },
      { topic: "JavaScript", count: 23 },
      { topic: "AI", count: 12 },
      { topic: "ゲーム開発", count: 8 }
    ],
    channelActivity: {
      "general": 45,
      "tech-talk": 38,
      "design": 22,
      "random": 15,
      "game-dev": 7
    },
    hourlyActivity: {
      "10": 10,
      "11": 15,
      "12": 18,
      "13": 5,
      "14": 12,
      "15": 20,
      "16": 22,
      "17": 15,
      "18": 8,
      "19": 2
    },
    topUsers: [
      { userId: "user111", messageCount: 18 },
      { userId: "user222", messageCount: 14 },
      { userId: "user333", messageCount: 10 }
    ],
    reactions: {
      total: 72,
      types: {
        "👍": 25,
        "❤️": 15,
        "🎉": 12,
        "😄": 10,
        "🙌": 10
      }
    }
  }
};

async function seedAnalytics() {
  console.log('Starting to seed analytics data...');
  
  const batch = db.batch();
  
  for (const [docId, data] of Object.entries(analyticsData)) {
    const docRef = db.collection('analytics_sessions').doc(docId);
    batch.set(docRef, data);
    console.log(`Prepared analytics data for ${data.date}`);
  }
  
  try {
    await batch.commit();
    console.log('Successfully seeded analytics data!');
  } catch (error) {
    console.error('Error seeding analytics data:', error);
    process.exit(1);
  }
  
  process.exit(0);
}

seedAnalytics();