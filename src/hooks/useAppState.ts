// Hook: owns the central AppState via useReducer and exposes dispatch

import { useReducer } from 'react';
import type { AppState, Card } from '../types';

type Action =
  | { type: 'ADD_CARD'; card: Card }
  | { type: 'DISMISS_CARD'; id: string }
  | { type: 'CLEAR_ALL' };

const initial: AppState = {
  gesture: 'idle',
  cards: [],
};

const reducer = (state: AppState, action: Action): AppState => {
  switch (action.type) {
    case 'ADD_CARD':
      return { ...state, cards: [...state.cards, action.card] };
    case 'DISMISS_CARD':
      return { ...state, cards: state.cards.filter((c) => c.id !== action.id) };
    case 'CLEAR_ALL':
      return { ...state, cards: [] };
  }
};

export const useAppState = () => {
  const [state, dispatch] = useReducer(reducer, initial);
  return { state, dispatch };
};
