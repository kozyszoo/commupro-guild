export interface User {
  id: string;
  username: string;
  joinedAt: Date;
  lastActive: Date;
  interests: string[];
  engagementScore: number;
} 