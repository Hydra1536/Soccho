import { gql } from '@apollo/client';

export const GET_FRIENDS = gql`
  query GetFriends {
    friendList {
      friendshipId
      requesterId
      addresseeId
      status
      createdAt
      userId
      username
      loyaltyScore
    }
  }
`;

export const GET_DASHBOARD_SUMMARY = gql`
  query DashboardSummary($userId: UUID!) {
    dashboardSummary(userId: $userId) {
      userId
      totalLent
      totalBorrowed
      totalConfirmed
    }
  }
`;

export const GET_FRIEND_LEDGER = gql`
  query FriendLedger($friendshipId: UUID!) {
    friendLedger(friendshipId: $friendshipId) {
      friendshipId
      netBalance
      pendingReceivable
      pendingPayable
      transactions {
        id
        lenderId
        borrowerId
        friendshipId
        amount
        status
        dueDate
      }
    }
  }
`;
