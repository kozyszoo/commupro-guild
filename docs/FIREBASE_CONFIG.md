# Discord にゃんこエージェント Firebase設定

## 目次
1. [Firebase設定](#firebase設定)
2. [Firestoreルール](#firestoreルール)
3. [Firestoreインデックス](#firestoreインデックス)

## Firebase設定

### firebase.json

```json
{
  "functions": {
    "source": "functions",
    "predeploy": [
      "npm --prefix \"$RESOURCE_DIR\" run build"
    ]
  },
  "firestore": {
    "rules": "firestore.rules",
    "indexes": "firestore.indexes.json"
  },
  "hosting": {
    "public": "public",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

## Firestoreルール

### firestore.rules

```javascript
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // 管理パネル用の読み取り許可（一時的）
    // 本番環境では適切な認証を実装してください
    match /{document=**} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

## Firestoreインデックス

### firestore.indexes.json

```json
{
  "indexes": [
    {
      "collectionGroup": "users",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "isActive",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "lastActivity",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "users",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "engagementScore",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "interactions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "interactions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "userId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "interactions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "type",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "topics",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "popularity",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "topics",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "trendScore",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "user_matches",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "status",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "matchScore",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "user_matches",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "user1Id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "status",
          "order": "ASCENDING"
        }
      ]
    },
    {
      "collectionGroup": "user_matches",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "user2Id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "status",
          "order": "ASCENDING"
        }
      ]
    },
    {
      "collectionGroup": "events",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "startTime",
          "order": "ASCENDING"
        }
      ]
    },
    {
      "collectionGroup": "bot_actions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "bot_actions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "userId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "actionType",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "bot_actions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "status",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "timestamp",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "analytics_sessions",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "date",
          "order": "DESCENDING"
        }
      ]
    },
    {
      "collectionGroup": "podcasts",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "guildId",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "publishedAt",
          "order": "DESCENDING"
        }
      ]
    }
  ]
}
```

## インデックス説明

### ユーザー関連インデックス
1. `users` コレクション
   - `guildId` + `isActive` + `lastActivity` (降順)
     - アクティブユーザーの最終活動日時による検索
   - `guildId` + `engagementScore` (降順)
     - エンゲージメントスコアによるユーザーランキング

### インタラクション関連インデックス
1. `interactions` コレクション
   - `guildId` + `timestamp` (降順)
     - サーバー内の最新インタラクション
   - `userId` + `timestamp` (降順)
     - ユーザーのインタラクション履歴
   - `guildId` + `type` + `timestamp` (降順)
     - 特定タイプのインタラクション検索

### トピック関連インデックス
1. `topics` コレクション
   - `guildId` + `popularity` (降順)
     - 人気トピックの検索
   - `guildId` + `trendScore` (降順)
     - トレンドトピックの検索

### マッチング関連インデックス
1. `user_matches` コレクション
   - `guildId` + `status` + `matchScore` (降順)
     - マッチングスコアによる検索
   - `user1Id` + `status`
     - ユーザー1のマッチング状態
   - `user2Id` + `status`
     - ユーザー2のマッチング状態

### イベント関連インデックス
1. `events` コレクション
   - `guildId` + `startTime`
     - イベントの開始時間順

### ボットアクション関連インデックス
1. `bot_actions` コレクション
   - `guildId` + `timestamp` (降順)
     - サーバー内の最新アクション
   - `userId` + `actionType` + `timestamp` (降順)
     - ユーザーへの特定アクション
   - `guildId` + `status` + `timestamp` (降順)
     - アクションの状態管理

### 分析関連インデックス
1. `analytics_sessions` コレクション
   - `guildId` + `date` (降順)
     - 日付順の分析セッション

### ポッドキャスト関連インデックス
1. `podcasts` コレクション
   - `guildId` + `publishedAt` (降順)
     - 公開日時順のポッドキャスト 